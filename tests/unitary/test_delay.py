from brownie import chain


def _prepare_for_provide(pool, peg, alice) -> int:
    amount = peg.balanceOf(alice)
    assert amount > 0, "Give some coins to alice"

    peg.approve(pool, amount, {"from": alice})
    pool.add_liquidity([amount, 0], 0, {"from": alice})

    return amount


def _prepare_for_withdraw(pool, pool_token, peg, pegged, alice, peg_keeper) -> int:
    amount = min(peg.balanceOf(alice), pegged.balanceOf(alice))
    assert amount > 0, "Give some coins to alice"

    amounts = [amount // 2, amount]
    peg.approve(pool, amounts[0], {"from": alice})
    pegged.approve(pool, amounts[1], {"from": alice})
    pool.add_liquidity(amounts, 0, {"from": alice})

    token_balance = pool_token.balanceOf(alice)
    pool_token.transfer(peg_keeper, token_balance // 3, {"from": alice})

    return amount // 2


def _sleep_delay(peg_keeper):
    chain.mine(
        timestamp=peg_keeper.last_change() + peg_keeper.action_delay()
    )


def _sleep_less_delay(peg_keeper):
    # -1 may not be enough, so probably need to run a couple of times, so at least 1 time passes
    chain.mine(
        timestamp=peg_keeper.last_change() + peg_keeper.action_delay() - 1
    )


def test_update_delay(peg_keeper, admin, pool, peg, alice):
    if peg_keeper.action_delay():
        _prepare_for_provide(pool, peg, alice)

        assert peg_keeper.update({"from": admin}).return_value
        _sleep_delay(peg_keeper)
        assert peg_keeper.update({"from": admin}).return_value


def test_update_no_delay(peg_keeper, admin, pool, peg, alice):
    if peg_keeper.action_delay():
        _prepare_for_provide(pool, peg, alice)

        assert peg_keeper.update({"from": admin}).return_value
        _sleep_less_delay(peg_keeper)
        assert not peg_keeper.update({"from": admin}).return_value


def test_provide_delay(peg_keeper, pool, peg, alice):
    if peg_keeper.action_delay():
        amount = _prepare_for_provide(pool, peg, alice)

        assert peg_keeper.provide(amount // 5, {"from": pool}).return_value
        _sleep_delay(peg_keeper)
        assert peg_keeper.provide((amount - amount // 5) // 5, {"from": pool}).return_value


def test_provide_no_delay(peg_keeper, pool, peg, alice):
    if peg_keeper.action_delay():
        amount = _prepare_for_provide(pool, peg, alice)

        assert peg_keeper.provide(amount // 5, {"from": pool}).return_value
        _sleep_less_delay(peg_keeper)
        assert not peg_keeper.provide((amount - amount // 5) // 5, {"from": pool}).return_value


def test_withdraw_delay(peg_keeper, pool, pool_token, peg, pegged, alice):
    if peg_keeper.action_delay():
        amount = _prepare_for_withdraw(pool, pool_token, peg, pegged, alice, peg_keeper)

        assert peg_keeper.withdraw(amount // 5, {"from": pool}).return_value
        _sleep_delay(peg_keeper)
        assert peg_keeper.withdraw((amount - amount // 5) // 5, {"from": pool}).return_value


def test_withdraw_no_delay(peg_keeper, pool, pool_token, peg, pegged, alice):
    if peg_keeper.action_delay():
        amount = _prepare_for_withdraw(pool, pool_token, peg, pegged, alice, peg_keeper)

        assert peg_keeper.withdraw(amount // 5, {"from": pool}).return_value
        _sleep_less_delay(peg_keeper)
        assert not peg_keeper.withdraw((amount - amount // 5) // 5, {"from": pool}).return_value
