## Tests roadmap
1.Test `PegKeeper` with default `CurvePool`(from `contracts/testing`)
- Access to all methods
- Actions delay of mint/burn
- First `add_liquidity`, `remove_liquidity`, `exchange`
- Minimum LP and coin values to mint and add
- Stress test with hypothesis

2. Test `CurvePool`, that automatically executes `PegKeeper` (choose parameters for `PegKeeper` so it does not affect)
- Copy from `curve-contract`

3. Test `PegKeeper` with `CurvePool`, that automatically executes `PegKeeper`
- First `add_liquidity`, `remove_liquidity`, `remove_liquidity_imbalance`, `remove_liquidity_one_coin`, `exchange`
- Minimum LP and coin values to mint and add
- Stress test with hypothesis
