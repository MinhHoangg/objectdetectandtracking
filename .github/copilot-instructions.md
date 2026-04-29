# RTK — Token-Optimized CLI

**rtk** is a CLI proxy that filters and compresses command outputs, saving 60-90% tokens.

## Rules for AI assistants

1. **Always prefix shell commands with `rtk`** — never run raw `git`, `cat`, `grep`, `find`, `ls`, `head`, `tail`, `cargo`, `docker`, `kubectl`, etc.
2. **For ALL file reads, use `rtk read <file>` in the terminal** — do NOT use the IDE's built-in file reader, `cat`, `head`, `tail`, or `Get-Content`. This applies even to single-file or quick lookups.
3. **For searching file contents, use `rtk grep`** — not raw `grep`, `rg`, or `Select-String`.
4. **For finding files by name, use `rtk find`** — not raw `find`, `Get-ChildItem`, or `dir`.
5. **For directory listings, use `rtk ls`** — not raw `ls` or `dir`.
6. **Use Git Bash** as the default terminal on Windows for these commands.

## Files

```bash
# Instead of:                       Use:
cat file.py                         rtk read file.py
head -50 file.py                    rtk read file.py
tail -100 file.py                   rtk read file.py
Get-Content file.py                 rtk read file.py
# (signatures only, strip bodies)   rtk read file.py -l aggressive
# (2-line heuristic code summary)   rtk smart file.py
ls -la                              rtk ls .
dir                                 rtk ls .
find . -name "*.py"                 rtk find "*.py" .
Get-ChildItem -Recurse              rtk find "*.py" .
grep "pattern" .                    rtk grep "pattern" .
rg "pattern"                        rtk grep "pattern" .
Select-String "pattern"             rtk grep "pattern" .
diff file1 file2                    rtk diff file1 file2
```

## Git

```bash
# Instead of:                       Use:
git status                          rtk git status
git log -n 10                       rtk git log -n 10
git diff                            rtk git diff
git add .                           rtk git add .                 # -> "ok"
git commit -m "msg"                 rtk git commit -m "msg"       # -> "ok abc1234"
git push                            rtk git push                  # -> "ok main"
git pull                            rtk git pull                  # -> "ok 3 files +10 -2"
```

## GitHub CLI

```bash
# Instead of:                       Use:
gh pr list                          rtk gh pr list
gh pr view 42                       rtk gh pr view 42
gh issue list                       rtk gh issue list
gh run list                         rtk gh run list
```

## Test runners

```bash
# Instead of:                       Use:
jest                                rtk jest                      # failures only
vitest                              rtk vitest                    # failures only
playwright test                     rtk playwright test
pytest                              rtk pytest                    # -90%
go test ./...                       rtk go test ./...
cargo test                          rtk cargo test
rake test                           rtk rake test
rspec                               rtk rspec
<any failing cmd>                   rtk err <cmd>                 # filter errors only
<any test cmd>                      rtk test <cmd>                # generic, failures only
```

## Build & lint

```bash
# Instead of:                       Use:
eslint .                            rtk lint
biome check                         rtk lint biome
tsc                                 rtk tsc
next build                          rtk next build
prettier --check .                  rtk prettier --check .
cargo build                         rtk cargo build
cargo clippy                        rtk cargo clippy
ruff check                          rtk ruff check
golangci-lint run                   rtk golangci-lint run
rubocop                             rtk rubocop
```

## Package managers

```bash
# Instead of:                       Use:
pnpm list                           rtk pnpm list
pip list                            rtk pip list                  # auto-detect uv
pip list --outdated                 rtk pip outdated
bundle install                      rtk bundle install
prisma generate                     rtk prisma generate
```

## AWS

```bash
# Instead of:                                  Use:
aws sts get-caller-identity                    rtk aws sts get-caller-identity
aws ec2 describe-instances                     rtk aws ec2 describe-instances
aws lambda list-functions                      rtk aws lambda list-functions
aws logs get-log-events ...                    rtk aws logs get-log-events ...
aws cloudformation describe-stack-events ...   rtk aws cloudformation describe-stack-events ...
aws dynamodb scan ...                          rtk aws dynamodb scan ...
aws iam list-roles                             rtk aws iam list-roles
aws s3 ls                                      rtk aws s3 ls
```

## Containers

```bash
# Instead of:                       Use:
docker ps                           rtk docker ps
docker images                       rtk docker images
docker logs <container>             rtk docker logs <container>
docker compose ps                   rtk docker compose ps
kubectl get pods                    rtk kubectl pods
kubectl logs <pod>                  rtk kubectl logs <pod>
kubectl get services                rtk kubectl services
```

## Data & misc

```bash
# Instead of:                       Use:
cat config.json                     rtk json config.json          # structure without values
# (dependency summary)              rtk deps
env | grep AWS                      rtk env -f AWS
cat app.log                         rtk log app.log               # deduplicated
curl <url>                          rtk curl <url>                # truncate + save full
wget <url>                          rtk wget <url>
<long verbose command>              rtk summary <cmd>             # heuristic summary
<any command>                       rtk proxy <cmd>               # raw passthrough + tracking
```

## Meta commands (use directly)

```bash
rtk gain                            # Token savings dashboard
rtk gain --graph                    # ASCII graph (last 30 days)
rtk gain --history                  # Per-command savings history
rtk gain --daily                    # Day-by-day breakdown
rtk gain --all --format json        # JSON export
rtk discover                        # Find missed rtk opportunities
rtk discover --all --since 7        # All projects, last 7 days
rtk session                         # RTK adoption across recent sessions
rtk proxy <cmd>                     # Run raw (no filtering) but track usage
```

## Global flags

```bash
-u, --ultra-compact                 # ASCII icons, inline format (extra savings)
-v, --verbose                       # Increase verbosity (-v, -vv, -vvv)
```
