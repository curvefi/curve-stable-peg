import brownie
import pytest
from brownie import ZERO_ADDRESS, chain, web3

ADMIN_ACTIONS_DEADLINE = 3 * 86400


def test_parameters(peg_keeper, swap, pegged, admin, receiver):
    assert peg_keeper.pegged() == pegged
    assert peg_keeper.pool() == swap

    assert peg_keeper.admin() == admin
    assert peg_keeper.future_admin() == ZERO_ADDRESS

    assert peg_keeper.receiver() == receiver
    assert peg_keeper.future_receiver() == ZERO_ADDRESS

    assert peg_keeper.min_asymmetry() == 2


def test_update_access(peg_keeper, swap, add_initial_liquidity):
    peg_keeper.update({"from": swap})


def test_update_no_access(peg_keeper, bob):
    with brownie.reverts("dev: callable only by the pool"):
        peg_keeper.update({"from": bob})


def test_set_new_min_asymmetry(peg_keeper, admin, alice):
    new_min_asymmetry = 2e7
    peg_keeper.set_new_min_asymmetry(new_min_asymmetry, {"from": admin})

    assert peg_keeper.min_asymmetry() == new_min_asymmetry


def test_set_new_min_asymmetry_bad_value(peg_keeper, admin, alice):
    with brownie.reverts("dev: bad asymmetry value"):
        peg_keeper.set_new_min_asymmetry(0, {"from": admin})
    with brownie.reverts("dev: bad asymmetry value"):
        peg_keeper.set_new_min_asymmetry(10 ** 10, {"from": admin})


def test_set_new_min_asymmetry_access(peg_keeper, alice):
    with brownie.reverts("dev: only admin"):
        peg_keeper.set_new_min_asymmetry(2e7, {"from": alice})


def test_commit_new_admin(peg_keeper, admin, alice):
    tx = peg_keeper.commit_new_admin(alice, {"from": admin})
    tx_time = web3.eth.get_block(tx.block_number).timestamp

    assert peg_keeper.admin() == admin
    assert peg_keeper.future_admin() == alice
    assert tx_time + ADMIN_ACTIONS_DEADLINE == peg_keeper.admin_actions_deadline()


def test_commit_new_admin_access(peg_keeper, alice):
    with brownie.reverts("dev: only admin"):
        peg_keeper.commit_new_admin(alice, {"from": alice})


def test_apply_new_admin(peg_keeper, admin, alice):
    peg_keeper.commit_new_admin(alice, {"from": admin})
    chain.sleep(ADMIN_ACTIONS_DEADLINE)
    peg_keeper.apply_new_admin({"from": alice})

    assert peg_keeper.admin() == alice
    assert peg_keeper.future_admin() == alice


def test_apply_new_admin_deadline(peg_keeper, admin, alice):
    peg_keeper.commit_new_admin(alice, {"from": admin})
    chain.sleep(ADMIN_ACTIONS_DEADLINE - 60)
    with brownie.reverts("dev: insufficient time"):
        peg_keeper.apply_new_admin({"from": alice})


def test_apply_new_admin_no_active(peg_keeper, alice):
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
    tx = peg_keeper.commit_new_receiver(alice, {"from": admin})
    tx_time = web3.eth.get_block(tx.block_number).timestamp

    assert peg_keeper.receiver() == receiver
    assert peg_keeper.future_receiver() == alice
    assert tx_time + ADMIN_ACTIONS_DEADLINE == peg_keeper.admin_actions_deadline()


def test_commit_new_receiver_access(peg_keeper, alice):
    with brownie.reverts("dev: only admin"):
        peg_keeper.commit_new_receiver(alice, {"from": alice})


def test_apply_new_receiver(peg_keeper, admin, alice):
    peg_keeper.commit_new_receiver(alice, {"from": admin})
    chain.sleep(ADMIN_ACTIONS_DEADLINE)
    peg_keeper.apply_new_receiver({"from": admin})

    assert peg_keeper.receiver() == alice
    assert peg_keeper.future_receiver() == alice


def test_apply_new_receiver_deadline(peg_keeper, admin, alice):
    peg_keeper.commit_new_receiver(alice, {"from": admin})
    chain.sleep(ADMIN_ACTIONS_DEADLINE - 60)
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
