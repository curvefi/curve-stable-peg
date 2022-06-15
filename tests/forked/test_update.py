import pytest
from brownie import chain


def _balance_pool(swap, coins, alice):
    diff = swap.balances(0) - swap.balances(1)
    i = 0 if diff < 0 else 1
    diff = abs(diff)
    coins[i]._mint_for_testing(alice, diff, {"from": alice})
    coins[i].approve(swap, diff, {"from": alice})
    amounts = [0, 0]
    amounts[i] = diff
    swap.add_liquidity(amounts, 0, {"from": alice})


def test_provide_and_withdraw(swap, coins, peg, pegged, peg_keeper, alice):
    pegged._mint_for_testing(peg_keeper, swap.balances(0), {"from": alice})

    _balance_pool(swap, coins, alice)
    add_amount = swap.balances(1) // 3
    peg._mint_for_testing(alice, add_amount, {"from": alice})
    peg.approve(swap, add_amount, {"from": alice})
    swap.add_liquidity([0, add_amount], 0, {"from": alice})

    assert peg_keeper.update({"from": alice}).return_value
    assert peg_keeper.debt() > 0
    assert abs(swap.balances(0) - swap.balances(1)) == pytest.approx(
        add_amount - add_amount // 5, rel=1e-4
    )

    _balance_pool(swap, coins, alice)
    chain.sleep(15 * 3600)

    remove_amount = swap.balances(0) // 3
    pegged._mint_for_testing(alice, remove_amount, {"from": alice})
    pegged.approve(swap, remove_amount, {"from": alice})
    swap.add_liquidity([remove_amount, 0], 0, {"from": alice})

    # remove_amount > add_amount => withdraws the whole debt
    assert peg_keeper.update({"from": alice}).return_value
    assert peg_keeper.debt() == 0
    assert abs(swap.balances(0) - swap.balances(1)) == pytest.approx(
        remove_amount - add_amount // 5, rel=1e-4
    )
