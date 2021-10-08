import pytest

pytestmark = [
    pytest.mark.usefixtures(
        "add_initial_liquidity",
        "provide_token_to_peg_keeper",
        "mint_alice",
        "approve_alice",
    ),
    pytest.mark.pluggable,
]


def _imbalance_pool(i, swap, initial_amounts, alice):
    amount = initial_amounts[i] // 3
    swap.exchange(i, 1 - i, amount, 0, {"from": alice})


@pytest.mark.parametrize("coin_to_imbalance", [0, 1])
def test_profit_receiver(
    swap, initial_amounts, peg_keeper, alice, bob, receiver, coin_to_imbalance
):
    _imbalance_pool(coin_to_imbalance, swap, initial_amounts, alice)
    peg_keeper.update(receiver, {"from": bob})
    assert swap.balanceOf(bob) == 0
    assert swap.balanceOf(receiver) > 0
