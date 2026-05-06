# ZMK Studio Export - Quick Reference

## What Was Done

Successfully exported your ZMK Studio keymap and converted it to your firmware keymap file.

## Your Current Keymap

- **Layer 0** (BASE): QWERTY with home row mods
- **Layer 1**: Numbers, symbols, calculator/email shortcuts
- **Layer 2**: Navigation arrows, volume, mouse buttons
- **Layer 3**: All 12 function keys (F1-F12) + numpad

## How to Export Again (After Making Changes)

```bash
# 1. Activate the virtual environment
cd ~/Development/repos/zmk-keyboard-toucan
source .venv/bin/activate

# 2. Export from your keyboard (make sure Chrome/ZMK Studio is closed)
python export_zmk_keymap.py --port /dev/ttyACM1

# 3. Convert to keymap format
python zmk_studio_to_keymap.py zmk_keymap_export.json

# 4. Review changes
git diff config/toucan.keymap

# 5. Commit
git add config/toucan.keymap
git commit -m "Update keymap from ZMK Studio"

# 6. Push to trigger build
git push
```

## Important Notes

- **Always close ZMK Studio web app** before running the export (so the serial port is free)
- **Your keyboard is on** `/dev/ttyACM1` (use `--port /dev/ttyACM1`)
- **Changes must be saved** in ZMK Studio before they'll appear in the export
- **Virtual environment** must be activated (`source .venv/bin/activate`)

## Known Issue

One key in Layer 2 has an invalid bluetooth command (command 4 doesn't exist in ZMK). It's safely set to `&none` (do nothing). You may want to fix this in ZMK Studio.

## If the Port Changes

Find your keyboard:
```bash
for port in /dev/ttyACM*; do 
    udevadm info -q property -n $port 2>/dev/null | grep "ID_MODEL=Toucan" && echo "Found at: $port"
done
```

Then use that port: `python export_zmk_keymap.py --port /dev/ttyACMX`

## Troubleshooting

**"Port busy" error**: Close ZMK Studio web interface  
**"Timeout" error**: Try the other ACM port  
**"Changes not showing"**: Make sure you saved in ZMK Studio first

## Files Created

- `export_zmk_keymap.py` - Export tool (uses zmk-studio-api)
- `zmk_studio_to_keymap.py` - Converter (JSON → .keymap)
- `.venv/` - Python virtual environment (with zmk-studio-api installed)
- `README_EXPORT.md` - Full documentation
- `QUICKSTART.md` - Quick start guide

## Next Build

Your changes are committed. Push to GitHub to trigger the build:

```bash
git push
```

Then download and flash the firmware to your keyboard.
