# curve-stable-peg
Stabilizer for the Curve pools.


### Overview
Peg Keeper stabilizes the pool by adding/removing the coin when the pool is imbalanced.
Arbitrageurs execute `PegKeeper.update()` and receive part of the profit in LP tokens.


### Dependencies

* [python3](https://www.python.org/downloads/release/python-368/) version 3.6 or greater, python3-dev
* [brownie](https://github.com/eth-brownie/brownie) – tested with version [1.16.4](https://github.com/eth-brownie/brownie/releases/tag/v1.16.4)
* [brownie-token-tester](https://github.com/iamdefinitelyahuman/brownie-token-tester)
* [ganache-cli](https://github.com/trufflesuite/ganache-cli) – tested with version [2.13.2](https://github.com/trufflesuite/ganache-cli/releases/tag/v2.13.2)


### Testing
The test suite contains common tests for all variants of PegKeepers, as well as unique per-type tests.
To run the entire suite:
```shell
brownie test
```
For other parameters see [tests](tests).


### Glossary
`Peg` – coin we peg to  
`Pegger` – coin we are pegging and able to mint/burn  
`PegKeeper` – contract that maintains the peg  
[`template`](contracts/template) – version of peg keeper with the swap  
[`pluggable`](contracts/pluggable) –version of peg keeper with already deployed swap


### License

(c) Curve.Fi, 2020 - [All rights reserved](LICENSE).
