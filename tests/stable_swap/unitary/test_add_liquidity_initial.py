import brownie
import pytest
from brownie import ETH_ADDRESS

pytestmark = pytest.mark.usefixtures("mint_alice", "approve_alice")


@pytest.mark.parametrize("min_amount", [0, 2 * 10 ** 18])
def test_initial(
    alice, swap, coins, pool_token, min_amount, decimals, n_coins, initial_amounts
):
    amounts = [10 ** i for i in decimals]
    value = "1 ether" if ETH_ADDRESS in coins else 0

    swap.add_liquidity(amounts, min_amount, {"from": alice, "value": value})

    for coin, amount, initial in zip(coins, amounts, initial_amounts):
        if coin == ETH_ADDRESS:
            assert alice.balance() + amount == initial
            assert swap.balance() == amount
        else:
            assert coin.balanceOf(alice) == initial - amount
            assert coin.balanceOf(swap) == amount

    assert pool_token.balanceOf(alice) == n_coins * 10 ** 18
    assert pool_token.totalSupply() == n_coins * 10 ** 18


@pytest.mark.parametrize("idx", range(2))
def test_initial_liquidity_missing_coin(alice, swap, pool_token, idx, decimals):
    amounts = [10 ** i for i in decimals]
    amounts[idx] = 0

    with brownie.reverts():
        swap.add_liquidity(amounts, 0, {"from": alice})
