import pytest

from brownie import chain
from flaky import flaky


pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "mint_bob")


def _prepare_for_provide(pool, peg, bob) -> int:
    amount = peg.balanceOf(bob)

    peg.approve(pool, amount, {"from": bob})
    pool.add_liquidity([amount, 0], 0, {"from": bob})

    return amount


def _prepare_for_withdraw(pool, pool_token, peg, pegged, bob, peg_keeper) -> int:
    amount = min(peg.balanceOf(bob), pegged.balanceOf(bob))

    amounts = [amount // 2, amount]
    peg.approve(pool, amounts[0], {"from": bob})
    pegged.approve(pool, amounts[1], {"from": bob})
    pool.add_liquidity(amounts, 0, {"from": bob})

    token_balance = pool_token.balanceOf(bob)
    pool_token.transfer(peg_keeper, token_balance // 2, {"from": bob})

    return amount // 2


def _sleep_delay(peg_keeper):
    chain.mine(
        timestamp=peg_keeper.last_change() + peg_keeper.action_delay()
    )


def _sleep_less_delay(peg_keeper):
    chain.mine(
        timestamp=peg_keeper.last_change() + peg_keeper.action_delay() - 1
    )


def test_update_delay(peg_keeper, admin, swap, peg, bob):
    if peg_keeper.action_delay():
        _prepare_for_provide(swap, peg, bob)

        assert peg_keeper.update({"from": admin}).return_value
        _sleep_delay(peg_keeper)
        assert peg_keeper.update({"from": admin}).return_value


@flaky
def test_update_no_delay(peg_keeper, admin, swap, peg, bob):
    if peg_keeper.action_delay():
        _prepare_for_provide(swap, peg, bob)

        assert peg_keeper.update({"from": admin}).return_value
        _sleep_less_delay(peg_keeper)
        assert not peg_keeper.update({"from": admin}).return_value


def test_provide_delay(peg_keeper, swap, peg, bob):
    if peg_keeper.action_delay():
        amount = _prepare_for_provide(swap, peg, bob)

        assert peg_keeper.provide(amount // 3, {"from": swap}).return_value
        _sleep_delay(peg_keeper)
        assert peg_keeper.provide(amount // 3, {"from": swap}).return_value


@flaky
def test_provide_no_delay(peg_keeper, swap, peg, bob):
    if peg_keeper.action_delay():
        amount = _prepare_for_provide(swap, peg, bob)

        assert peg_keeper.provide(amount // 3, {"from": swap}).return_value
        _sleep_less_delay(peg_keeper)
        assert not peg_keeper.provide(amount // 3, {"from": swap}).return_value


def test_withdraw_delay(peg_keeper, swap, pool_token, peg, pegged, bob):
    if peg_keeper.action_delay():
        amount = _prepare_for_withdraw(swap, pool_token, peg, pegged, bob, peg_keeper)

        assert peg_keeper.withdraw(amount // 3, {"from": swap}).return_value
        _sleep_delay(peg_keeper)
        assert peg_keeper.withdraw(amount // 3, {"from": swap}).return_value


@flaky
def test_withdraw_no_delay(peg_keeper, swap, pool_token, peg, pegged, bob):
    if peg_keeper.action_delay():
        amount = _prepare_for_withdraw(swap, pool_token, peg, pegged, bob, peg_keeper)

        assert peg_keeper.withdraw(amount // 3, {"from": swap}).return_value
        _sleep_less_delay(peg_keeper)
        assert not peg_keeper.withdraw(amount // 3, {"from": swap}).return_value
