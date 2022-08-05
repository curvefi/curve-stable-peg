## Tests

to run only specific test suites use:  
`--type` to run only certain type of peg keepers  
`--contracts` to run only certain contracts of peg keepers  
`--unitary` to run only unitary tests  
`--integration` to run only integration tests  
`--forked-tests` to run forked tests(do not forget to specify network, e.g. `--network mainnet-fork`)  

For example:
```shell
brownie test --unitary --type pluggable-optimized
brownie test --network mainnet-fork --forked-tests --contracts mim
```
