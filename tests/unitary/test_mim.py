import brownie
import pytest

pytestmark = pytest.mark.usefixtures(
    "add_initial_liquidity",
    "mint_alice",
    "approve_alice",
)


@pytest.fixture(scope="module", autouse=True)
def remove_pegged_from_peg_keeper(pegged, peg_keeper):
    balance = pegged.balanceOf(peg_keeper)
    pegged.burn(balance, {"from": peg_keeper})


@pytest.fixture(scope="module")
def little_amount():
    yield 100


@pytest.fixture(scope="function")
def add_little_amount_of_pegged_in_peg_keeper(peg_keeper, pegged, little_amount, alice):
    amount = little_amount * 10 ** pegged.decimals()
    pegged._mint_for_testing(peg_keeper, amount, {"from": alice})


def test_provide_no_balance(
    swap,
    peg,
    pegged,
    alice,
    peg_keeper,
    peg_keeper_updater,
):
    swap.add_liquidity([0, 10**24], 0, {"from": alice})
    balances = [swap.balances(0), swap.balances(1)]
    real_balances = [pegged.balanceOf(swap), peg.balanceOf(swap)]

    with brownie.reverts():
        peg_keeper.update({"from": peg_keeper_updater})

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
    little_amount,
    add_little_amount_of_pegged_in_peg_keeper,
):
    swap.add_liquidity([0, 10**24], 0, {"from": alice})

    balances = [swap.balances(0), swap.balances(1)]
    real_balances = [pegged.balanceOf(swap), peg.balanceOf(swap)]

    # Profit is 0
    assert "Provide" in peg_keeper.update({"from": peg_keeper_updater}).events
    provided_amount = little_amount * 10**18

    new_balances = [swap.balances(0), swap.balances(1)]
    new_real_balances = [pegged.balanceOf(swap), peg.balanceOf(swap)]
    assert new_balances[0] == balances[0] + provided_amount
    assert new_balances[1] == balances[1]

    assert new_real_balances[0] == real_balances[0] + provided_amount
    assert new_real_balances[1] == real_balances[1]


def test_commit_new_pegged_admin(peg_keeper, admin, bob):
    # Initially admin == pegged_admin
    peg_keeper.commit_new_pegged_admin(bob, {"from": admin})
    assert peg_keeper.pegged_admin() == admin
    assert peg_keeper.future_pegged_admin() == bob

    with brownie.reverts():  # dev: only pegged admin
        peg_keeper.commit_new_pegged_admin(bob, {"from": bob})


def test_new_pegged_admin(
    peg_keeper, pegged, add_little_amount_of_pegged_in_peg_keeper, admin, bob
):
    peg_keeper.commit_new_pegged_admin(bob, {"from": admin})

    with brownie.reverts():  # dev: only new pegged admin
        peg_keeper.apply_new_pegged_admin({"from": admin})
    peg_keeper.apply_new_pegged_admin({"from": bob})
    assert peg_keeper.pegged_admin() == bob
    assert peg_keeper.future_pegged_admin() == bob

    # Only pegged admin
    with brownie.reverts():  # dev: only pegged admin
        peg_keeper.commit_new_pegged_admin(admin, {"from": admin})
    amount = pegged.balanceOf(peg_keeper)
    assert amount > 0
    with brownie.reverts():  # dev: only pegged admin
        peg_keeper.withdraw_pegged(amount, admin, {"from": admin})
    peg_keeper.withdraw_pegged(amount, {"from": bob})


def test_withdraw_pegged_no_balance(
    pegged,
    alice,
    peg_keeper,
    admin,
    base_amount,
):
    alice_pegged_balance = pegged.balanceOf(alice)

    assert not peg_keeper.withdraw_pegged(
        base_amount * 10**18, alice, {"from": admin}
    ).return_value

    alice_new_pegged_balance = pegged.balanceOf(alice)
    assert alice_pegged_balance == alice_new_pegged_balance


def test_withdraw_pegged_exceed(
    pegged,
    alice,
    peg_keeper,
    admin,
    little_amount,
    add_little_amount_of_pegged_in_peg_keeper,
):
    alice_pegged_balance = pegged.balanceOf(alice)
    assert peg_keeper.withdraw_pegged(
        little_amount * 50 * 10**18, alice, {"from": admin}
    ).return_value

    alice_new_pegged_balance = pegged.balanceOf(alice)
    peg_keeper_new_pegged_balance = pegged.balanceOf(peg_keeper)

    assert alice_pegged_balance == alice_new_pegged_balance - little_amount * 10**18
    assert peg_keeper_new_pegged_balance == 0


def test_withdraw_pegged(
    pegged,
    alice,
    peg_keeper,
    admin,
    little_amount,
    add_little_amount_of_pegged_in_peg_keeper,
):
    amount = little_amount / 2 * 10**18

    peg_keeper_pegged_balance = pegged.balanceOf(peg_keeper)
    alice_pegged_balance = pegged.balanceOf(alice)
    returned_amount = peg_keeper.withdraw_pegged(
        amount, alice, {"from": admin}
    ).return_value
    assert returned_amount == amount

    alice_new_pegged_balance = pegged.balanceOf(alice)
    peg_keeper_new_pegged_balance = pegged.balanceOf(peg_keeper)

    assert alice_pegged_balance == alice_new_pegged_balance - amount
    assert peg_keeper_pegged_balance == peg_keeper_new_pegged_balance + amount


def test_event(peg_keeper, pegged, alice, admin):
    amount = pegged.balanceOf(alice)
    pegged.transfer(peg_keeper, amount, {"from": alice})
    tx = peg_keeper.withdraw_pegged(amount, alice, {"from": admin})
    event = tx.events["WithdrawPegged"]
    assert event["amount"] == amount
    assert event["receiver"] == alice
