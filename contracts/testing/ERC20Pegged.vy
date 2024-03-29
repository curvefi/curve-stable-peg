# @version ^0.2.0
"""
@notice Mintable and burnable mock ERC20 for testing
"""

event Transfer:
    _from: indexed(address)
    _to: indexed(address)
    _value: uint256

event Approval:
    _owner: indexed(address)
    _spender: indexed(address)
    _value: uint256

name: public(String[64])
symbol: public(String[32])
decimals: public(uint256)
balanceOf: public(HashMap[address, uint256])
allowances: HashMap[address, HashMap[address, uint256]]
total_supply: uint256

owner: address
minters: public(HashMap[address, bool])


@external
def __init__(_name: String[64], _symbol: String[32], _decimals: uint256):
    self.name = _name
    self.symbol = _symbol
    self.decimals = _decimals

    self.owner = msg.sender


@external
@view
def totalSupply() -> uint256:
    return self.total_supply


@external
@view
def allowance(_owner : address, _spender : address) -> uint256:
    return self.allowances[_owner][_spender]


@external
def transfer(_to : address, _value : uint256) -> bool:
    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    log Transfer(msg.sender, _to, _value)
    return True


@external
def transferFrom(_from : address, _to : address, _value : uint256) -> bool:
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    self.allowances[_from][msg.sender] -= _value
    log Transfer(_from, _to, _value)
    return True


@external
def approve(_spender : address, _value : uint256) -> bool:
    self.allowances[msg.sender][_spender] = _value
    log Approval(msg.sender, _spender, _value)
    return True


@external
def add_minter(_minter: address):
    assert msg.sender == self.owner, "Access denied."
    self.minters[_minter] = True


@external
def mint(_target: address, _value: uint256) -> bool:
    assert self.minters[msg.sender], "Access denied."
    self.total_supply += _value
    self.balanceOf[_target] += _value
    log Transfer(ZERO_ADDRESS, _target, _value)

    return True


@external
def burn(_value: uint256) -> bool:
    self.balanceOf[msg.sender] -= _value
    self.total_supply -= _value
    log Transfer(msg.sender, ZERO_ADDRESS, _value)

    return True


@external
def _mint_for_testing(_target: address, _value: uint256) -> bool:
    self.total_supply += _value
    self.balanceOf[_target] += _value
    log Transfer(ZERO_ADDRESS, _target, _value)

    return True
