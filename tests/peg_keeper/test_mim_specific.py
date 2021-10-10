import pytest

pytestmark = pytest.mark.usefixtures(
    "add_initial_liquidity",
    "mint_alice",
    "approve_alice",
)


def test_provide_no_balance(
    swap,
    peg,
    pegged,
    alice,
    peg_keeper,
    peg_keeper_updater,
    set_peg_keeper_func,
):
    swap.add_liquidity([0, 10 ** 24], 0, {"from": alice})
    balances = [swap.balances(0), swap.balances(1)]
    real_balances = [pegged.balanceOf(swap), peg.balanceOf(swap)]

    set_peg_keeper_func()
    assert not peg_keeper.update({"from": peg_keeper_updater}).return_value

    new_balances = [swap.balances(0), swap.balances(1)]
    new_real_balances = [pegged.balanceOf(swap), peg.balanceOf(swap)]
    assert new_balances[0] == balances[0]
    assert new_balances[1] == balances[1]

    assert new_real_balances[0] == real_balances[0]
    assert new_real_balances[1] == real_balances[1]


def test_provide_little_amount(
    swap,
    peg,
    pegged,
    alice,
    peg_keeper,
    peg_keeper_updater,
    set_peg_keeper_func,
    little_amount,
    provide_little_amount_of_pegged_to_peg_keeper,
):
    swap.add_liquidity([0, 10 ** 24], 0, {"from": alice})

    balances = [swap.balances(0), swap.balances(1)]
    real_balances = [pegged.balanceOf(swap), peg.balanceOf(swap)]

    set_peg_keeper_func()
    assert peg_keeper.update({"from": peg_keeper_updater}).return_value
    provided_amount = little_amount * 10 ** 18

    new_balances = [swap.balances(0), swap.balances(1)]
    new_real_balances = [pegged.balanceOf(swap), peg.balanceOf(swap)]
    assert new_balances[0] == balances[0] + provided_amount
    assert new_balances[1] == balances[1]

    assert new_real_balances[0] == real_balances[0] + provided_amount
    assert new_real_balances[1] == real_balances[1]


def test_withdraw_pegged_no_balance(
    pegged,
    alice,
    peg_keeper,
    admin,
    base_amount,
):
    alice_pegged_balance = pegged.balanceOf(alice)

    assert not peg_keeper.withdraw_pegged(
        base_amount * 10 ** 18, alice, {"from": admin}
    ).return_value

    alice_new_pegged_balance = pegged.balanceOf(alice)
    assert alice_pegged_balance == alice_new_pegged_balance


def test_withdraw_pegged_exceed(
    pegged,
    alice,
    peg_keeper,
    admin,
    little_amount,
    provide_little_amount_of_pegged_to_peg_keeper,
):
    alice_pegged_balance = pegged.balanceOf(alice)
    assert peg_keeper.withdraw_pegged(
        little_amount * 50 * 10 ** 18, alice, {"from": admin}
    ).return_value

    alice_new_pegged_balance = pegged.balanceOf(alice)
    peg_keeper_new_pegged_balance = pegged.balanceOf(peg_keeper)

    assert alice_pegged_balance == alice_new_pegged_balance - little_amount * 10 ** 18
    assert peg_keeper_new_pegged_balance == 0


def test_withdraw_pegged(
    pegged,
    alice,
    peg_keeper,
    admin,
    little_amount,
    provide_little_amount_of_pegged_to_peg_keeper,
):
    amount = little_amount / 2 * 10 ** 18

    peg_keeper_pegged_balance = pegged.balanceOf(peg_keeper)
    alice_pegged_balance = pegged.balanceOf(alice)
    assert peg_keeper.withdraw_pegged(amount, alice, {"from": admin}).return_value

    alice_new_pegged_balance = pegged.balanceOf(alice)
    peg_keeper_new_pegged_balance = pegged.balanceOf(peg_keeper)

    assert alice_pegged_balance == alice_new_pegged_balance - amount
    assert peg_keeper_pegged_balance == peg_keeper_new_pegged_balance + amount
