import pytest

pytestmark = pytest.mark.usefixtures(
    "add_initial_liquidity",
    "provide_token_to_peg_keeper",
    "set_peg_keeper",
    "mint_alice",
    "approve_alice",
)


def test_exchange_peg_to_pegged(
    swap, initial_amounts, alice, balance_change_after_provide
):
    amount = initial_amounts[0] // 2
    recieved = swap.exchange(0, 1, amount, 0,).return_value  # from  # to  # min_dy
    balance_change_after_provide(amount + recieved)


def test_exchange_pegged_to_peg(
    swap, initial_amounts, alice, balance_change_after_withdraw
):
    amount = initial_amounts[1] // 2
    recieved = swap.exchange(1, 0, amount, 0,).return_value  # from  # to  # min_dy
    balance_change_after_withdraw(amount + recieved)
