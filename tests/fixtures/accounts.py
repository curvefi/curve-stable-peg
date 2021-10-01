import pytest


@pytest.fixture(scope="session")
def admin(accounts):
    """Admin of Peg Keeper"""
    yield accounts[1]


@pytest.fixture(scope="session")
def alice(accounts):
    """Also owner of deployed contracts"""
    yield accounts[2]


@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[3]


@pytest.fixture(scope="session")
def charlie(accounts):
    yield accounts[4]


@pytest.fixture(scope="session")
def receiver(accounts):
    """Peg Keeper profit receiver"""
    yield accounts[5]
