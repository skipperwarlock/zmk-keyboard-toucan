# Export ZMK Studio Keymap

Tools to export your ZMK Studio keymap configuration and save it to your firmware.

## The Problem

ZMK Studio stores your keymap in the keyboard's persistent storage. When you flash new firmware, those changes are lost unless they're saved in your `config/toucan.keymap` file. ZMK Studio doesn't have a built-in export feature yet.

## The Solution

These tools connect to your keyboard via USB (or Bluetooth) and extract the keymap directly using the ZMK Studio RPC protocol.

## Installation

```bash
pip install zmk-studio-api
```

## Usage

### Step 1: Export from Keyboard

Connect your keyboard and run:

```bash
# Auto-detect serial port
python export_zmk_keymap.py

# Or specify the port
python export_zmk_keymap.py --port /dev/ttyACM0

# On Windows
python export_zmk_keymap.py --port COM3

# Or use Bluetooth
python export_zmk_keymap.py --ble
```

This creates `zmk_keymap_export.json` with your current keymap.

### Step 2: Convert to Keymap Format

```bash
python zmk_studio_to_keymap.py zmk_keymap_export.json
```

This updates `config/toucan.keymap` with your exported configuration.

### Step 3: Review and Commit

```bash
# Check what changed
git diff config/toucan.keymap

# Commit the changes
git add config/toucan.keymap
git commit -m "Update keymap from ZMK Studio"
```

### Step 4: Build and Flash

Build your firmware (via GitHub Actions or locally) and flash to your keyboard. Your ZMK Studio configuration is now permanent!

## Troubleshooting

### "No serial ports found" or Connection Error

**Check your connection:**
- Make sure your keyboard is connected via USB
- Try a different USB cable or port
- On Linux, you may need permissions:
  ```bash
  sudo usermod -a -G dialout $USER
  # Then log out and back in
  ```

**Check ZMK Studio is enabled:**
Your firmware must have ZMK Studio enabled. Check your config files for:
```
CONFIG_ZMK_STUDIO=y
```

### "Device is locked"

If the export tool reports the device is locked, you need to unlock it first:

1. In ZMK Studio UI, unlock the keyboard, OR
2. Press the `studio_unlock` key on your keyboard (if you have one configured)

The unlock is usually on a hidden layer to prevent accidental keymap changes.

### "Unknown behavior" warnings

The converter may not recognize some advanced behaviors. These will be marked with FIXME comments in the keymap file. You can manually edit these after conversion.

## Advanced Options

### Export Options

```bash
# Save to custom file
python export_zmk_keymap.py --output my_export.json

# Include raw protocol data (for debugging)
python export_zmk_keymap.py --raw

# Use simple format (less detailed)
python export_zmk_keymap.py --format simple
```

### Convert to Different File

```bash
# Convert to a different keymap file
python zmk_studio_to_keymap.py export.json boards/shields/toucan/toucan.keymap
```

## How It Works

1. **`export_zmk_keymap.py`** uses the `zmk-studio-api` library to:
   - Connect to your keyboard via USB or Bluetooth
   - Query the ZMK Studio RPC protocol
   - Export all layers with their names and key bindings
   - Save as JSON

2. **`zmk_studio_to_keymap.py`** processes the JSON:
   - Parses behavior descriptions (KeyPress, MomentaryLayer, etc.)
   - Converts HID usage codes to ZMK keycodes
   - Formats as devicetree syntax
   - Updates your keymap file

## Supported Behaviors

The converter handles most common ZMK behaviors:

- **Key Press:** `&kp KEY`
- **Layer controls:** `&mo`, `&to`, `&tog`, `&lt`
- **Modifiers:** `&mt`, `&sk`
- **Bluetooth:** `&bt BT_CLR`, `&bt BT_SEL N`
- **Output:** `&out OUT_USB`, `&out OUT_BLE`
- **Special:** `&trans`, `&none`, `&sys_reset`, `&bootloader`
- **And more...**

Unknown behaviors are marked with FIXME comments for manual review.

## Example Workflow

```bash
# 1. Make changes in ZMK Studio (experiment freely!)

# 2. When happy with your layout, export it:
python export_zmk_keymap.py

# 3. Convert to keymap format:
python zmk_studio_to_keymap.py zmk_keymap_export.json

# 4. Review the changes:
git diff config/toucan.keymap

# 5. Commit and build:
git add config/toucan.keymap
git commit -m "Add media keys and adjust nav layer"
git push

# 6. Flash the updated firmware to your keyboard
```

Now your ZMK Studio changes are saved in your firmware and version control!

## Tips

- **Start small:** Export and test frequently when making changes
- **Use git:** Commit your working keymap before making big changes
- **Check for FIXMEs:** Review any behaviors the converter couldn't recognize
- **Keep in sync:** Re-export whenever you make changes in ZMK Studio

## Requirements

- Python 3.7+
- `zmk-studio-api` library
- ZMK firmware with Studio enabled (`CONFIG_ZMK_STUDIO=y`)
- USB or Bluetooth connection to your keyboard

## Credits

- Uses [zmk-studio-api](https://github.com/srwi/zmk-studio-api) by Stephan Rumswinkel
- Based on [ZMK Studio RPC Protocol](https://zmk.dev/docs/development/studio-rpc-protocol)

## Future

When ZMK Studio adds native export functionality, these tools won't be necessary. Track progress: https://github.com/zmkfirmware/zmk-studio/issues/124
