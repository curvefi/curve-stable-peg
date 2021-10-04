## Tests
Tests are divided into 3 parts:  
- `peg_keeper` – unitary tests for Peg Keeper
- `stable_swap` – tests for pool with no Peg Keeper set
- `stable_peg` – tests of Peg Keeper set with the pool

Add `--peg-keeper`, `--stable-swap` or/and `--stable-peg` to run only those test suites.  
Also use:  
`--unitary` to run only unitary tests  
`--integration` to run only integration tests  
For example:
```shell
brownie test --stable-peg --unitary
```
