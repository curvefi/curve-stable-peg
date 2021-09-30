import brownie
import pytest

pytestmark = pytest.mark.usefixtures(
    "add_initial_liquidity", "provide_token_to_peg_keeper", "set_peg_keeper"
)


def test_add(swap, peg, pegged, initial_amounts, peg_keeper):
    amount = initial_amounts[1]
    pegged._mint_for_testing(peg_keeper, amount, {"from": peg_keeper})

    balances = [swap.balances(0), swap.balances(1)]
    real_balances = [peg.balanceOf(swap), pegged.balanceOf(swap)]

    swap.peg_keeper_add(amount, {"from": peg_keeper})

    new_balances = [swap.balances(0), swap.balances(1)]
    new_real_balances = [peg.balanceOf(swap), pegged.balanceOf(swap)]
    assert new_balances[0] == balances[0]
    assert new_balances[1] == balances[1] + amount

    assert new_real_balances[0] == real_balances[0]
    assert new_real_balances[1] == real_balances[1] + amount


def test_add_insufficient(swap, pegged, initial_amounts, peg_keeper):
    amount = initial_amounts[1]
    pegged._mint_for_testing(peg_keeper, amount, {"from": peg_keeper})

    with brownie.reverts():
        swap.peg_keeper_add(amount + 1, {"from": peg_keeper})


def test_add_access(swap, bob):
    with brownie.reverts("Callable only by Peg Keeper"):
        swap.peg_keeper_add(100, {"from": bob})


def test_event(swap, peg_keeper, pegged, pool_token, initial_amounts):
    amount = initial_amounts[1]
    pegged._mint_for_testing(peg_keeper, amount, {"from": peg_keeper})
    tx = swap.peg_keeper_add(amount, {"from": peg_keeper})

    event = tx.events["AddLiquidity"]
    assert event["provider"] == peg_keeper
    assert event["token_amounts"] == [0, amount]
    assert event["fees"] == [0, 0]
    assert event["token_supply"] == pool_token.totalSupply()
