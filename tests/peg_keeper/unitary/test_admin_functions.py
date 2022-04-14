import brownie
import pytest
from brownie import ZERO_ADDRESS, chain
from flaky import flaky

ADMIN_ACTIONS_DEADLINE = 3 * 86400


def test_parameters(peg_keeper, swap, pegged, admin, receiver):
    assert peg_keeper.pegged() == pegged
    assert peg_keeper.pool() == swap

    assert peg_keeper.admin() == admin
    assert peg_keeper.future_admin() == ZERO_ADDRESS

    assert peg_keeper.receiver() == receiver
    assert peg_keeper.future_receiver() == ZERO_ADDRESS

    assert peg_keeper.caller_share() == 2e4

    if hasattr(peg_keeper, "pegged_admin"):
        assert peg_keeper.pegged_admin() == admin
        assert peg_keeper.future_pegged_admin() == ZERO_ADDRESS


def test_update_access(
    peg_keeper,
    peg_keeper_updater,
    add_initial_liquidity,
    provide_token_to_peg_keeper,
    imbalance_pool,
):
    imbalance_pool(0)
    peg_keeper.update({"from": peg_keeper_updater})


@pytest.mark.template
def test_update_no_access(peg_keeper, bob):
    with brownie.reverts("dev: callable only by the pool"):
        peg_keeper.update({"from": bob})


def test_set_new_caller_share(peg_keeper, admin):
    new_caller_share = 5e4
    peg_keeper.set_new_caller_share(new_caller_share, {"from": admin})

    assert peg_keeper.caller_share() == new_caller_share


def test_set_new_caller_share_bad_value(peg_keeper, admin):
    with brownie.reverts("dev: bad part value"):
        peg_keeper.set_new_caller_share(1e5 + 1, {"from": admin})


def test_set_new_caller_share_only_admin(peg_keeper, alice):
    with brownie.reverts("dev: only admin"):
        peg_keeper.set_new_caller_share(5e4, {"from": alice})


def test_commit_new_admin(peg_keeper, admin, alice):
    peg_keeper.commit_new_admin(alice, {"from": admin})

    assert peg_keeper.admin() == admin
    assert peg_keeper.future_admin() == alice
    assert (
        0
        <= chain.time() + ADMIN_ACTIONS_DEADLINE - peg_keeper.admin_actions_deadline()
        <= 1
    )


def test_commit_new_admin_access(peg_keeper, alice):
    with brownie.reverts("dev: only admin"):
        peg_keeper.commit_new_admin(alice, {"from": alice})


def test_apply_new_admin(peg_keeper, admin, alice):
    peg_keeper.commit_new_admin(alice, {"from": admin})
    chain.sleep(ADMIN_ACTIONS_DEADLINE)
    peg_keeper.apply_new_admin({"from": alice})

    assert peg_keeper.admin() == alice
    assert peg_keeper.future_admin() == alice
    assert peg_keeper.admin_actions_deadline() == 0


def test_apply_new_admin_only_new_admin(peg_keeper, admin, alice, bob):
    peg_keeper.commit_new_admin(alice, {"from": admin})
    chain.sleep(ADMIN_ACTIONS_DEADLINE)

    with brownie.reverts("dev: only new admin"):
        peg_keeper.apply_new_admin({"from": bob})


@flaky
def test_apply_new_admin_deadline(peg_keeper, admin, alice):
    peg_keeper.commit_new_admin(alice, {"from": admin})
    chain.sleep(ADMIN_ACTIONS_DEADLINE - 1)
    with brownie.reverts("dev: insufficient time"):
        peg_keeper.apply_new_admin({"from": alice})


def test_apply_new_admin_no_active(peg_keeper, admin, alice):
    peg_keeper.commit_new_admin(alice, {"from": admin})
    chain.sleep(ADMIN_ACTIONS_DEADLINE)
    peg_keeper.apply_new_admin({"from": alice})

    with brownie.reverts("dev: no active action"):
        peg_keeper.apply_new_admin({"from": alice})


def test_revert_new_admin(peg_keeper, admin, alice):
    peg_keeper.commit_new_admin(alice, {"from": admin})
    peg_keeper.revert_new_staff({"from": admin})

    assert peg_keeper.admin_actions_deadline() == 0


def test_revert_new_admin_only_admin(peg_keeper, admin, alice):
    peg_keeper.commit_new_admin(alice, {"from": admin})
    with brownie.reverts("dev: only admin"):
        peg_keeper.revert_new_staff({"from": alice})


def test_revert_new_admin_without_commit(peg_keeper, admin):
    peg_keeper.revert_new_staff({"from": admin})

    assert peg_keeper.admin_actions_deadline() == 0


def test_commit_new_receiver(peg_keeper, admin, alice, receiver):
    peg_keeper.commit_new_receiver(alice, {"from": admin})

    assert peg_keeper.receiver() == receiver
    assert peg_keeper.future_receiver() == alice
    assert (
        0
        <= chain.time() + ADMIN_ACTIONS_DEADLINE - peg_keeper.admin_actions_deadline()
        <= 1
    )


def test_commit_new_receiver_access(peg_keeper, alice):
    with brownie.reverts("dev: only admin"):
        peg_keeper.commit_new_receiver(alice, {"from": alice})


def test_apply_new_receiver(peg_keeper, admin, alice):
    peg_keeper.commit_new_receiver(alice, {"from": admin})
    chain.sleep(ADMIN_ACTIONS_DEADLINE)
    peg_keeper.apply_new_receiver({"from": admin})

    assert peg_keeper.receiver() == alice
    assert peg_keeper.future_receiver() == alice


@flaky
def test_apply_new_receiver_deadline(peg_keeper, admin, alice):
    peg_keeper.commit_new_receiver(alice, {"from": admin})
    chain.sleep(ADMIN_ACTIONS_DEADLINE - 1)
    with brownie.reverts("dev: insufficient time"):
        peg_keeper.apply_new_receiver({"from": admin})


def test_apply_new_receiver_no_active(peg_keeper, alice):
    with brownie.reverts("dev: no active action"):
        peg_keeper.apply_new_receiver({"from": alice})


def test_revert_new_receiver(peg_keeper, admin, alice):
    peg_keeper.commit_new_receiver(alice, {"from": admin})
    peg_keeper.revert_new_staff({"from": admin})

    assert peg_keeper.admin_actions_deadline() == 0


def test_revert_new_receiver_only_admin(peg_keeper, admin, alice):
    peg_keeper.commit_new_receiver(alice, {"from": admin})
    with brownie.reverts("dev: only admin"):
        peg_keeper.revert_new_staff({"from": alice})


def test_revert_new_receiver_without_commit(peg_keeper, admin):
    peg_keeper.revert_new_staff({"from": admin})

    assert peg_keeper.admin_actions_deadline() == 0


@pytest.mark.parametrize("action0", ["commit_new_admin", "commit_new_receiver"])
@pytest.mark.parametrize("action1", ["commit_new_admin", "commit_new_receiver"])
def test_commit_already_active(peg_keeper, admin, alice, action0, action1):
    if action0 == "commit_new_admin":
        peg_keeper.commit_new_admin(alice, {"from": admin})
    else:
        peg_keeper.commit_new_receiver(alice, {"from": admin})

    with brownie.reverts("dev: active action"):
        if action1 == "commit_new_admin":
            peg_keeper.commit_new_admin(alice, {"from": admin})
        else:
            peg_keeper.commit_new_receiver(alice, {"from": admin})
