import brownie
import pytest

pytestmark = pytest.mark.usefixtures(
    "add_initial_liquidity", "provide_token_to_peg_keeper", "set_peg_keeper"
)


def test_add(swap, peg, pegged, initial_amounts, peg_keeper):
    amount = initial_amounts[1]
    pegged._mint_for_testing(peg_keeper, amount, {"from": peg_keeper})
    pegged.approve(swap, amount, {"from": peg_keeper})

    balances = [swap.balances(0), swap.balances(1)]
    real_balances = [peg.balanceOf(swap), pegged.balanceOf(swap)]

    swap.peg_keeper_add(amount, {"from": peg_keeper})

    new_balances = [swap.balances(0), swap.balances(1)]
    new_real_balances = [peg.balanceOf(swap), pegged.balanceOf(swap)]
    assert new_balances[0] == balances[0]
    assert int(new_balances[1]) == balances[1] + amount

    assert new_real_balances[0] == real_balances[0]
    assert new_real_balances[1] == real_balances[1] + amount


def test_add_access(swap, bob):
    with brownie.reverts("Callable only by Peg Keeper"):
        swap.peg_keeper_add(100, {"from": bob})


def test_remove(swap, peg, pegged, initial_amounts, peg_keeper):
    amount = initial_amounts[0] // 2

    balances = [swap.balances(0), swap.balances(1)]
    real_balances = [peg.balanceOf(swap), pegged.balanceOf(swap)]

    swap.peg_keeper_remove(amount, {"from": peg_keeper})

    new_balances = [swap.balances(0), swap.balances(1)]
    new_real_balances = [peg.balanceOf(swap), pegged.balanceOf(swap)]
    assert new_balances[0] == balances[0]
    assert int(new_balances[1]) == balances[1] - amount

    assert new_real_balances[0] == real_balances[0]
    assert new_real_balances[1] == real_balances[1] - amount


def test_remove_access(swap, bob):
    with brownie.reverts("Callable only by Peg Keeper"):
        swap.peg_keeper_remove(100, {"from": bob})


def test_remove_via_token(swap, peg, pegged, pool_token, peg_keeper):
    token_amount = pool_token.balanceOf(peg_keeper)

    balances = [swap.balances(0), swap.balances(1)]
    real_balances = [peg.balanceOf(swap), pegged.balanceOf(swap)]

    amount = swap.peg_keeper_remove_via_token(
        token_amount, {"from": peg_keeper}
    ).return_value
    assert amount > 0

    new_balances = [swap.balances(0), swap.balances(1)]
    new_real_balances = [peg.balanceOf(swap), pegged.balanceOf(swap)]
    assert new_balances[0] == balances[0]
    assert int(new_balances[1]) == balances[1] - amount

    assert new_real_balances[0] == real_balances[0]
    assert new_real_balances[1] == real_balances[1] - amount


def test_remove_via_token_access(swap, bob):
    with brownie.reverts("Callable only by Peg Keeper"):
        swap.peg_keeper_remove_via_token(100, {"from": bob})
