import pytest
from brownie import chain
from brownie.exceptions import VirtualMachineError
from brownie.test import strategy

pytestmark = pytest.mark.usefixtures(
    "add_initial_liquidity",
    "provide_token_to_peg_keeper",
    "mint_alice",
    "approve_alice",
)


class StateMachine:
    """
    Stateful test that performs a series of deposits, swaps and withdrawals
    and confirms that peg keeper's withdraw profit does not take too much.
    """

    st_idx = strategy("int", min_value=0, max_value=1)
    st_pct = strategy("decimal", min_value="0.5", max_value="10000", places=2)

    def __init__(
        cls,
        alice,
        swap,
        pegged,
        peg_keeper,
        decimals,
        receiver,
        always_withdraw,
        peg_keeper_name,
    ):
        cls.alice = alice
        cls.swap = swap
        cls.pegged = pegged
        cls.peg_keeper = peg_keeper
        cls.decimals = decimals
        cls.receiver = receiver
        cls.always_withdraw = always_withdraw
        cls.is_meta = "meta" in peg_keeper_name

    def setup(self):
        # Needed in withdraw profit check
        self.pegged.approve(self.swap, 2 ** 256 - 1, {"from": self.alice})

    def rule_add_one_coin(self, st_idx, st_pct):
        """
        Add one coin to the pool.
        """
        amounts = [0, 0]
        amounts[st_idx] = int(10 ** self.decimals[st_idx] * st_pct)
        self.swap.add_liquidity(amounts, 0, {"from": self.alice})

    def rule_add_coins(self, amount_0="st_pct", amount_1="st_pct"):
        """
        Add coins to the pool.
        """
        amounts = [
            int(10 ** self.decimals[0] * amount_0),
            int(10 ** self.decimals[1] * amount_1),
        ]
        self.swap.add_liquidity(amounts, 0, {"from": self.alice})

    def rule_remove_one_coin(self, st_idx, st_pct):
        """
        Remove liquidity from the pool in only one coin.
        """
        token_amount = int(10 ** 18 * st_pct)
        self.swap.remove_liquidity_one_coin(
            token_amount, st_idx, 0, {"from": self.alice}
        )

    def rule_remove_imbalance(self, amount_0="st_pct", amount_1="st_pct"):
        """
        Remove liquidity from the pool in an imbalanced manner.
        """
        amounts = [
            int(10 ** self.decimals[0] * amount_0),
            int(10 ** self.decimals[1] * amount_1),
        ]
        self.swap.remove_liquidity_imbalance(
            amounts, 2 ** 256 - 1, {"from": self.alice}
        )

    def rule_remove(self, st_pct):
        """
        Remove liquidity from the pool.
        """
        amount = int(10 ** 18 * st_pct)
        self.swap.remove_liquidity(amount, [0] * 2, {"from": self.alice})

    def rule_exchange(self, st_idx, st_pct):
        """
        Perform a swap.
        """
        amount = 10 ** self.decimals[st_idx] * st_pct
        self.swap.exchange(st_idx, 1 - st_idx, amount, 0, {"from": self.alice})

    def rule_withdraw_profit(self):
        """
        Withdraw profit from Peg Keeper.
        """
        profit = self.peg_keeper.calc_profit()
        receiver_balance = self.swap.balanceOf(self.receiver)

        returned = self.peg_keeper.withdraw_profit().return_value

        assert profit == returned
        assert receiver_balance + profit == self.swap.balanceOf(self.receiver)

    def _manual_update(self) -> bool:
        try:
            self.peg_keeper.update({"from": self.alice})
        except VirtualMachineError as e:
            # assert e.revert_msg in [
            #     "dev: peg was unprofitable",
            #     "dev: zero tokens burned",  # StableSwap assertion when add/remove zero coins
            # ]
            return False
        return True

    def invariant_withdraw_profit(self):
        """
        Withdraw profit and check that Peg Keeper is still able to withdraw his debt.
        """
        self._manual_update()
        self.rule_withdraw_profit()

        debt = self.peg_keeper.debt()
        if self.is_meta:
            amount = 5 * (debt + 1) + self.swap.balances(1) * 11 // 10 - self.swap.balances(0)
        else:
            amount = 5 * (debt + 1) + self.swap.balances(1) - self.swap.balances(0)
        self.pegged._mint_for_testing(self.alice, amount, {"from": self.alice})
        self.swap.add_liquidity([amount, 0], 0, {"from": self.alice})

        chain.sleep(15 * 60)
        if self._manual_update():
            assert self.peg_keeper.debt() == 0
            if self.is_meta:
                assert self.swap.balances(1) * 11 // 10 == pytest.approx(self.swap.balances(0) - 4 * debt - 5, abs=10)
            else:
                assert self.swap.balances(1) == self.swap.balances(0) - 4 * debt - 5

        # withdraw_profit, mint, add_liquidity
        chain.undo(2 if self.always_withdraw else 3)

    def invariant_advance_time(self):
        """
        Advance the clock by 15 minutes between each action.
        Needed for action_delay in Peg Keeper.
        """
        chain.sleep(15 * 60)


@pytest.mark.parametrize("always_withdraw", [False, True])
def test_withdraw_profit(
    add_initial_liquidity,
    state_machine,
    swap,
    pegged,
    decimals,
    set_fees,
    peg_keeper,
    admin,
    receiver,
    alice,
    always_withdraw,
    peg_keeper_name,
):
    set_fees(4 * 10 ** 7)

    state_machine(
        StateMachine,
        alice,
        swap,
        pegged,
        peg_keeper,
        decimals,
        receiver,
        always_withdraw,
        peg_keeper_name,
        settings={"max_examples": 10, "stateful_step_count": 10},
    )
