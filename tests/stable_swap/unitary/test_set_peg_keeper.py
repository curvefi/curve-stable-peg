import brownie
from brownie import ZERO_ADDRESS


def test_set_peg_keeper(swap, peg_keeper, alice):
    assert swap.peg_keeper() == ZERO_ADDRESS
    swap.set_peg_keeper(peg_keeper, {"from": alice})
    assert swap.peg_keeper() == peg_keeper


def test_no_access(swap, peg_keeper, bob):
    with brownie.reverts():
        swap.set_peg_keeper(peg_keeper, {"from": bob})
