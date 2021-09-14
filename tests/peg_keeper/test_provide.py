import pytest
from brownie.test import given, strategy

pytestmark = pytest.mark.usefixtures(
    "add_initial_liquidity", "mint_alice", "approve_alice",
)


@given(amount=strategy("uint256", min_value=10 ** 20, max_value=10 ** 24))
def test_provide(swap, peg, pegged, alice, amount, peg_keeper):
    swap.add_liquidity([amount, 0], 0, {"from": alice})
    balances = [swap.balances(0), swap.balances(1)]
    real_balances = [peg.balanceOf(swap), pegged.balanceOf(swap)]

    swap.set_peg_keeper(peg_keeper, {"from": alice})
    assert peg_keeper.update({"from": swap}).return_value

    new_balances = [swap.balances(0), swap.balances(1)]
    new_real_balances = [peg.balanceOf(swap), pegged.balanceOf(swap)]
    assert new_balances[0] == balances[0]
    assert int(new_balances[1]) == balances[1] + amount // 5

    assert new_real_balances[0] == real_balances[0]
    assert new_real_balances[1] == real_balances[1] + amount // 5


def test_min_coin_amount(swap, initial_amounts, alice, peg_keeper):
    swap.add_liquidity([initial_amounts[0], 0], 0, {"from": alice})
    swap.set_peg_keeper(peg_keeper, {"from": alice})
    assert peg_keeper.update({"from": swap}).return_value


def test_less_min_coin_amount(swap, alice, peg_keeper):
    swap.add_liquidity([1, 0], 0, {"from": alice})
    swap.set_peg_keeper(peg_keeper, {"from": alice})
    assert not peg_keeper.update({"from": swap}).return_value


def test_event(swap, initial_amounts, alice, peg_keeper, set_peg_keeper):
    tx = swap.add_liquidity([initial_amounts[0], 0], 0, {"from": alice})
    event = tx.events["Provide"]
    assert event["amount"] == initial_amounts[0] // 5
