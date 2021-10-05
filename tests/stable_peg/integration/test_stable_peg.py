import pytest
from brownie import chain
from brownie.test import strategy

pytestmark = pytest.mark.usefixtures(
    "add_initial_liquidity",
    "provide_token_to_peg_keeper",
    "set_peg_keeper",
    "mint_alice",
    "approve_alice",
)


class StateMachine:
    """
    Stateful test that performs a series of deposits, swaps and withdrawals
    and confirms that peg keeper does not fail and pegs correctly.
    """

    st_idx = strategy("int", min_value=0, max_value=1)
    st_pct = strategy("decimal", min_value="0.5", max_value="10000", places=2)

    def __init__(
        cls,
        alice,
        swap,
        decimals,
        min_asymmetry,
        peg_keeper,
        peg_keeper_updater,
        need_manual_update,
    ):
        cls.alice = alice
        cls.swap = swap
        cls.decimals = decimals
        cls.min_asymmetry = min_asymmetry
        cls.balances = [swap.balances(0), swap.balances(1)]

        cls.peg_keeper = peg_keeper
        cls.peg_keeper_updater = peg_keeper_updater
        cls.need_manual_update = need_manual_update

    def _update_balances(self, amounts, remove: bool = False):
        if remove:
            self.balances[0] -= amounts[0]
            self.balances[1] -= amounts[1]
        else:
            self.balances[0] += amounts[0]
            self.balances[1] += amounts[1]

    def _is_balanced(self):
        x, y = self.balances
        return 1e10 - 4e10 * x * y // (x + y) ** 2 < self.min_asymmetry

    def rule_add_one_coin(self, st_idx, st_pct):
        """
        Add one coin to the pool.
        """
        amounts = [0, 0]
        amounts[st_idx] = int(10 ** self.decimals[st_idx] * st_pct)
        self.swap.add_liquidity(amounts, 0, {"from": self.alice})
        self._update_balances(amounts)

    def rule_add_coins(self, amount_0="st_pct", amount_1="st_pct"):
        """
        Add coins to the pool.
        """
        amounts = [
            int(10 ** self.decimals[0] * amount_0),
            int(10 ** self.decimals[1] * amount_1),
        ]
        self.swap.add_liquidity(amounts, 0, {"from": self.alice})
        self._update_balances(amounts)

    def rule_remove_one_coin(self, st_idx, st_pct):
        """
        Remove liquidity from the pool in only one coin.
        """
        amounts = [0, 0]
        token_amount = int(10 ** 18 * st_pct)
        amounts[st_idx] = self.swap.remove_liquidity_one_coin(
            token_amount, st_idx, 0, {"from": self.alice}
        ).return_value
        self._update_balances(amounts, True)

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
        self._update_balances(amounts, True)

    def rule_remove(self, st_pct):
        """
        Remove liquidity from the pool.
        """
        amount = int(10 ** 18 * st_pct)
        amounts = self.swap.remove_liquidity(
            amount, [0] * 2, {"from": self.alice}
        ).return_value
        self._update_balances(amounts, True)

    def rule_exchange(self, st_idx, st_pct):
        """
        Perform a swap.
        """
        amounts = [0, 0]
        amounts[st_idx] = 10 ** self.decimals[st_idx] * st_pct
        amounts[1 - st_idx] = -self.swap.exchange(
            st_idx, 1 - st_idx, amounts[st_idx], 0, {"from": self.alice}
        ).return_value
        self._update_balances(amounts)

    def invariant_check_diff(self):
        """
        Verify that Peg Keeper decreased diff of balances by 1/5.
        """
        if self.need_manual_update:
            self.peg_keeper.update({"from": self.peg_keeper_updater})
        diff = self.swap.balances(0) - self.swap.balances(1)
        last_diff = self.balances[0] - self.balances[1]
        if self._is_balanced():
            assert diff == last_diff
        else:
            # Negative diff can make error of +-1
            last_diff = abs(last_diff)
            assert abs(diff) == last_diff - last_diff // 5
        self.balances = [self.swap.balances(0), self.swap.balances(1)]

    def invariant_advance_time(self):
        """
        Advance the clock by 15 minutes between each action.
        Needed for action_delay in Peg Keeper.
        """
        chain.sleep(15 * 60)


@pytest.mark.parametrize("min_asymmetry", [2, 2e3])
def test_always_peg(
    add_initial_liquidity,
    state_machine,
    swap,
    alice,
    decimals,
    set_fees,
    peg_keeper,
    peg_keeper_updater,
    peg_keeper_type,
    admin,
    min_asymmetry,
):
    set_fees(4 * 10 ** 7, 0)
    peg_keeper.set_new_min_asymmetry(min_asymmetry, {"from": admin})

    # Probably need to lower parameters, test takes 40min
    state_machine(
        StateMachine,
        alice,
        swap,
        decimals,
        min_asymmetry,
        peg_keeper,
        peg_keeper_updater,
        peg_keeper_type != "template",
        settings={"max_examples": 20, "stateful_step_count": 40},
    )
