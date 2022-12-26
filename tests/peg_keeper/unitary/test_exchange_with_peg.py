def test_exchange_provide_withdraw(swap, initial_amounts, coins, pegged, bob, wait_for_peg, history):
    balances, debt, available_debt = [swap.balances(0), swap.balances(1)], swap.debt(), swap.available_debt()

    dx = initial_amounts[0] // 10
    min_amount = int(swap.get_dy(0, 1, dx))
    swap.exchange(0, 1, dx, min_amount, {"from": bob})
    to_provide = (dx + min_amount) // 5
    assert swap.balances(0) == balances[0] + dx
    assert swap.balances(1) == balances[1] - min_amount + to_provide
    assert swap.debt() == debt + to_provide
    assert swap.available_debt() == available_debt - to_provide
    assert swap.last_change() == history[-1].timestamp

    wait_for_peg()
    balances, debt, available_debt = [swap.balances(0), swap.balances(1)], swap.debt(), swap.available_debt()
    dx = initial_amounts[1] // 10
    min_amount = int(swap.get_dy(1, 0, dx))
    swap.exchange(1, 0, dx, min_amount, {"from": bob})
    to_withdraw = (dx + min_amount - to_provide * 4) // 5
    assert swap.balances(0) == balances[0] - min_amount
    assert swap.balances(1) == balances[1] + dx - to_withdraw
    assert swap.debt() == debt - to_withdraw
    assert swap.available_debt() == available_debt + to_withdraw
    assert swap.last_change() == history[-1].timestamp
