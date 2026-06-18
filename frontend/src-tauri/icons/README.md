# App icons

Tauri's bundler needs the icon set referenced in `tauri.conf.json`. Generate
them from a single square PNG (1024×1024 recommended):

```bash
cargo tauri icon path/to/logo.png
```

This writes `32x32.png`, `128x128.png`, `128x128@2x.png`, `icon.icns`, and
`icon.ico` into this folder. Until you do, `tauri build` will fail on missing
icons (`tauri dev` is more lenient).
