import pytest

pytestmark = [
    pytest.mark.usefixtures(
        "add_initial_liquidity",
        "provide_token_to_peg_keeper",
        "set_peg_keeper",
        "mint_alice",
        "approve_alice",
    ),
    pytest.mark.template,
]


def test_remove_liquidity_peg(swap, alice, balance_change_after_withdraw):
    """Remove [x, 0]"""
    amount = swap.remove_liquidity_one_coin(
        swap.balanceOf(alice),
        0,  # coin
        0,  # min_amount
        {"from": alice},
    ).return_value
    balance_change_after_withdraw(amount)


def test_remove_liquidity_pegged(swap, alice, balance_change_after_provide):
    """Remove [0, x]"""
    amount = swap.remove_liquidity_one_coin(
        swap.balanceOf(alice),
        1,  # coin
        0,  # min_amount
        {"from": alice},
    ).return_value
    balance_change_after_provide(amount)


def test_remove_liquidity_equal(swap, peg, pegged, alice, peg_keeper, admin):
    """Remove [x, x]"""
    balances = [swap.balances(0), swap.balances(1)]
    real_balances = [peg.balanceOf(swap), pegged.balanceOf(swap)]

    amounts = swap.remove_liquidity(
        swap.balanceOf(alice), [0, 0], {"from": alice}
    ).return_value

    assert balances == [swap.balances(0) + amounts[0], swap.balances(1) + amounts[1]]
    assert real_balances == [
        peg.balanceOf(swap) + amounts[0],
        pegged.balanceOf(swap) + amounts[1],
    ]


def test_remove_liquidity_more_peg(
    swap, peg, pegged, alice, peg_keeper, balance_change_after_withdraw
):
    """Remove [2 * x, x]"""
    token_balance = swap.balanceOf(alice)
    # Balances in the pool are equal
    amount = swap.calc_withdraw_one_coin(2 * token_balance // 3, 0, {"from": alice})
    swap.remove_liquidity_imbalance(
        [amount, amount // 2], token_balance, {"from": alice}
    )

    diff = amount - amount // 2
    balance_change_after_withdraw(diff)


def test_remove_liquidity_more_pegged(swap, alice, balance_change_after_provide):
    """Remove [x, 2 * x]"""
    token_balance = swap.balanceOf(alice)
    # Balances in the pool are equal
    amount = swap.calc_withdraw_one_coin(2 * token_balance // 3, 1, {"from": alice})
    swap.remove_liquidity_imbalance(
        [amount // 2, amount], token_balance, {"from": alice}
    )

    diff = amount - amount // 2
    balance_change_after_provide(diff)


def test_remove_liquidity_after_kill(alice, swap, n_coins):
    swap.kill_me({"from": alice})
    swap.remove_liquidity(swap.balanceOf(alice), [0] * n_coins, {"from": alice})
