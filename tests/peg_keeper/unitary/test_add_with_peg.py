def test_add_provide_withdraw(swap, initial_amounts, coins, pegged, bob, wait_for_peg, history):
    debt, available_debt = swap.debt(), swap.available_debt()

    # provide
    amounts = [initial_amount // 2 if coin != pegged else 0 for initial_amount, coin in zip(initial_amounts, coins)]
    swap.add_liquidity(amounts, 0, {"from": bob})
    to_provide = sum(amounts) // 5
    assert swap.debt() == debt + to_provide
    assert swap.available_debt() == available_debt - to_provide
    assert swap.last_change() == history[-1].timestamp
    debt, available_debt, last_change = debt + to_provide, available_debt - to_provide, swap.last_change()

    wait_for_peg()

    # make equal
    amounts = [initial_amount // 2 - to_provide if coin == pegged else 0 for initial_amount, coin in zip(initial_amounts, coins)]
    swap.add_liquidity(amounts, 0, {"from": bob})
    assert swap.debt() == debt
    assert swap.available_debt() == available_debt
    assert swap.last_change() == last_change

    # withdraw
    amounts = [initial_amount // 2 if coin == pegged else 0 for initial_amount, coin in zip(initial_amounts, coins)]
    swap.add_liquidity(amounts, 0, {"from": bob})
    to_withdraw = sum(amounts) // 5
    assert swap.debt() == debt - to_withdraw
    assert swap.available_debt() == available_debt + to_withdraw
    assert swap.last_change() == history[-1].timestamp

    assert swap.balanceOf(swap) > 0, "Did not profit"
