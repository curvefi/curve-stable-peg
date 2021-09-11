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


MIN_COIN = 10 ** 6


class StateMachine:
    """
    Stateful test that performs a series of deposits, swaps and withdrawals
    and confirms that the virtual price only goes up.
    """

    st_idx = strategy("int", min_value=0, max_value=1)
    st_pct = strategy("decimal", min_value="0.5", max_value="1", places=2)

    def __init__(cls, alice, swap, decimals):
        cls.alice = alice
        cls.swap = swap
        cls.decimals = decimals
        cls.last_diff = 0

    def rule_add_one_coin(self, st_idx, st_pct):
        """
        Add one coin to the pool.
        """
        amounts = [0, 0]
        amounts[st_idx] = int(10 ** self.decimals[st_idx] * st_pct)
        self.swap.add_liquidity(amounts, 0, {"from": self.alice})
        self.last_diff += amounts[0] - amounts[1]

    def rule_add_coins(self, amount_0="st_pct", amount_1="st_pct"):
        """
        Add one coin to the pool.
        """
        amounts = [
            int(10 ** self.decimals[0] * amount_0),
            int(10 ** self.decimals[1] * amount_1),
        ]
        self.swap.add_liquidity(amounts, 0, {"from": self.alice})
        self.last_diff += amounts[0] - amounts[1]

    def rule_remove_one_coin(self, st_idx, st_pct):
        """
        Remove liquidity from the pool in only one coin.
        """
        amounts = [0, 0]
        token_amount = int(10 ** self.decimals[st_idx] * st_pct)
        amounts[st_idx] = self.swap.remove_liquidity_one_coin(token_amount, st_idx, 0, {"from": self.alice}).return_value
        self.last_diff -= amounts[0] - amounts[1]

    def rule_remove_imbalance(self, amount_0="st_pct", amount_1="st_pct"):
        """
        Remove liquidity from the pool in an imbalanced manner.
        """
        amounts = [
            int(10 ** self.decimals[0] * amount_0),
            int(10 ** self.decimals[1] * amount_1),
        ]
        self.swap.remove_liquidity_imbalance(amounts, 2 ** 256 - 1, {"from": self.alice})
        self.last_diff -= amounts[0] - amounts[1]

    def rule_remove(self, st_pct):
        """
        Remove liquidity from the pool.
        """
        amount = int(10 ** 18 * st_pct)
        amounts = self.swap.remove_liquidity(amount, [0] * 2, {"from": self.alice}).return_value
        self.last_diff -= amounts[0] - amounts[1]

    def rule_exchange(self, st_idx, st_pct):
        """
        Perform a swap.
        """
        amounts = [0, 0]
        amounts[st_idx] = 10 ** self.decimals[st_idx] * st_pct
        amounts[1 - st_idx] = -self.swap.exchange(st_idx, 1 - st_idx, amounts[st_idx], 0, {"from": self.alice}).return_value
        self.last_diff += amounts[0] - amounts[1]

    def invariant_check_diff(self):
        """
        Verify that Peg Keeper decreased diff of balances by 1/5.
        """
        diff = self.swap.balances(0) - self.swap.balances(1)
        if abs(self.last_diff) >= MIN_COIN:
            # Negative diff can make error of +-1
            self.last_diff = abs(self.last_diff)
            assert abs(diff) == self.last_diff - self.last_diff // 5
        else:
            assert diff == self.last_diff
        self.last_diff = diff

    def invariant_advance_time(self):
        """
        Advance the clock by 1 hour between each action.
        Needed for action_delay in Peg Keeper.
        """
        chain.sleep(3600)


def test_always_peg(
    add_initial_liquidity,
    state_machine,
    swap,
    alice,
    bob,
    coins,
    decimals,
    base_amount,
    set_fees,
):
    set_fees(4 * 10 ** 7, 0)

    # Probably need to lower parameters, test takes 40min
    state_machine(
        StateMachine,
        alice,
        swap,
        decimals,
        settings={"max_examples": 25, "stateful_step_count": 50},
    )
