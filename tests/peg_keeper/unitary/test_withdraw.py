import brownie
import pytest
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy

pytestmark = pytest.mark.usefixtures(
    "add_initial_liquidity",
    "provide_token_to_peg_keeper",
    "mint_alice",
    "approve_alice",
)


@given(amount=strategy("uint256", min_value=10 ** 20, max_value=10 ** 24))
def test_withdraw(
    swap,
    peg,
    pegged,
    alice,
    amount,
    peg_keeper,
    peg_keeper_updater,
):
    swap.add_liquidity([amount, 0], 0, {"from": alice})
    balances = [swap.balances(0), swap.balances(1)]
    real_balances = [pegged.balanceOf(swap), peg.balanceOf(swap)]

    assert peg_keeper.update({"from": peg_keeper_updater}).return_value

    new_balances = [swap.balances(0), swap.balances(1)]
    new_real_balances = [pegged.balanceOf(swap), peg.balanceOf(swap)]
    assert new_balances[0] == balances[0] - amount // 5
    assert new_balances[1] == balances[1]

    assert new_real_balances[0] == real_balances[0] - amount // 5
    assert new_real_balances[1] == real_balances[1]


def test_withdraw_insufficient_debt(
    swap,
    peg,
    pegged,
    alice,
    initial_amounts,
    peg_keeper,
    peg_keeper_updater,
):
    """Provide 1000x of pegged, so Peg Keeper can't withdraw the whole 1/5 part."""
    amount = 1000 * initial_amounts[0]
    pegged._mint_for_testing(alice, amount, {"from": alice})
    pegged.approve(swap, amount, {"from": alice})
    swap.add_liquidity([amount, 0], 0, {"from": alice})
    balances = [swap.balances(0), swap.balances(1)]
    real_balances = [pegged.balanceOf(swap), peg.balanceOf(swap)]

    assert peg_keeper.update({"from": peg_keeper_updater}).return_value

    new_balances = [swap.balances(0), swap.balances(1)]
    new_real_balances = [pegged.balanceOf(swap), peg.balanceOf(swap)]
    assert balances[0] > new_balances[0] > balances[0] - amount // 5
    assert new_balances[1] == balances[1]

    assert real_balances[0] > new_real_balances[0] > real_balances[0] - amount // 5
    assert new_real_balances[1] == real_balances[1]


def test_withdraw_dust_debt(
    swap,
    peg,
    pegged,
    alice,
    initial_amounts,
    peg_keeper,
    peg_keeper_updater,
    balance_change_after_withdraw,
):
    amount = 5 * (initial_amounts[0] - 1)
    pegged._mint_for_testing(alice, 2 * amount, {"from": alice})
    pegged.approve(swap, 2 * amount, {"from": alice})

    # Peg Keeper withdraws almost all debt
    swap.add_liquidity([amount, 0], 0, {"from": alice})
    assert peg_keeper.update({"from": peg_keeper_updater}).return_value
    balance_change_after_withdraw(amount)

    remove_amount = swap.balances(0) - swap.balances(1)
    swap.remove_liquidity_imbalance([remove_amount, 0], 2 ** 256 - 1, {"from": alice})
    assert swap.balances(0) == swap.balances(1)

    # Does not withdraw anything
    swap.add_liquidity([amount, 0], 0, {"from": alice})
    assert not peg_keeper.update({"from": peg_keeper_updater}).return_value


def test_almost_balanced(
    swap,
    alice,
    peg_keeper,
    peg_keeper_updater,
    set_fees,
):
    swap.add_liquidity([10 ** 18, 0], 0, {"from": alice})
    set_fees(1 * 10 ** 6, 0)
    with brownie.reverts():  # dev: peg was unprofitable
        peg_keeper.update({"from": peg_keeper_updater})


def test_event(swap, initial_amounts, alice, peg_keeper, peg_keeper_updater):
    swap.add_liquidity([initial_amounts[0], 0], 0, {"from": alice})
    tx = peg_keeper.update({"from": peg_keeper_updater})
    event = tx.events["Withdraw"]
    assert event["amount"] == initial_amounts[0] // 5
