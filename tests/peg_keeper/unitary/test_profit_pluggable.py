import brownie
import pytest
from brownie.test import given, strategy

pytestmark = [
    pytest.mark.usefixtures(
        "add_initial_liquidity",
        "provide_token_to_peg_keeper",
        "mint_alice",
        "approve_alice",
    )
]


@pytest.mark.parametrize("coin_to_imbalance", [0, 1])
def test_profit_receiver(
    swap, peg_keeper, bob, receiver, coin_to_imbalance, imbalance_pool
):
    imbalance_pool(coin_to_imbalance)
    peg_keeper.update(receiver, {"from": bob})
    assert swap.balanceOf(bob) == 0
    assert swap.balanceOf(receiver) > 0


def test_unprofitable_peg(
    swap, decimals, pegged, peg_keeper, alice, imbalance_pool, set_fees, chain
):
    # Leave a little of debt
    little = 10 * 10 ** decimals[0]
    imbalance_pool(0, 5 * (peg_keeper.debt() - little))
    peg_keeper.update({"from": alice})

    # Imbalance so it should give all
    able_to_add = pegged.balanceOf(peg_keeper)
    imbalance_pool(1, 5 * able_to_add, add_diff=True)

    set_fees(10 ** 9)

    with brownie.reverts():  # dev: peg was unprofitable
        chain.sleep(15 * 60)
        peg_keeper.update({"from": alice})


@given(share=strategy("int", min_value=0, max_value=10 ** 5))
@pytest.mark.parametrize("coin_to_imbalance", [0, 1])
def test_profit_share(
    peg_keeper, swap, bob, admin, coin_to_imbalance, imbalance_pool, share
):
    peg_keeper.set_new_caller_share(share, {"from": admin})
    imbalance_pool(coin_to_imbalance)

    profit_before = peg_keeper.calc_profit()
    peg_keeper.update({"from": bob})
    profit_after = peg_keeper.calc_profit()

    receiver_profit = profit_after - profit_before
    caller_profit = swap.balanceOf(bob)

    assert caller_profit == (receiver_profit + caller_profit) * share // 10 ** 5
