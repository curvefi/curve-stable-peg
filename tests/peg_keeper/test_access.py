import brownie
from brownie import ZERO_ADDRESS


def test_parameters(peg_keeper, swap, pegged, admin):
    assert peg_keeper.pegged() == pegged
    assert peg_keeper.pool() == swap

    assert peg_keeper.admin() == admin
    assert peg_keeper.future_admin() == ZERO_ADDRESS

    assert peg_keeper.min_asymmetry() == 2


def test_access(peg_keeper, swap, add_initial_liquidity):
    peg_keeper.update({"from": swap})


def test_update_no_access(peg_keeper, bob):
    with brownie.reverts():
        peg_keeper.update({"from": bob})


def test_commit_new_admin(peg_keeper, admin, alice):
    peg_keeper.commit_new_admin(alice, {"from": admin})

    assert peg_keeper.admin() == admin
    assert peg_keeper.future_admin() == alice


def test_apply_new_admin(peg_keeper, admin, alice):
    peg_keeper.commit_new_admin(alice, {"from": admin})
    peg_keeper.apply_new_admin({"from": alice})

    assert peg_keeper.admin() == alice
    assert peg_keeper.future_admin() == alice


def test_set_new_min_asymmetry(peg_keeper, admin, alice):
    new_min_asymmetry = 2e7
    peg_keeper.set_new_min_asymmetry(new_min_asymmetry, {"from": admin})

    assert peg_keeper.min_asymmetry() == new_min_asymmetry


def test_set_new_min_asymmetry_bad_value(peg_keeper, admin, alice):
    with brownie.reverts():
        peg_keeper.set_new_min_asymmetry(0, {"from": admin})
    with brownie.reverts():
        peg_keeper.set_new_min_asymmetry(10 ** 10, {"from": admin})


def test_commit_new_admin_access(peg_keeper, alice):
    with brownie.reverts("Access denied."):
        peg_keeper.commit_new_admin(alice, {"from": alice})


def test_apply_new_admin_access(peg_keeper, alice):
    with brownie.reverts("Access denied."):
        peg_keeper.apply_new_admin({"from": alice})


def test_set_new_min_asymmetry_access(peg_keeper, alice):
    with brownie.reverts("Access denied."):
        peg_keeper.set_new_min_asymmetry(2e7, {"from": alice})
