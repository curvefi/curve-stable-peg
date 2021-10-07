# (c) Curve.Fi, 2021
# Peg Keeper for pool with equal decimals of coins
# @version 0.2.15


interface CurvePool:
    def balances(i_coin: uint256) -> uint256: view
    def coins(i: uint256) -> address: view
    def lp_token() -> address: view
    def add_liquidity(_amounts: uint256[2], _min_mint_amount: uint256) -> uint256: nonpayable
    def remove_liquidity_imbalance(_amounts: uint256[2], _max_burn_amount: uint256) -> uint256: nonpayable
    def get_virtual_price() -> uint256: view
    def balanceOf(arg0: address) -> uint256: view
    def transfer(_to : address, _value : uint256) -> bool: nonpayable

interface ERC20Pegged:
    def approve(_spender: address, _amount: uint256): nonpayable
    def mint(_to: address, _amount: uint256): nonpayable
    def burn(_amount: uint256): nonpayable
    def balanceOf(arg0: address) -> uint256: view


event Provide:
    amount: uint256


event Withdraw:
    amount: uint256


event Profit:
    lp_amount: uint256


# Time between minting/burning coins
ACTION_DELAY: constant(uint256) = 15 * 60
ADMIN_ACTIONS_DELAY: constant(uint256) = 3 * 86400

# Minimum value to provide/withdraw, if can't provide/withdraw full amount
MIN_PEGGED_AMOUNT: constant(uint256) = 10 ** 18

ASYMMETRY_PRECISION: constant(uint256) = 10 ** 10
min_asymmetry: public(uint256)

PRECISION: constant(uint256) = 10 ** 18
# Calculation error for profit
PROFIT_THRESHOLD: constant(uint256) = 10 ** 8


pegged: public(address)
pool: public(address)

last_change: public(uint256)
debt: public(uint256)

admin: public(address)
future_admin: public(address)

admin_actions_deadline: public(uint256)


@external
def __init__(_pool: address, _min_asymmetry: uint256):
    """
    @notice Contract constructor
    @param _pool Contract pool address
    """
    self.pool = _pool
    self.pegged = CurvePool(_pool).coins(0)
    ERC20Pegged(self.pegged).approve(_pool, MAX_UINT256)

    self.admin = msg.sender

    self.min_asymmetry = _min_asymmetry


@internal
def _provide(_amount: uint256) -> bool:
    ERC20Pegged(self.pegged).mint(self, _amount)

    CurvePool(self.pool).add_liquidity([_amount, 0], 0)

    self.last_change = block.timestamp
    self.debt += _amount
    log Provide(_amount)
    return True


@internal
def _withdraw(_amount: uint256) -> bool:
    debt: uint256 = self.debt
    amount: uint256 = _amount
    if amount > debt:
        if debt < MIN_PEGGED_AMOUNT:
            return False
        amount = debt

    CurvePool(self.pool).remove_liquidity_imbalance([amount, 0], MAX_UINT256)

    coin_balance: uint256 = ERC20Pegged(self.pegged).balanceOf(self)
    ERC20Pegged(self.pegged).burn(coin_balance)

    self.last_change = block.timestamp
    self.debt -= amount
    log Withdraw(amount)
    return True


@internal
def _is_balanced(x: uint256, y: uint256) -> bool:
    return ASYMMETRY_PRECISION - 4 * ASYMMETRY_PRECISION * x * y / (x + y) ** 2 < self.min_asymmetry


@internal
@view
def _calc_profit() -> uint256:
    lp_balance: uint256 = CurvePool(self.pool).balanceOf(self)

    virtual_price: uint256 = CurvePool(self.pool).get_virtual_price()
    lp_debt: uint256 = self.debt * PRECISION / virtual_price

    if lp_balance <= lp_debt + PROFIT_THRESHOLD:
        return 0
    else:
        return lp_balance - lp_debt - PROFIT_THRESHOLD


@external
def update(_profit_receiver: address = msg.sender) -> bool:
    """
    @notice Mint or burn coins from the pool to stabilize it
    @return True if peg was maintained, otherwise False
    """
    if self.last_change + ACTION_DELAY > block.timestamp:
        return False

    pool: address = self.pool
    balance_pegged: uint256 = CurvePool(pool).balances(0)
    balance_peg: uint256 = CurvePool(pool).balances(1)

    if self._is_balanced(balance_peg, balance_pegged):
        return False

    status: bool = False
    if balance_peg > balance_pegged:
        status = self._provide((balance_peg - balance_pegged) / 5)
    else:
        status = self._withdraw((balance_pegged - balance_peg) / 5)

    if not status:
        return False

    # Send generated profit
    lp_amount: uint256 = self._calc_profit()
    CurvePool(self.pool).transfer(_profit_receiver, lp_amount)

    return True


@external
def set_new_min_asymmetry(_new_min_asymmetry: uint256):
    """
    @notice Commit new min_asymmetry of pool
    @param _new_min_asymmetry Min asymmetry with PRECISION
    """
    assert msg.sender == self.admin  # dev: only admin
    assert 1 < _new_min_asymmetry  # dev: bad asymmetry value
    assert _new_min_asymmetry < ASYMMETRY_PRECISION  # dev: bad asymmetry value

    self.min_asymmetry = _new_min_asymmetry


@external
def commit_new_admin(_new_admin: address):
    """
    @notice Commit new admin of the Peg Keeper
    @param _new_admin Address of the new admin
    """
    assert msg.sender == self.admin  # dev: only admin
    assert self.admin_actions_deadline == 0 # dev: active action

    deadline: uint256 = block.timestamp + ADMIN_ACTIONS_DELAY
    self.admin_actions_deadline = deadline
    self.future_admin = _new_admin


@external
def apply_new_admin():
    """
    @notice Apply new admin of the Peg Keeper
    @dev Should be executed from new admin
    """
    assert block.timestamp >= self.admin_actions_deadline  # dev: insufficient time
    assert self.admin_actions_deadline != 0  # dev: no active action

    self.admin = self.future_admin
    self.admin_actions_deadline = 0


@external
def revert_new_staff():
    assert msg.sender == self.admin  # dev: only admin

    self.admin_actions_deadline = 0
