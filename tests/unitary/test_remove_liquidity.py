import pytest
from pytest import approx


@pytest.fixture
def _add_liquidity_and_update(pool, peg, pegged, alice, peg_keeper, admin):
    amount = peg.balanceOf(alice) // 2
    assert amount > 0, "Give some coins to alice"

    peg.approve(pool, amount, {"from": alice})
    pool.add_liquidity([amount, 0], 0, {"from": alice})
    peg_keeper.update({"from": admin})


def test_remove_liquidity_peg_once(_add_liquidity_and_update, pool, pool_token, peg, pegged, alice, peg_keeper, admin):
    amount = pool.calc_withdraw_one_coin(pool_token.balanceOf(alice) // 2, 0)
    pool.remove_liquidity_imbalance([amount, 0], 2 ** 256 - 1, {"from": alice})
    assert peg_keeper.update({"from": admin}).return_value

    # TODO: fix _add_liquidity_and_update
    # assert int(peg.balanceOf(pool)) == approx(pegged.balanceOf(pool) - 4 * amount / 5)
    # assert int(pool.balances(0)) == approx(pool.balances(1) - 4 * amount / 5, abs=amount * pool.fee())
