import brownie
from brownie import ZERO_ADDRESS


def test_parameters(peg_keeper, pool, pegged, receiver, admin):
    assert peg_keeper.pegged() == pegged
    assert peg_keeper.pool() == pool

    assert peg_keeper.admin() == admin
    assert peg_keeper.receiver() == receiver

    assert peg_keeper.future_admin() == ZERO_ADDRESS
    assert peg_keeper.future_receiver() == ZERO_ADDRESS


def test_update_access(peg_keeper, alice):
    # Available for anyone
    peg_keeper.update({"from": alice})


def test_commit_new_receiver(peg_keeper, admin, alice, receiver):
    peg_keeper.commit_new_receiver(alice, {"from": admin})

    assert peg_keeper.receiver() == receiver
    assert peg_keeper.future_receiver() == alice


def test_apply_new_receiver(peg_keeper, admin, alice):
    peg_keeper.commit_new_receiver(alice, {"from": admin})
    peg_keeper.apply_new_receiver({"from": admin})

    assert peg_keeper.receiver() == alice
    assert peg_keeper.future_receiver() == alice


def test_commit_new_admin(peg_keeper, admin, alice):
    peg_keeper.commit_new_admin(alice, {"from": admin})

    assert peg_keeper.admin() == admin
    assert peg_keeper.future_admin() == alice


def test_apply_new_admin(peg_keeper, admin, alice):
    peg_keeper.commit_new_admin(alice, {"from": admin})
    peg_keeper.apply_new_admin({"from": alice})

    assert peg_keeper.admin() == alice
    assert peg_keeper.future_admin() == alice


def test_commit_new_receiver_access(peg_keeper, alice):
    with brownie.reverts("Access denied."):
        peg_keeper.commit_new_receiver(alice, {"from": alice})


def test_apply_new_receiver_access(peg_keeper, alice):
    with brownie.reverts("Access denied."):
        peg_keeper.apply_new_receiver({"from": alice})


def test_commit_new_admin_access(peg_keeper, alice):
    with brownie.reverts("Access denied."):
        peg_keeper.commit_new_admin(alice, {"from": alice})


def test_apply_new_admin_access(peg_keeper, alice):
    with brownie.reverts("Access denied."):
        peg_keeper.apply_new_admin({"from": alice})
