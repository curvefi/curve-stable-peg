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
    and confirms that profit is calculated right.
    """

    st_idx = strategy("int", min_value=0, max_value=1)
    st_pct = strategy("decimal", min_value="0.5", max_value="10000", places=2)

    def __init__(cls, alice, swap, peg_keeper, decimals):
        cls.alice = alice
        cls.swap = swap
        cls.peg_keeper = peg_keeper
        cls.decimals = decimals
        cls.profit = 0

    def setup(self):
        self.profit = self.peg_keeper.calc_profit()

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

    def invariant_profit_increases(self):
        """
        Verify that Peg Keeper profit only increases.
        """
        profit = self.peg_keeper.calc_profit()
        assert profit >= self.profit
        self.profit = profit

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

    def invariant_profit(self):
        """
        Check Profit value.
        """
        self._manual_update()

        profit = self.peg_keeper.calc_profit()
        virtual_price = self.swap.get_virtual_price()
        aim_profit = (
            self.swap.balanceOf(self.peg_keeper)
            - self.peg_keeper.debt() * 10 ** 18 // virtual_price
        )
        assert aim_profit >= profit  # Never take more than real profit
        assert aim_profit - profit < 2e18  # Error less than 2 LP Tokens

    def invariant_advance_time(self):
        """
        Advance the clock by 15 minutes between each action.
        Needed for action_delay in Peg Keeper.
        """
        chain.sleep(15 * 60)


def test_profit_increases(
    add_initial_liquidity,
    state_machine,
    swap,
    alice,
    decimals,
    set_fees,
    peg_keeper,
    admin,
):
    set_fees(4 * 10 ** 7, 0)

    state_machine(
        StateMachine,
        alice,
        swap,
        peg_keeper,
        decimals,
        settings={"max_examples": 20, "stateful_step_count": 40},
    )
