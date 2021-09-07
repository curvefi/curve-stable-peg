import pytest

from pytest import approx
from brownie import chain


pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "mint_alice", "set_peg_keeper")


def _balance_change(pool, peg, pegged, diff):
    assert int(peg.balanceOf(pool)) == approx(pegged.balanceOf(pool) + 4 * diff / 5)
    assert int(pool.balances(0)) == approx(pool.balances(1) + 4 * diff / 5, abs=diff * pool.fee() / 10 ** 10)


def _balance_do_not_change(pool, peg, pegged, peg_keeper, admin):
    balances = [pool.balances(0), pool.balances(1)]
    real_balances = [peg.balanceOf(pool), pegged.balanceOf(pool)]

    assert not peg_keeper.update({"from": admin}).return_value

    assert balances == [pool.balances(0), pool.balances(1)]
    assert real_balances == [peg.balanceOf(pool), pegged.balanceOf(pool)]


def test_add_liquidity_peg(swap, peg, pegged, alice, peg_keeper, admin):
    """ Add [x, 0] """
    amount = peg.balanceOf(alice)
    peg.approve(swap, amount, {"from": alice})
    swap.add_liquidity([amount, 0], 0, {"from": alice})
    _balance_change(swap, peg, pegged, amount)


def test_add_liquidity_pegged(swap, peg, pegged, alice, peg_keeper, admin):
    """ Add [0, x] """
    amount = pegged.balanceOf(alice)

    pegged.approve(swap, amount, {"from": alice})
    swap.add_liquidity([0, amount], 0, {"from": alice})
    _balance_do_not_change(swap, peg, pegged, peg_keeper, admin)


def test_add_liquidity_equal(swap, peg, pegged, alice, peg_keeper, admin):
    """ Add [x, x] """
    amount = min(peg.balanceOf(alice), pegged.balanceOf(alice))

    peg.approve(swap, amount, {"from": alice})
    pegged.approve(swap, amount, {"from": alice})
    swap.add_liquidity([amount, amount], 0, {"from": alice})
    _balance_do_not_change(swap, peg, pegged, peg_keeper, admin)


def test_add_liquidity_more_peg(swap, peg, pegged, alice, peg_keeper, admin):
    """ Add [2 * x, x] """
    amount = min(peg.balanceOf(alice), pegged.balanceOf(alice))
    amounts = [amount, amount // 2]

    peg.approve(swap, amounts[0], {"from": alice})
    pegged.approve(swap, amounts[1], {"from": alice})
    swap.add_liquidity(amounts, 0, {"from": alice})

    diff = amounts[0] - amounts[1]
    _balance_change(swap, peg, pegged, diff)


def test_add_liquidity_more_pegged(swap, peg, pegged, alice, peg_keeper, admin):
    """ Add [x, 2 * x] """
    amount = min(peg.balanceOf(alice), pegged.balanceOf(alice))
    amounts = [amount // 2, amount]

    peg.approve(swap, amounts[0], {"from": alice})
    pegged.approve(swap, amounts[1], {"from": alice})
    swap.add_liquidity(amounts, 0, {"from": alice})

    _balance_do_not_change(swap, peg, pegged, peg_keeper, admin)


def test_add_liquidity_many_times(swap, peg, pegged, alice, peg_keeper, admin):
    times = 10
    action_delay = peg_keeper.action_delay()
    amount = peg.balanceOf(alice) // times
    peg.approve(swap, amount * times, {"from": alice})
    for _ in range(times):
        swap.add_liquidity([amount, 0], 0, {"from": alice})

        diff = swap.balances(0) - swap.balances(1)
        _balance_change(swap, peg, pegged, diff)

        chain.sleep(action_delay)
