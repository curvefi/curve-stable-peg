import pytest

pytestmark = pytest.mark.usefixtures(
    "add_initial_liquidity", "set_peg_keeper", "mint_alice", "approve_alice",
)


def _balance_do_not_change(pool, peg, pegged, amounts, alice):
    balances = [pool.balances(0), pool.balances(1)]
    real_balances = [peg.balanceOf(pool), pegged.balanceOf(pool)]

    pool.add_liquidity(amounts, 0, {"from": alice})

    assert balances == [pool.balances(0) - amounts[0], pool.balances(1) - amounts[1]]
    assert real_balances == [
        peg.balanceOf(pool) - amounts[0],
        pegged.balanceOf(pool) - amounts[1],
    ]


def test_add_liquidity_peg(swap, peg, alice, balance_change_after_provide):
    """ Add [x, 0] """
    amount = peg.balanceOf(alice)
    swap.add_liquidity([amount, 0], 0, {"from": alice})
    balance_change_after_provide(amount)


def test_add_liquidity_pegged(swap, peg, pegged, alice):
    """ Add [0, x] """
    amount = pegged.balanceOf(alice)
    _balance_do_not_change(swap, peg, pegged, [0, amount], alice)


def test_add_liquidity_equal(swap, peg, pegged, alice, peg_keeper, admin):
    """ Add [x, x] """
    amount = min(peg.balanceOf(alice), pegged.balanceOf(alice))
    _balance_do_not_change(swap, peg, pegged, [amount, amount], alice)


def test_add_liquidity_more_peg(swap, peg, pegged, alice, balance_change_after_provide):
    """ Add [2 * x, x] """
    amount = min(peg.balanceOf(alice), pegged.balanceOf(alice))
    amounts = [amount, amount // 2]

    swap.add_liquidity(amounts, 0, {"from": alice})

    diff = amounts[0] - amounts[1]
    balance_change_after_provide(diff)


def test_add_liquidity_more_pegged(swap, peg, pegged, alice, peg_keeper, admin):
    """ Add [x, 2 * x] """
    amount = min(peg.balanceOf(alice), pegged.balanceOf(alice))
    _balance_do_not_change(swap, peg, pegged, [amount // 2, amount], alice)
