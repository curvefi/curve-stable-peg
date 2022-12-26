import pytest

ACTION_DELAY = 15 * 60


@pytest.fixture(scope="module")
def wait_for_peg(chain):
    def inner():
        chain.sleep(ACTION_DELAY)
    yield inner


@pytest.fixture(scope="module", autouse=True)
def provide_peg(add_initial_liquidity, mint_bob, approve_bob, base_amount, pegged, swap, alice, wait_for_peg):
    amount = base_amount * 10 ** 18 // 5
    pegged._mint_for_testing(alice, amount, {"from": alice})
    pegged.approve(swap, amount, {"from": alice})
    swap.provide_pegged(amount, {"from": alice})
    wait_for_peg()
