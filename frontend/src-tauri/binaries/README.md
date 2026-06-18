# Sidecar binaries

Tauri loads the backend from here as a sidecar. Build it with:

```bash
cd ../../../backend
pip install pyinstaller
./build_sidecar.sh
```

That produces `voiceclone-backend-<target-triple>` in this directory (e.g.
`voiceclone-backend-aarch64-apple-darwin`). The triple must match your Rust
host target (`rustc -Vv | grep host`). These binaries are gitignored.
