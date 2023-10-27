# multicaller

Helper for using multicall to aggregate onchain data calls into a single RPC call.
## Features
* Uses multicall3, allowing for failing calls on a per-call basis
* Iteratively breaks up a call bundle if it's too large for the endpoint
* Uses native web3py contract functions rather than requiring users to [write the function ABI for each call](https://github.com/banteg/multicall.py/blob/9117c552c6ae85acec8452961db0aac51119070b/examples/daistats.py#L77)


## Dev

### Format

```bash
make fmt
```

### Lint

```bash
make lint
```

### Test

```bash
make test
```

#### Run all tests

```bash
make all
```

### Releasing

We can use `tbump` to automatically bump our versions in preparation of a release.

```bash 
new_version=0.1.1
git checkout -b v$new_version
git push --set-upstream origin $(git rev-parse --abbrev-ref HEAD)
tbump new_version
```

The release workflow will then detect that a branch with a `v` prefix exists and create a release from it.

Additionally, the package will be published to PyPI.
