import pytest
from pytest import approx


@pytest.fixture
def _provide_liquidity_and_token(pool, peg, pegged, alice, pool_token, peg_keeper):
    """ Add liquidity to the pool and split received LP tokens between alice and peg_keeper """
    amount = min(peg.balanceOf(alice), pegged.balanceOf(alice))
    assert amount > 0, "Give some coins to alice"

    peg.approve(pool, amount, {"from": alice})
    pegged.approve(pool, amount, {"from": alice})
    pool.add_liquidity([amount, amount], 0, {"from": alice})
    lp_amount = pool_token.balanceOf(alice)
    pool_token.transfer(peg_keeper, lp_amount // 2, {"from": alice})


def _balance_change(pool, peg, pegged, peg_keeper, admin, diff):
    assert peg_keeper.update({"from": admin}).return_value

    assert int(peg.balanceOf(pool)) == approx(pegged.balanceOf(pool) - (diff - diff // 5))
    assert int(pool.balances(0)) == approx(pool.balances(1) - (diff - diff // 5), abs=diff * pool.fee())


def test_remove_liquidity_peg(_provide_liquidity_and_token, pool, pool_token, peg, pegged, alice, peg_keeper, admin):
    amount = pool.remove_liquidity_one_coin(pool_token.balanceOf(alice), 0, 0, {"from": alice}).return_value

    _balance_change(pool, peg, pegged, peg_keeper, admin, amount)
