## Tests

Use:
`--contract` to run certain contract of peg keepers(see [_contracts](conftest.py)  
`--unitary` to run only unitary tests  
`--integration` to run only integration tests  
`--forked-tests` to run forked tests(do not forget to specify network, e.g. `--network mainnet-fork`)  

For example:
```shell
brownie test --integration
brownie test --network mainnet-fork --forked-tests --contract mim
```
