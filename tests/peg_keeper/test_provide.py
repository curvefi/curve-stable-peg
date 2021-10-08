import pytest
from brownie.test import given, strategy

pytestmark = pytest.mark.usefixtures(
    "add_initial_liquidity",
    "mint_alice",
    "approve_alice",
)


@given(amount=strategy("uint256", min_value=10 ** 20, max_value=10 ** 24))
def test_provide(
    swap,
    peg,
    pegged,
    alice,
    amount,
    peg_keeper,
    peg_keeper_updater,
    set_peg_keeper_func,
):
    swap.add_liquidity([0, amount], 0, {"from": alice})
    balances = [swap.balances(0), swap.balances(1)]
    real_balances = [pegged.balanceOf(swap), peg.balanceOf(swap)]

    set_peg_keeper_func()
    assert peg_keeper.update({"from": peg_keeper_updater}).return_value

    new_balances = [swap.balances(0), swap.balances(1)]
    new_real_balances = [pegged.balanceOf(swap), peg.balanceOf(swap)]
    assert new_balances[0] == balances[0] + amount // 5
    assert new_balances[1] == balances[1]

    assert new_real_balances[0] == real_balances[0] + amount // 5
    assert new_real_balances[1] == real_balances[1]


def test_min_coin_amount(
    swap, initial_amounts, alice, peg_keeper, peg_keeper_updater, set_peg_keeper_func
):
    swap.add_liquidity([0, initial_amounts[1]], 0, {"from": alice})
    set_peg_keeper_func()
    assert peg_keeper.update({"from": peg_keeper_updater}).return_value


def test_almost_balanced(
    swap, alice, peg_keeper, peg_keeper_updater, set_peg_keeper_func
):
    swap.add_liquidity([0, 10 ** 18], 0, {"from": alice})
    set_peg_keeper_func()
    assert not peg_keeper.update({"from": peg_keeper_updater}).return_value


def test_event(swap, initial_amounts, alice, peg_keeper, peg_keeper_updater):
    swap.add_liquidity([0, initial_amounts[1]], 0, {"from": alice})
    tx = peg_keeper.update({"from": peg_keeper_updater})
    event = tx.events["Provide"]
    assert event["amount"] == initial_amounts[1] // 5
