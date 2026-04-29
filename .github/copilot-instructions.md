# RTK — Token-Optimized CLI

**rtk** is a CLI proxy that filters and compresses command outputs, saving 60-90% tokens.

## Rules for AI assistants

1. **Always prefix shell commands with `rtk`** — never run raw `git`, `cat`, `grep`, `find`, `ls`, `head`, `tail`, `cargo`, `docker`, `kubectl`, etc.
2. **For ALL file reads, use `rtk read <file>` in the terminal** — do NOT use the IDE's built-in file reader, `cat`, `head`, `tail`, or `Get-Content`. This applies even to single-file or quick lookups.
3. **For searching file contents, use `rtk grep`** — not raw `grep`, `rg`, or `Select-String`.
4. **For finding files by name, use `rtk find`** — not raw `find`, `Get-ChildItem`, or `dir`.
5. **For directory listings, use `rtk ls`** — not raw `ls` or `dir`.
6. **Use Git Bash** as the default terminal on Windows for these commands.

```bash
# Instead of:              Use:
cat file.py                rtk read file.py
head -50 file.py           rtk read file.py
grep "pattern" .           rtk grep "pattern" .
find . -name "*.py"        rtk find "*.py" .
ls -la                     rtk ls .
git status                 rtk git status
git log -10                rtk git log -10
cargo test                 rtk cargo test
docker ps                  rtk docker ps
kubectl get pods           rtk kubectl pods
```

## Meta commands (use directly)

```bash
rtk gain              # Token savings dashboard
rtk gain --history    # Per-command savings history
rtk discover          # Find missed rtk opportunities
rtk proxy <cmd>       # Run raw (no filtering) but track usage
```

## Common commands

```bash
rtk ls .                        # Token-optimized directory tree
rtk read file.rs                # Smart file reading (MUST use rtk for file reads!)
rtk read file.rs -l aggressive  # Signatures only (strips bodies)
rtk smart file.rs               # 2-line heuristic code summary
rtk find "*.rs" .               # Compact find results
rtk grep "pattern" .            # Grouped search results
rtk diff file1 file2            # Condensed diff
