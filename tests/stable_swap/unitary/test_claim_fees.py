import brownie
import pytest
from brownie import ETH_ADDRESS

MAX_FEE = 5 * 10 ** 9


@pytest.fixture(scope="module", autouse=True)
def setup(alice, add_initial_liquidity, mint_bob, approve_bob, set_fees):
    set_fees(MAX_FEE, MAX_FEE)


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_admin_balances(alice, bob, swap, coins, initial_amounts, sending, receiving):
    for send, recv in [(sending, receiving), (receiving, sending)]:
        value = initial_amounts[send] if coins[send] == ETH_ADDRESS else 0
        swap.exchange(
            send, recv, initial_amounts[send], 0, {"from": bob, "value": value}
        )

    for i in (sending, receiving):
        if coins[i] == ETH_ADDRESS:
            admin_fee = swap.balance() - swap.balances(i)
            assert admin_fee + swap.balances(i) == swap.balance()
        else:
            admin_fee = coins[i].balanceOf(swap) - swap.balances(i)
            assert admin_fee + swap.balances(i) == coins[i].balanceOf(swap)

        assert admin_fee > 0


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_withdraw_one_coin(
    alice, bob, swap, coins, sending, receiving, initial_amounts, get_admin_balances
):

    value = 0
    if coins[sending] == ETH_ADDRESS:
        value = initial_amounts[sending]

    swap.exchange(
        sending, receiving, initial_amounts[sending], 0, {"from": bob, "value": value}
    )

    admin_balances = get_admin_balances()

    assert admin_balances[receiving] > 0
    assert sum(admin_balances) == admin_balances[receiving]

    swap.withdraw_admin_fees({"from": alice})

    if coins[receiving] == ETH_ADDRESS:
        assert alice.balance() == admin_balances[receiving]
        assert swap.balances(receiving) == swap.balance()
    else:
        assert coins[receiving].balanceOf(alice) == admin_balances[receiving]
        assert swap.balances(receiving) == coins[receiving].balanceOf(swap)


def test_withdraw_all_coins(
    alice, bob, swap, coins, initial_amounts, get_admin_balances, n_coins
):
    for send, recv in zip(range(n_coins), list(range(1, n_coins)) + [0]):
        value = initial_amounts[send] if coins[send] == ETH_ADDRESS else 0
        swap.exchange(
            send, recv, initial_amounts[send], 0, {"from": bob, "value": value}
        )

    admin_balances = get_admin_balances()

    swap.withdraw_admin_fees({"from": alice})

    for balance, coin in zip(admin_balances, coins):
        if coin == ETH_ADDRESS:
            assert balance == alice.balance()
        else:
            assert coin.balanceOf(alice) == balance
