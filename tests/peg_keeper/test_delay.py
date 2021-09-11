import pytest

from brownie import chain
from flaky import flaky


pytestmark = pytest.mark.usefixtures(
    "add_initial_liquidity",
    "provide_token_to_peg_keeper",
    "set_peg_keeper",
    "mint_bob",
    "approve_bob",
)


def _prepare_for_provide(swap, peg, bob) -> int:
    amount = peg.balanceOf(bob)
    swap.add_liquidity([amount, 0], 0, {"from": bob})

    return amount


def _prepare_for_withdraw(swap, pegged, bob) -> int:
    amount = pegged.balanceOf(bob)
    swap.add_liquidity([0, amount], 0, {"from": bob})

    return amount


@pytest.mark.parametrize("method", ["provide", "withdraw"])
def test_update_delay(peg_keeper, swap, peg, pegged, bob, method):
    if peg_keeper.action_delay():
        if method == "provide":
            _prepare_for_provide(swap, peg, bob)
        else:
            _prepare_for_withdraw(swap, pegged, bob)

        chain.mine(
            timestamp=peg_keeper.last_change() + peg_keeper.action_delay()
        )
        assert peg_keeper.update({"from": swap}).return_value


@pytest.mark.parametrize("method", ["provide", "withdraw"])
@flaky
def test_update_no_delay(peg_keeper, swap, peg, pegged, bob, method):
    if peg_keeper.action_delay():
        if method == "provide":
            _prepare_for_provide(swap, peg, bob)
        else:
            _prepare_for_withdraw(swap, pegged, bob)

        chain.mine(
            timestamp=peg_keeper.last_change() + peg_keeper.action_delay() - 1
        )
        assert not peg_keeper.update({"from": swap}).return_value
