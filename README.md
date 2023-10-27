# multicaller

Helper for using multicall to aggregate onchain data calls into a single RPC call.


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

We can use tbump to automatically bump our versions in preparation of a release.

```bash 
new_version=0.1.1
git checkout -b v$new_version
git push --set-upstream origin $(git rev-parse --abbrev-ref HEAD)
tbump new_version
```

The release workflow will then detect that a branch with a `v` prefix exists and create a release from it.

Additionally, the package will be published to PyPI.
