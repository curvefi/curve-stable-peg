import pytest
from pytest import approx


pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "provide_token_to_peg_keeper")


def _balance_change_withdraw(pool, peg, pegged, peg_keeper, admin, diff):
    assert peg_keeper.update({"from": admin}).return_value

    assert int(peg.balanceOf(pool)) == approx(pegged.balanceOf(pool) - (diff - diff // 5))
    assert int(pool.balances(0)) == approx(pool.balances(1) - (diff - diff // 5), abs=diff * pool.fee() / 10 ** 10)


def _balance_change_provide(pool, peg, pegged, peg_keeper, admin, diff):
    assert peg_keeper.update({"from": admin}).return_value

    assert int(peg.balanceOf(pool)) == approx(pegged.balanceOf(pool) + (diff - diff // 5))
    assert int(pool.balances(0)) == approx(pool.balances(1) + (diff - diff // 5), abs=diff * pool.fee() / 10 ** 10)


def _balance_do_not_change(pool, peg, pegged, peg_keeper, admin):
    balances = [pool.balances(0), pool.balances(1)]
    real_balances = [peg.balanceOf(pool), pegged.balanceOf(pool)]

    assert not peg_keeper.update({"from": admin}).return_value

    assert balances == [pool.balances(0), pool.balances(1)]
    assert real_balances == [peg.balanceOf(pool), pegged.balanceOf(pool)]


def test_remove_liquidity_peg(swap, pool_token, peg, pegged, alice, peg_keeper, admin):
    """ Remove [x, 0] """
    amount = swap.remove_liquidity_one_coin(
        pool_token.balanceOf(alice),
        0,  # coin
        0,  # min_amount
        {"from": alice},
    ).return_value
    _balance_change_withdraw(swap, peg, pegged, peg_keeper, admin, amount)


def test_remove_liquidity_pegged(swap, pool_token, peg, pegged, alice, peg_keeper, admin):
    """ Remove [0, x] """
    amount = swap.remove_liquidity_one_coin(
        pool_token.balanceOf(alice),
        1,  # coin
        0,  # min_amount
        {"from": alice},
    ).return_value
    _balance_change_provide(swap, peg, pegged, peg_keeper, admin, amount)


def test_remove_liquidity_equal(swap, pool_token, peg, pegged, alice, peg_keeper, admin):
    """ Remove [x, x] """
    swap.remove_liquidity(pool_token.balanceOf(alice), [0, 0], {"from": alice})
    _balance_do_not_change(swap, peg, pegged, peg_keeper, admin)


def test_remove_liquidity_more_peg(swap, pool_token, peg, pegged, alice, peg_keeper, admin):
    """ Remove [2 * x, x] """
    token_balance = pool_token.balanceOf(alice)
    # Balances in the pool are equal
    amount = swap.calc_withdraw_one_coin(2 * token_balance // 3, 0, {"from": alice})
    swap.remove_liquidity_imbalance([amount, amount // 2], token_balance, {"from": alice})

    diff = amount - amount // 2
    _balance_change_withdraw(swap, peg, pegged, peg_keeper, admin, diff)


def test_remove_liquidity_more_pegged(swap, pool_token, peg, pegged, alice, peg_keeper, admin):
    """ Remove [x, 2 * x] """
    token_balance = pool_token.balanceOf(alice)
    # Balances in the pool are equal
    amount = swap.calc_withdraw_one_coin(2 * token_balance // 3, 1, {"from": alice})
    swap.remove_liquidity_imbalance([amount // 2, amount], token_balance, {"from": alice})

    diff = amount - amount // 2
    _balance_change_provide(swap, peg, pegged, peg_keeper, admin, diff)
