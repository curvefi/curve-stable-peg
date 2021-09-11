# (c) Curve.Fi, 2021
# Peg Keeper
# @version 0.2.15


interface CurvePool:
    def peg_keeper_add(_amount: uint256) -> uint256: nonpayable
    def balances(i_coin: uint256) -> uint256: view
    def calc_token_amount(amounts: uint256[2], deposit: bool) -> uint256: view
    def calc_withdraw_one_coin(_token_amount: uint256, i: int128) -> uint256: nonpayable
    def coins(i: uint256) -> address: view
    def lp_token() -> address: view
    def peg_keeper_remove(_amount: uint256) -> uint256: nonpayable
    def peg_keeper_remove_via_token(_token_amount: uint256) -> uint256: nonpayable
    def token() -> address: view

interface PoolToken:
    def balanceOf(arg0: address) -> uint256: view
    # Will be needed to give profit
    def transfer(_to: address, _amount: uint256): nonpayable

interface ERC20Pegged:
    def approve(_spender: address, _amount: uint256): nonpayable
    def mint(_to: address, _amount: uint256): nonpayable
    def burn(_amount: uint256): nonpayable
    def balanceOf(arg0: address) -> uint256: view


event Provide:
    amount: uint256


event Withdraw:
    amount: uint256


MIN_POOL_TOKEN_AMOUNT: constant(uint256) = 10 ** 3
MIN_AMOUNT: constant(uint256) = 10 ** 6


# Assume decimals of peg and pegged are equal
pegged: public(address)
pool: public(address)
pool_token: address

action_delay: public(uint256)
last_change: public(uint256)

admin: public(address)
receiver: public(address)  # receiver of profit

future_admin: public(address)
future_receiver: public(address)


@external
def __init__(_pool: address, _action_delay: uint256, _receiver: address):
    """
    @notice Contract constructor
    @param _pool Contract pool address
    @param _action_delay Time between minting/burning coins
    @param _receiver Address of profit receiver
    """
    self.pool = _pool
    self.pool_token = CurvePool(_pool).lp_token()
    self.pegged = CurvePool(_pool).coins(1)
    
    self.action_delay = _action_delay

    self.admin = msg.sender
    self.receiver = _receiver


@internal
def _provide(_amount: uint256) -> bool:
    if _amount < MIN_AMOUNT:
        return False

    pegged: address = self.pegged
    pool: address = self.pool

    # Mint '_amount' of coin
    ERC20Pegged(pegged).mint(self, _amount)
    ERC20Pegged(pegged).approve(pool, _amount)

    # Add '_amount' of coin to the pool
    # Can not be rugged with min_amount=0
    CurvePool(pool).peg_keeper_add(_amount)

    self.last_change = block.timestamp
    log Provide(_amount)
    return True


@internal
def _withdraw(_amount: uint256) -> bool:
    if _amount < MIN_AMOUNT:
        return False
    pool: address = self.pool

    # Remove coins from the pool
    amounts: uint256[2] = [0, _amount]
    token_amount: uint256 = CurvePool(pool).calc_token_amount(amounts, False) * 1004 / 1000
    token_balance: uint256 = PoolToken(self.pool_token).balanceOf(self)
    if token_amount <= token_balance:
        CurvePool(pool).peg_keeper_remove(_amount)
        log Withdraw(_amount)
    elif token_balance < MIN_POOL_TOKEN_AMOUNT:
        return False
    else:  # Remove?
        amount: uint256 = CurvePool(pool).calc_withdraw_one_coin(token_balance, 1)
        if amount < MIN_AMOUNT:
            return False

        amount = CurvePool(pool).peg_keeper_remove_via_token(token_balance)
        log Withdraw(amount)

    # Burn coins
    coin_balance: uint256 = ERC20Pegged(self.pegged).balanceOf(self)
    ERC20Pegged(self.pegged).burn(coin_balance)

    self.last_change = block.timestamp
    return True


@external
def update() -> bool:
    """
    @notice Mint or burn coins from the pool to stabilize it
    @return True if peg was maintained, otherwise False
    """
    assert msg.sender == self.pool, "Callable by the pool"
    if self.last_change + self.action_delay > block.timestamp:
        return False

    pool: address = self.pool
    balance_peg: uint256 = CurvePool(pool).balances(0)
    balance_pegged: uint256 = CurvePool(pool).balances(1)

    if balance_peg > balance_pegged:
        return self._provide((balance_peg - balance_pegged) / 5)
    else:
        # balance_peg == balance_pegged will return False due to 0 < MIN_AMOUNT
        return self._withdraw((balance_pegged - balance_peg) / 5)


# @external
# def profit():
#     # Count minted vs withdrawable?


@external
def commit_new_admin(_new_admin: address):
    """
    @notice Commit new admin of the Peg Keeper
    @param _new_admin Address of the new admin
    """
    assert msg.sender == self.admin, "Access denied."
    self.future_admin = _new_admin


@external
def apply_new_admin():
    """
    @notice Apply new admin of the Peg Keeper
    @dev Should be executed from new admin
    """
    assert msg.sender == self.future_admin, "Access denied."
    self.admin = self.future_admin


@external
def commit_new_receiver(_new_receiver: address):
    """
    @notice Commit new receiver of profit
    @param _new_receiver Address of the new receiver
    """
    assert msg.sender == self.admin, "Access denied."
    self.future_receiver = _new_receiver


@external
def apply_new_receiver():
    """
    @notice Apply new receiver of profit
    """
    assert msg.sender == self.admin, "Access denied."
    self.receiver = self.future_receiver
