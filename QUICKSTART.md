# Quick Start: Export Your ZMK Studio Keymap

## TL;DR

```bash
# Install the library
pip install zmk-studio-api

# Export from your keyboard
python export_zmk_keymap.py

# Convert to keymap file
python zmk_studio_to_keymap.py zmk_keymap_export.json

# Review and commit
git diff config/toucan.keymap
git add config/toucan.keymap
git commit -m "Update keymap from ZMK Studio"
```

## What This Does

These tools extract your ZMK Studio keymap directly from your keyboard via USB/Bluetooth and convert it to the `.keymap` file format so it's saved in your firmware.

## Prerequisites

1. **Your keyboard must have ZMK Studio enabled**
   - Check your firmware for `CONFIG_ZMK_STUDIO=y`
   - If not enabled, you'll need to enable it and flash first

2. **Python 3.7 or newer**
   ```bash
   python3 --version
   ```

3. **USB or Bluetooth connection**
   - USB is recommended (faster, more reliable)
   - Make sure your keyboard is connected

## Installation

```bash
pip install zmk-studio-api
```

That's it! The required library includes all the protocol handling.

## Step-by-Step Usage

### Step 1: Connect Your Keyboard

- **USB:** Plug in your keyboard
- **Bluetooth:** Make sure it's paired and connected

On Linux, you may need to add yourself to the `dialout` group:
```bash
sudo usermod -a -G dialout $USER
# Then log out and log back in
```

### Step 2: Export the Keymap

Run the export tool:

```bash
cd ~/Development/repos/zmk-keyboard-toucan
python export_zmk_keymap.py
```

**What it does:**
- Auto-detects your keyboard on USB
- Connects using the ZMK Studio protocol
- Reads all layers and their bindings
- Saves to `zmk_keymap_export.json`

**If it fails:**
- Try specifying the port manually: `python export_zmk_keymap.py --port /dev/ttyACM0`
- Check if the device is locked (see README_EXPORT.md)
- Make sure ZMK Studio is enabled in your firmware

### Step 3: Convert to Keymap

Convert the JSON export to devicetree format:

```bash
python zmk_studio_to_keymap.py zmk_keymap_export.json
```

**What it does:**
- Reads the exported JSON
- Parses all behaviors (key presses, layer switches, etc.)
- Converts to ZMK devicetree syntax
- Updates `config/toucan.keymap` with your layers

### Step 4: Review Changes

Check what changed:

```bash
git diff config/toucan.keymap
```

Look for:
- ✓ Your layer names are preserved
- ✓ Key bindings match what you set in ZMK Studio
- ⚠️ Any FIXME comments (unknown behaviors to fix manually)

### Step 5: Test and Commit

If everything looks good:

```bash
# Commit the changes
git add config/toucan.keymap
git commit -m "Update keymap from ZMK Studio"

# Push to trigger build (if using GitHub Actions)
git push
```

Then flash the built firmware to your keyboard.

## Common Options

### Specify Serial Port

```bash
python export_zmk_keymap.py --port /dev/ttyACM0
```

On Windows: `--port COM3`

### Use Bluetooth Instead

```bash
python export_zmk_keymap.py --ble
```

### Custom Output File

```bash
python export_zmk_keymap.py --output my_keymap.json
python zmk_studio_to_keymap.py my_keymap.json config/toucan.keymap
```

## Troubleshooting

### "zmk-studio-api is required"

Install it:
```bash
pip install zmk-studio-api
```

### "No serial ports found"

1. Check USB connection
2. Try a different USB port/cable
3. Check permissions (Linux):
   ```bash
   ls -l /dev/ttyACM* /dev/ttyUSB*
   ```

### "Device is locked"

Unlock in ZMK Studio or press your `studio_unlock` key combo.

### Unknown behaviors / FIXME comments

Some advanced behaviors may not be recognized. Edit the keymap manually to fix these.

## What Gets Exported

- ✓ All layers with their names
- ✓ All key bindings
- ✓ Layer switches (mo, to, tog, lt)
- ✓ Modifiers (mt, sk)
- ✓ Bluetooth controls
- ✓ Output selection
- ✓ Special keys (trans, reset, etc.)

## Example Output

The export creates JSON like:

```json
{
  "device": {
    "name": "Toucan"
  },
  "layers": [
    {
      "name": "BASE",
      "bindings": [
        {"behavior": {"type": "KeyPress", "raw": "KeyPress(...)"}},
        ...
      ]
    }
  ]
}
```

The converter transforms this to:

```c
base {
    display-name = "BASE";
    bindings = <
        &kp Q  &kp W  &kp E  ...
    >;
};
```

## Need Help?

See the full documentation in `README_EXPORT.md` for:
- Detailed troubleshooting
- Advanced options
- How it works under the hood
- Supported behaviors

## That's It!

You now have a way to export your ZMK Studio configuration and save it permanently in your firmware. Run the export whenever you make changes in Studio, and your keymap will stay in sync with your firmware source code.
