import pytest
from brownie.test import given, strategy

pytestmark = [
    pytest.mark.usefixtures(
        "add_initial_liquidity",
        "provide_token_to_peg_keeper",
        "mint_alice",
    ),
    pytest.mark.template,
]


@pytest.fixture(scope="module")
def make_profit(swap, peg, pegged, initial_amounts, alice, set_fees):
    def _inner(amount):
        """Amount to add to balances."""
        set_fees(1 * 10 ** 9, 0)
        exchange_amount = amount * 5

        peg.approve(swap, exchange_amount, {"from": alice})
        swap.exchange(0, 1, exchange_amount, 0, {"from": alice})

        pegged.approve(swap, exchange_amount, {"from": alice})
        swap.exchange(1, 0, exchange_amount, 0, {"from": alice})

    return _inner


def test_initial_debt(peg_keeper, initial_amounts):
    assert peg_keeper.debt() == initial_amounts[0]


def test_calc_initial_profit(peg_keeper, swap):
    """Peg Keeper always generate profit, including first mint."""
    debt = peg_keeper.debt()
    assert debt / swap.get_virtual_price() < swap.balanceOf(peg_keeper)
    aim_profit = swap.balanceOf(peg_keeper) - debt * 10 ** 18 / swap.get_virtual_price()
    assert aim_profit > peg_keeper.calc_profit() > 0


@given(donate_fee=strategy("int", min_value=1, max_value=10 ** 20))
def test_calc_profit(peg_keeper, swap, make_profit, donate_fee):
    debt = peg_keeper.debt()

    make_profit(donate_fee)

    profit = peg_keeper.calc_profit()
    virtual_price = swap.get_virtual_price()
    aim_profit = swap.balanceOf(peg_keeper) - debt * 10 ** 18 // virtual_price
    assert aim_profit >= profit  # Never take more than real profit
    assert aim_profit - profit < 1e18  # Error less than 1 LP Token


@given(donate_fee=strategy("int", min_value=1, max_value=10 ** 20))
def test_withdraw_profit(
    peg_keeper,
    swap,
    pegged,
    initial_amounts,
    make_profit,
    admin,
    receiver,
    alice,
    peg_keeper_updater,
    balance_change_after_withdraw,
    donate_fee,
):
    """Withdraw profit and update for the whole debt."""
    make_profit(donate_fee)

    profit = peg_keeper.calc_profit()
    returned = peg_keeper.withdraw_profit({"from": admin}).return_value
    assert profit == returned
    assert profit == swap.balanceOf(receiver)

    amount = 5 * initial_amounts[0] + swap.balances(1) - swap.balances(0)
    pegged._mint_for_testing(alice, amount, {"from": alice})
    pegged.approve(swap, amount, {"from": alice})
    swap.add_liquidity([amount, 0], 0, {"from": alice})

    swap.set_peg_keeper(peg_keeper, {"from": alice})
    assert peg_keeper.update({"from": peg_keeper_updater}).return_value
    balance_change_after_withdraw(5 * initial_amounts[0])


def test_0_after_withdraw(peg_keeper, admin):
    peg_keeper.withdraw_profit({"from": admin})
    assert peg_keeper.calc_profit() == 0


def test_withdraw_profit_access(peg_keeper, alice, set_peg_keeper):
    peg_keeper.withdraw_profit({"from": alice})


def test_event(peg_keeper):
    profit = peg_keeper.calc_profit()
    tx = peg_keeper.withdraw_profit()
    event = tx.events["Profit"]
    assert event["lp_amount"] == profit
