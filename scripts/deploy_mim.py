from brownie import accounts
from brownie.network.gas.strategies import GasNowScalingStrategy
from brownie.project.main import get_loaded_projects

DEPLOYER = accounts.at("0x71F718D3e4d1449D1502A6A7595eb84eBcCB1683", force=True)

gas_price = GasNowScalingStrategy("slow", "fast")


MIM_POOL = "0x5a6A4D54456819380173272A5E8E9B9904BdF41B"
PROFIT_RECEIVER = "0x8CF8Af108B3B46DDC6AD596aebb917E053F0D72b"  # Pool proxy
CALLER_SHARE = 2 * 10**4  # 2%

PEGGED_ADMIN = "0x5f0DeE98360d8200b20812e174d139A1a633EDd2"  # Mim owner


def main():
    project = get_loaded_projects()[0]

    peg_keeper_mim = project.PegKeeperMim.deploy(
        MIM_POOL,
        PROFIT_RECEIVER,
        CALLER_SHARE,
        {"from": DEPLOYER, "gas_price": gas_price},
    )
    peg_keeper_mim.commit_new_pegged_admin(
        PEGGED_ADMIN,
        {"from": DEPLOYER, "gas_price": gas_price},
    )
