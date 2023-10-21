# multicaller

Helper for using multicall to aggregate onchain data calls into a single RPC call.


## DEV

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
export new_version=0.1.6 && tbump $new_version
```

The release workflow will then detect that a branch with a `v` prefix exists and create a release from it.

Additionally, the package will be published to PyPI.
