# (c) Curve.Fi, 2021
# Peg Keeper for pool with equal decimals of coins
# @version 0.2.15


interface CurvePool:
    def balances(i_coin: uint256) -> uint256: view
    def coins(i: uint256) -> address: view
    def lp_token() -> address: view
    def peg_keeper_add(_amount: uint256) -> uint256: nonpayable
    def peg_keeper_remove(_amount: uint256) -> uint256: nonpayable
    def peg_keeper_remove_via_token(_token_amount: uint256) -> uint256: nonpayable
    def calc_token_amount(amounts: uint256[2], deposit: bool) -> uint256: view
    def calc_withdraw_one_coin(_token_amount: uint256, i: int128) -> uint256: nonpayable

interface PoolToken:
    def balanceOf(arg0: address) -> uint256: view

interface ERC20Pegged:
    def approve(_spender: address, _amount: uint256): nonpayable
    def mint(_to: address, _amount: uint256): nonpayable
    def burn(_amount: uint256): nonpayable
    def balanceOf(arg0: address) -> uint256: view


event Provide:
    amount: uint256


event Withdraw:
    amount: uint256


# Time between minting/burning coins
ACTION_DELAY: constant(uint256) = 15 * 60

# Minimum value to withdraw, if can't withdraw full amount
MIN_POOL_TOKEN_AMOUNT: constant(uint256) = 10 ** 18

PRECISION: constant(uint256) = 10 ** 10
min_asymmetry: public(uint256)


pegged: public(address)
pool: public(address)
pool_token: address

last_change: public(uint256)

admin: public(address)
future_admin: public(address)


@external
def __init__(_pool: address, _min_asymmetry: uint256):
    """
    @notice Contract constructor
    @param _pool Contract pool address
    """
    self.pool = _pool
    self.pool_token = CurvePool(_pool).lp_token()
    self.pegged = CurvePool(_pool).coins(1)

    self.admin = msg.sender

    self.min_asymmetry = _min_asymmetry


@internal
def _provide(_amount: uint256) -> bool:
    pegged: address = self.pegged
    pool: address = self.pool

    # Mint '_amount' of coin
    ERC20Pegged(pegged).mint(self, _amount)
    ERC20Pegged(pegged).approve(pool, _amount)

    # Add '_amount' of coin to the pool
    CurvePool(pool).peg_keeper_add(_amount)

    self.last_change = block.timestamp
    log Provide(_amount)
    return True


@internal
def _withdraw(_amount: uint256) -> bool:
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
    else:
        amount: uint256 = CurvePool(pool).peg_keeper_remove_via_token(token_balance)
        log Withdraw(amount)

    # Burn coins
    coin_balance: uint256 = ERC20Pegged(self.pegged).balanceOf(self)
    ERC20Pegged(self.pegged).burn(coin_balance)

    self.last_change = block.timestamp
    return True


@internal
def _is_balanced(x: uint256, y: uint256) -> bool:
    return PRECISION - 4 * PRECISION * x * y / (x + y) ** 2 < self.min_asymmetry


@external
def update() -> bool:
    """
    @notice Mint or burn coins from the pool to stabilize it
    @return True if peg was maintained, otherwise False
    """
    assert msg.sender == self.pool, "Callable by the pool"
    if self.last_change + ACTION_DELAY > block.timestamp:
        return False

    pool: address = self.pool
    balance_peg: uint256 = CurvePool(pool).balances(0)
    balance_pegged: uint256 = CurvePool(pool).balances(1)

    if self._is_balanced(balance_peg, balance_pegged):
        return False

    if balance_peg > balance_pegged:
        return self._provide((balance_peg - balance_pegged) / 5)
    else:
        return self._withdraw((balance_pegged - balance_peg) / 5)


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
def set_new_min_asymmetry(_new_min_asymmetry: uint256):
    """
    @notice Commit new min_asymmetry of pool
    @param _new_min_asymmetry Min asymmetry with PRECISION
    """
    assert msg.sender == self.admin, "Access denied."
    assert 1 < _new_min_asymmetry, "Bad asymmetry value."
    assert _new_min_asymmetry < PRECISION, "Bad asymmetry value."
    self.min_asymmetry = _new_min_asymmetry
