import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "set_peg_keeper")


def test_exchange_peg_to_pegged():
    pass


def test_exchange_pegged_to_peg():
    pass
