import pytest

from pytest import approx
from brownie.test import given, strategy


pytestmark = pytest.mark.usefixtures("add_initial_liquidity")


@given(amount=strategy("uint256", min_value=10 ** 18, max_value=10 ** 20))
def test_provide(swap, peg, pegged, peg_keeper, amount):
    balances = [swap.balances(0), swap.balances(1)]
    real_balances = [peg.balanceOf(swap), pegged.balanceOf(swap)]

    assert peg_keeper.provide(amount, {"from": swap}).return_value

    new_balances = [swap.balances(0), swap.balances(1)]
    new_real_balances = [peg.balanceOf(swap), pegged.balanceOf(swap)]
    assert new_balances[0] == balances[0]
    assert int(new_balances[1]) == approx(balances[1] + amount, abs=amount * swap.fee() / 10 ** 10)

    assert new_real_balances[0] == real_balances[0]
    assert new_real_balances[1] == real_balances[1] + amount


def test_min_coin_amount(peg_keeper, swap):
    assert peg_keeper.provide(10 ** 24, {"from": swap}).return_value


def test_less_min_coin_amount(peg_keeper, swap):
    assert not peg_keeper.provide(1, {"from": swap}).return_value
