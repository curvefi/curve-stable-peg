def test_admin_fees(swap, initial_amounts, coins, pegged, alice, bob, wait_for_peg):
    initial_balances = [coin.balanceOf(alice) for coin in coins]
    swap.exchange(0, 1, initial_amounts[0] // 2, 0, {"from": bob})
    swap.exchange(1, 0, initial_amounts[1] // 2, 0, {"from": bob})

    admin_balances = [swap.admin_balances(0), swap.admin_balances(1)]
    swap.withdraw_admin_fees()
    for i in range(2):
        assert coins[i].balanceOf(alice) == initial_balances[i] + admin_balances[i]

    assert swap.debt() > 0
    swap.withdraw_admin_fees(True)

    # Is able to return all debt
    wait_for_peg()
    swap.exchange(1, 0, initial_amounts[1] // 2, 0, {"from": bob})
    assert swap.debt() == 0
