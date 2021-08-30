from pytest import approx
from brownie import chain


def _balance_change(pool, peg, pegged, peg_keeper, admin, diff):
    assert peg_keeper.update({"from": admin}).return_value

    assert int(peg.balanceOf(pool)) == approx(pegged.balanceOf(pool) + 4 * diff / 5)
    assert int(pool.balances(0)) == approx(pool.balances(1) + 4 * diff / 5, abs=diff * pool.fee())


def _balance_do_not_change(pool, peg, pegged, peg_keeper, admin):
    balances = [pool.balances(0), pool.balances(1)]
    real_balances = [peg.balanceOf(pool), pegged.balanceOf(pool)]

    assert not peg_keeper.update({"from": admin}).return_value

    assert balances == [pool.balances(0), pool.balances(1)]
    assert real_balances == [peg.balanceOf(pool), pegged.balanceOf(pool)]


def test_add_liquidity_peg(pool, peg, pegged, alice, peg_keeper, admin):
    """ Add [x, 0] """
    amount = peg.balanceOf(alice)
    assert amount > 0, "Give some coins to alice"
    peg.approve(pool, amount, {"from": alice})
    pool.add_liquidity([amount, 0], 0, {"from": alice})
    _balance_change(pool, peg, pegged, peg_keeper, admin, amount)


def test_add_liquidity_pegged(pool, peg, pegged, alice, peg_keeper, admin):
    """ Add [0, x] """
    amount = pegged.balanceOf(alice)
    assert amount > 0, "Give some coins to alice"

    pegged.approve(pool, amount, {"from": alice})
    pool.add_liquidity([0, amount], 0, {"from": alice})
    _balance_do_not_change(pool, peg, pegged, peg_keeper, admin)


def test_add_liquidity_equal(pool, peg, pegged, alice, peg_keeper, admin):
    """ Add [x, x] """
    amount = min(peg.balanceOf(alice), pegged.balanceOf(alice))
    assert amount > 0, "Give some coins to alice"

    peg.approve(pool, amount, {"from": alice})
    pegged.approve(pool, amount, {"from": alice})
    pool.add_liquidity([amount, amount], 0, {"from": alice})
    _balance_do_not_change(pool, peg, pegged, peg_keeper, admin)


def test_add_liquidity_more_peg(pool, peg, pegged, alice, peg_keeper, admin):
    """ Add [2 * x, x] """
    amount = min(peg.balanceOf(alice), pegged.balanceOf(alice))
    assert amount > 0, "Give some coins to alice"
    amounts = [amount, amount // 2]

    peg.approve(pool, amounts[0], {"from": alice})
    pegged.approve(pool, amounts[1], {"from": alice})
    pool.add_liquidity(amounts, 0, {"from": alice})

    diff = amounts[0] - amounts[1]
    _balance_change(pool, peg, pegged, peg_keeper, admin, diff)


def test_add_liquidity_more_pegged(pool, peg, pegged, alice, peg_keeper, admin):
    """ Add [x, 2 * x] """
    amount = min(peg.balanceOf(alice), pegged.balanceOf(alice))
    assert amount > 0, "Give some coins to alice"
    amounts = [amount // 2, amount]

    peg.approve(pool, amounts[0], {"from": alice})
    pegged.approve(pool, amounts[1], {"from": alice})
    pool.add_liquidity(amounts, 0, {"from": alice})

    _balance_do_not_change(pool, peg, pegged, peg_keeper, admin)


def test_add_liquidity_many_times(pool, peg, pegged, alice, peg_keeper, admin):
    times = 10
    action_delay = peg_keeper.action_delay()
    amount = peg.balanceOf(alice) // times
    assert amount > 0, "Give some coins to alice"
    peg.approve(pool, amount * times, {"from": alice})
    for _ in range(times):
        pool.add_liquidity([amount, 0], 0, {"from": alice})

        diff = pool.balances(0) - pool.balances(1)
        _balance_change(pool, peg, pegged, peg_keeper, admin, diff)

        chain.sleep(action_delay)
