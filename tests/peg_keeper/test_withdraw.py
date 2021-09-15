import pytest
from brownie.test import given, strategy

pytestmark = pytest.mark.usefixtures(
    "add_initial_liquidity",
    "provide_token_to_peg_keeper",
    "mint_alice",
    "approve_alice",
)


@given(amount=strategy("uint256", min_value=10 ** 20, max_value=10 ** 24))
def test_withdraw(swap, peg, pegged, alice, amount, peg_keeper):
    swap.add_liquidity([0, amount], 0, {"from": alice})
    balances = [swap.balances(0), swap.balances(1)]
    real_balances = [peg.balanceOf(swap), pegged.balanceOf(swap)]

    swap.set_peg_keeper(peg_keeper, {"from": alice})
    assert peg_keeper.update({"from": swap}).return_value

    new_balances = [swap.balances(0), swap.balances(1)]
    new_real_balances = [peg.balanceOf(swap), pegged.balanceOf(swap)]
    assert new_balances[0] == balances[0]
    assert int(new_balances[1]) == balances[1] - amount // 5

    assert new_real_balances[0] == real_balances[0]
    assert new_real_balances[1] == real_balances[1] - amount // 5


def test_withdraw_insufficient_token_balance(
    swap, peg, pegged, alice, initial_amounts, peg_keeper
):
    """ Provide 1000x of pegged, so Peg Keeper can't withdraw the whole 1/5 part. """
    amount = 1000 * initial_amounts[1]
    pegged._mint_for_testing(alice, amount, {"from": alice})
    pegged.approve(swap, amount, {"from": alice})
    swap.add_liquidity([0, amount], 0, {"from": alice})
    balances = [swap.balances(0), swap.balances(1)]
    real_balances = [peg.balanceOf(swap), pegged.balanceOf(swap)]

    swap.set_peg_keeper(peg_keeper, {"from": alice})
    assert peg_keeper.update({"from": swap}).return_value

    new_balances = [swap.balances(0), swap.balances(1)]
    new_real_balances = [peg.balanceOf(swap), pegged.balanceOf(swap)]
    assert new_balances[0] == balances[0]
    assert balances[1] > int(new_balances[1]) > balances[1] - amount // 5

    assert new_real_balances[0] == real_balances[0]
    assert real_balances[1] > new_real_balances[1] > real_balances[1] - amount // 5


def test_withdraw_dust_token_balance(
    swap, pool_token, peg, pegged, alice, initial_amounts, peg_keeper
):
    amount = initial_amounts[1]
    pegged._mint_for_testing(alice, amount, {"from": alice})
    pegged.approve(swap, amount, {"from": alice})
    swap.add_liquidity([0, amount], 0, {"from": alice})

    token_balance = pool_token.balanceOf(peg_keeper)
    pool_token.transfer(alice, token_balance - 100, {"from": peg_keeper})
    swap.set_peg_keeper(peg_keeper, {"from": alice})
    assert not peg_keeper.update({"from": swap}).return_value


def test_min_coin_amount(swap, initial_amounts, alice, peg_keeper):
    swap.add_liquidity([0, initial_amounts[1]], 0, {"from": alice})
    swap.set_peg_keeper(peg_keeper, {"from": alice})
    assert peg_keeper.update({"from": swap}).return_value


def test_less_min_coin_amount(swap, alice, peg_keeper):
    swap.add_liquidity([0, 1], 0, {"from": alice})
    swap.set_peg_keeper(peg_keeper, {"from": alice})
    assert not peg_keeper.update({"from": swap}).return_value


def test_event(swap, initial_amounts, alice, peg_keeper, set_peg_keeper):
    tx = swap.add_liquidity([0, initial_amounts[1]], 0, {"from": alice})
    event = tx.events["Withdraw"]
    assert event["amount"] == initial_amounts[1] // 5
