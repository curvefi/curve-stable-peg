from brownie import chain


def test_update_delay(peg_keeper, admin, pool, peg, alice):
    action_delay = peg_keeper.action_delay()
    if action_delay:
        amount = peg.balanceOf(alice) // 2
        assert amount > 0, "Give some coins to alice"

        peg.approve(pool, amount, {"from": alice})
        pool.add_liquidity([amount, 0], 0, {"from": alice})
        assert peg_keeper.update({"from": admin})

        chain.sleep(action_delay)

        assert peg_keeper.update({"from": admin})


def test_update_no_delay(peg_keeper, admin, pool, peg, alice):
    action_delay = peg_keeper.action_delay()
    if action_delay:
        amount = peg.balanceOf(alice) // 2
        assert amount > 0, "Give some coins to alice"

        peg.approve(pool, amount, {"from": alice})
        pool.add_liquidity([amount, 0], 0, {"from": alice})
        assert peg_keeper.update({"from": admin})

        chain.sleep(action_delay - 1)

        assert not peg_keeper.update({"from": admin})
