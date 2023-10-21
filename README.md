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
tbump --dry-run --bump=patch
```