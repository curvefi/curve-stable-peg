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
    def balanceOf(arg0: address) -> uint256: view


event Provide:
    amount: uint256


event Withdraw:
    amount: uint256


event Profit:
    lp_amount: uint256


event WithdrawPegged:
    amount: uint256
    receiver: address


# Time between providing/withdrawing coins
ACTION_DELAY: constant(uint256) = 15 * 60
ADMIN_ACTIONS_DELAY: constant(uint256) = 3 * 86400

# Minimum value to provide/withdraw, if can't provide/withdraw full amount
MIN_PEGGED_AMOUNT: constant(uint256) = 10 ** 18

ASYMMETRY_PRECISION: constant(uint256) = 10 ** 10
min_asymmetry: public(uint256)

PRECISION: constant(uint256) = 10 ** 18
# Calculation error for profit
PROFIT_THRESHOLD: constant(uint256) = 10 ** 18

pegged: public(address)
pool: public(address)

last_change: public(uint256)
debt: public(uint256)

SHARE_PRECISION: constant(uint256) = 10 ** 5
caller_share: public(uint256)

admin: public(address)
future_admin: public(address)

pegged_admin: public(address)
future_pegged_admin: public(address)

# Receiver of profit
receiver: public(address)
future_receiver: public(address)

admin_actions_deadline: public(uint256)


@external
def __init__(_pool: address, _receiver: address, _min_asymmetry: uint256, _caller_share: uint256):
    """
    @notice Contract constructor
    @param _pool Contract pool address
    @param _receiver Receiver of the profit
    @param _min_asymmetry Min asymmetry for pegging
    @param _caller_share Caller's share of profit
    """
    self.pool = _pool
    self.pegged = CurvePool(_pool).coins(0)
    ERC20Pegged(self.pegged).approve(_pool, MAX_UINT256)

    self.admin = msg.sender
    self.pegged_admin = msg.sender
    self.receiver = _receiver

    self.min_asymmetry = _min_asymmetry
    self.caller_share = _caller_share


@internal
def _provide(_amount: uint256) -> bool:
    pegged_balance: uint256 = ERC20Pegged(self.pegged).balanceOf(self)
    amount: uint256 = _amount
    if amount > pegged_balance:
        if pegged_balance < MIN_PEGGED_AMOUNT:
            return False
        amount = pegged_balance

    CurvePool(self.pool).add_liquidity([amount, 0], 0)

    self.last_change = block.timestamp
    self.debt += amount

    log Provide(amount)

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

    self.last_change = block.timestamp
    self.debt -= amount

    log Withdraw(amount)

    return True


@internal
@view
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
@view
def calc_profit() -> uint256:
    """
    @notice Calculate generated profit in LP tokens
    @return Amount of generated profit
    """
    return self._calc_profit()


@external
@nonpayable
def update(_beneficiary: address = msg.sender) -> uint256:
    """
    @notice Provide or withdraw coins from the pool to stabilize it
    @param _beneficiary Beneficiary address
    @return Amount of profit received by beneficiary
    """
    if self.last_change + ACTION_DELAY > block.timestamp:
        return 0

    pool: address = self.pool
    balance_pegged: uint256 = CurvePool(pool).balances(0)
    balance_peg: uint256 = CurvePool(pool).balances(1)

    if self._is_balanced(balance_peg, balance_pegged):
        return 0

    initial_profit: uint256 = self._calc_profit()

    status: bool = False
    if balance_peg > balance_pegged:
        status = self._provide((balance_peg - balance_pegged) / 5)
    else:
        status = self._withdraw((balance_pegged - balance_peg) / 5)

    if not status:
        return 0

    # Send generated profit
    new_profit: uint256 = self._calc_profit()
    assert new_profit >= initial_profit  # dev: peg was unprofitable
    lp_amount: uint256 = new_profit - initial_profit
    caller_profit: uint256 = lp_amount * self.caller_share / SHARE_PRECISION
    CurvePool(self.pool).transfer(_beneficiary, caller_profit)

    return caller_profit


@external
@nonpayable
def set_new_min_asymmetry(_new_min_asymmetry: uint256):
    """
    @notice Set new min_asymmetry of pool
    @param _new_min_asymmetry Min asymmetry with PRECISION
    """
    assert msg.sender == self.admin  # dev: only admin
    assert 1 < _new_min_asymmetry  # dev: bad asymmetry value
    assert _new_min_asymmetry < ASYMMETRY_PRECISION  # dev: bad asymmetry value

    self.min_asymmetry = _new_min_asymmetry


@external
@nonpayable
def set_new_caller_share(_new_caller_share: uint256):
    """
    @notice Set new update caller's part
    @param _new_caller_share Part with SHARE_PRECISION
    """
    assert msg.sender == self.admin  # dev: only admin
    assert _new_caller_share <= SHARE_PRECISION  # dev: bad part value

    self.caller_share = _new_caller_share


@external
@nonpayable
def commit_new_pegged_admin(_new_pegged_admin: address):
    """
    @notice Commit new pegged admin
    @param _new_pegged_admin New pegged admin address
    """
    assert msg.sender == self.pegged_admin  # dev: only pegged admin
    self.future_pegged_admin = _new_pegged_admin


@external
@nonpayable
def apply_new_pegged_admin():
    """
    @notice Apply new pegged admin
    @dev Should be executed from new pegged admin
    """
    assert msg.sender == self.future_pegged_admin  # dev: only new pegged admin
    self.pegged_admin = self.future_pegged_admin


@external
@nonpayable
def withdraw_pegged(_amount: uint256, _receiver: address = msg.sender) -> uint256:
    """
    @notice Withdraw pegged coin from PegKeeper
    @dev Min(pegged_balance, _amount) will be withdrawn. Should be executed from pegged admin
    @param _amount Amount of coin to withdraw
    @param _receiver Address that receives the withdrawn coins
    @return Amount of withdrawn pegged
    """
    assert msg.sender == self.pegged_admin  # dev: only pegged admin

    pegged_balance: uint256 = ERC20Pegged(self.pegged).balanceOf(self)

    if pegged_balance == 0:
        return 0

    amount: uint256 = _amount
    if amount > pegged_balance:
        amount = pegged_balance

    response: Bytes[32] = raw_call(
        self.pegged,
        concat(
            method_id("transfer(address,uint256)"),
            convert(_receiver, bytes32),
            convert(amount, bytes32),
        ),
        max_outsize=32,
    )
    if len(response) > 0:
        assert convert(response, bool)

    log WithdrawPegged(amount, _receiver)

    return amount

@external
@nonpayable
def withdraw_profit() -> uint256:
    """
    @notice Withdraw profit generated by Peg Keeper
    @return Amount of LP Token received
    """
    lp_amount: uint256 = self._calc_profit()
    CurvePool(self.pool).transfer(self.receiver, lp_amount)

    log Profit(lp_amount)

    return lp_amount


@external
@nonpayable
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
@nonpayable
def apply_new_admin():
    """
    @notice Apply new admin of the Peg Keeper
    @dev Should be executed from new admin
    """
    assert msg.sender == self.future_admin  # dev: only new admin
    assert block.timestamp >= self.admin_actions_deadline  # dev: insufficient time
    assert self.admin_actions_deadline != 0  # dev: no active action

    self.admin = self.future_admin
    self.admin_actions_deadline = 0


@external
@nonpayable
def commit_new_receiver(_new_receiver: address):
    """
    @notice Commit new receiver of profit
    @param _new_receiver Address of the new receiver
    """
    assert msg.sender == self.admin  # dev: only admin
    assert self.admin_actions_deadline == 0 # dev: active action

    deadline: uint256 = block.timestamp + ADMIN_ACTIONS_DELAY
    self.admin_actions_deadline = deadline
    self.future_receiver = _new_receiver


@external
@nonpayable
def apply_new_receiver():
    """
    @notice Apply new receiver of profit
    """
    assert block.timestamp >= self.admin_actions_deadline  # dev: insufficient time
    assert self.admin_actions_deadline != 0  # dev: no active action

    self.receiver = self.future_receiver
    self.admin_actions_deadline = 0


@external
@nonpayable
def revert_new_staff():
    """
    @notice Revert new admin of the Peg Keeper
    @dev Should be executed from admin
    """
    assert msg.sender == self.admin  # dev: only admin

    self.admin_actions_deadline = 0
