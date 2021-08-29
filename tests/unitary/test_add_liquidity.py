from contextlib import contextmanager
from pytest import approx
from brownie import chain


def test_add_liquidity_once(pool, peg, pegged, alice, peg_keeper, admin):
    amount = peg.balanceOf(alice)
    assert amount > 0, "Give some coins to alice"
    peg.approve(pool, amount, {"from": alice})
    pool.add_liquidity([amount, 0], 0, {"from": alice})
    assert peg_keeper.update({"from": admin}).return_value

    assert int(peg.balanceOf(pool)) == approx(pegged.balanceOf(pool) + 4 * amount / 5)
    assert int(pool.balances(0)) == approx(pool.balances(1) + 4 * amount / 5, abs=amount * pool.fee())


def test_add_liquidity_many_times(pool, peg, pegged, alice, peg_keeper, admin):
    times = 10
    action_delay = peg_keeper.action_delay()
    amount = peg.balanceOf(alice) // times
    assert amount > 0, "Give some coins to alice"
    peg.approve(pool, amount * times, {"from": alice})
    for _ in range(times):
        pool.add_liquidity([amount, 0], 0, {"from": alice})
        diff = pool.balances(0) - pool.balances(1)
        assert peg_keeper.update({"from": admin}).return_value

        assert int(peg.balanceOf(pool)) == approx(pegged.balanceOf(pool) + 4 * diff / 5)
        assert int(pool.balances(0)) == approx(pool.balances(1) + 4 * diff / 5, abs=amount * pool.fee())
        chain.sleep(action_delay)


@contextmanager
def _balance_do_not_change(pool, peg, pegged):
    balances = [pool.balances(0), pool.balances(1)]
    real_balances = [peg.balanceOf(pool), pegged.balanceOf(pool)]

    yield

    assert balances == [pool.balances(0), pool.balances(1)]
    assert real_balances == [peg.balanceOf(pool), pegged.balanceOf(pool)]


def test_add_liquidity_equal(pool, peg, pegged, alice, peg_keeper, admin):
    amount = min(peg.balanceOf(alice), pegged.balanceOf(alice))
    assert amount > 0, "Give some coins to alice"

    peg.approve(pool, amount, {"from": alice})
    pegged.approve(pool, amount, {"from": alice})
    pool.add_liquidity([amount, amount], 0, {"from": alice})
    with _balance_do_not_change(pool, peg, pegged):
        assert not peg_keeper.update({"from": admin}).return_value


def test_add_liquidity_pegged(pool, peg, pegged, alice, peg_keeper, admin):
    amount = pegged.balanceOf(alice)
    assert amount > 0, "Give some coins to alice"

    pegged.approve(pool, amount, {"from": alice})
    pool.add_liquidity([0, amount], 0, {"from": alice})
    with _balance_do_not_change(pool, peg, pegged):
        assert not peg_keeper.update({"from": admin}).return_value


def test_add_liquidity_more_pegged(pool, peg, pegged, alice, peg_keeper, admin):
    amount = min(peg.balanceOf(alice), pegged.balanceOf(alice))
    assert amount > 0, "Give some coins to alice"
    amounts = [amount // 2, amount]

    peg.approve(pool, amounts[0], {"from": alice})
    pegged.approve(pool, amounts[1], {"from": alice})
    pool.add_liquidity(amounts, 0, {"from": alice})
    with _balance_do_not_change(pool, peg, pegged):
        assert not peg_keeper.update({"from": admin}).return_value

