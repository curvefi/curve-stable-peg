## Tests
Tests are divided into 3 parts:  
- `peg_keeper` – unitary tests for Peg Keeper
- `stable_swap` – tests for pool with no Peg Keeper set
- `stable_peg` – tests of Peg Keeper set with the pool

Add `--peg-keeper`, `--stable-swap` or/and `--stable-peg` to run only those test suites.  
Also use:  
`--type` to run only certain type of peg keepers  
`--contracts` to run only certain contracts of peg keepers
`--unitary` to run only unitary tests  
`--integration` to run only integration tests  
`--forked-tests` to run forked tests(do not forget to specify network, e.g. `--network mainnet-fork`)  
For example:
```shell
brownie test --stable-peg --unitary --type pluggable-optimized
brownie test --network mainnet-fork --forked-tests --contracts mim
```
