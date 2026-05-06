#!/usr/bin/env python3
"""
Convert ZMK Studio JSON export to devicetree keymap format.

Usage:
    python zmk_studio_to_keymap.py <studio_export.json> [output_keymap.keymap]
    
If output file is not specified, updates config/toucan.keymap by default.
"""

import json
import sys
import re
from typing import Dict, List, Any, Optional


# HID Usage to ZMK keycode mapping
HID_TO_ZMK = {
    # Letters (0x04-0x1D)
    0x04: 'A', 0x05: 'B', 0x06: 'C', 0x07: 'D', 0x08: 'E', 0x09: 'F', 0x0A: 'G',
    0x0B: 'H', 0x0C: 'I', 0x0D: 'J', 0x0E: 'K', 0x0F: 'L', 0x10: 'M', 0x11: 'N',
    0x12: 'O', 0x13: 'P', 0x14: 'Q', 0x15: 'R', 0x16: 'S', 0x17: 'T', 0x18: 'U',
    0x19: 'V', 0x1A: 'W', 0x1B: 'X', 0x1C: 'Y', 0x1D: 'Z',
    
    # Numbers (0x1E-0x27)
    0x1E: 'N1', 0x1F: 'N2', 0x20: 'N3', 0x21: 'N4', 0x22: 'N5',
    0x23: 'N6', 0x24: 'N7', 0x25: 'N8', 0x26: 'N9', 0x27: 'N0',
    
    # Special keys
    0x28: 'RET', 0x29: 'ESC', 0x2A: 'BSPC', 0x2B: 'TAB', 0x2C: 'SPACE',
    0x2D: 'MINUS', 0x2E: 'EQUAL', 0x2F: 'LBKT', 0x30: 'RBKT', 0x31: 'BSLH',
    0x33: 'SEMI', 0x34: 'SQT', 0x35: 'GRAVE', 0x36: 'COMMA', 0x37: 'DOT',
    0x38: 'FSLH', 0x39: 'CAPS',
    
    # Function keys (0x3A-0x45)
    0x3A: 'F1', 0x3B: 'F2', 0x3C: 'F3', 0x3D: 'F4', 0x3E: 'F5', 0x3F: 'F6',
    0x40: 'F7', 0x41: 'F8', 0x42: 'F9', 0x43: 'F10', 0x44: 'F11', 0x45: 'F12',
    
    # Special function keys
    0x46: 'PSCRN', 0x47: 'SLCK', 0x48: 'PAUSE_BREAK', 0x49: 'INS',
    0x4A: 'HOME', 0x4B: 'PG_UP', 0x4C: 'DEL', 0x4D: 'END', 0x4E: 'PG_DN',
    
    # Arrows (0x4F-0x52)
    0x4F: 'RIGHT', 0x50: 'LEFT', 0x51: 'DOWN', 0x52: 'UP',
    
    # Numpad
    0x53: 'KP_NUM', 0x54: 'KP_DIVIDE', 0x55: 'KP_MULTIPLY', 0x56: 'KP_MINUS',
    0x57: 'KP_PLUS', 0x58: 'KP_ENTER', 0x59: 'KP_N1', 0x5A: 'KP_N2',
    0x5B: 'KP_N3', 0x5C: 'KP_N4', 0x5D: 'KP_N5', 0x5E: 'KP_N6',
    0x5F: 'KP_N7', 0x60: 'KP_N8', 0x61: 'KP_N9', 0x62: 'KP_N0',
    0x63: 'KP_DOT',
    
    # Additional keys
    0x54: 'KP_DIVIDE',  # Keypad /
    0x55: 'KP_MULTIPLY',  # Keypad * (85 decimal)
    0x56: 'KP_MINUS',  # Keypad - (86 decimal)
    0x57: 'KP_PLUS',  # Keypad + (87 decimal)
    0x58: 'KP_EQUAL',  # Keypad = (88 decimal)
    0x59: 'KP_N1',  # Keypad 1 (89 decimal)
    0x5A: 'KP_N2',  # Keypad 2 (90 decimal)
    0x5B: 'KP_N3',  # Keypad 3 (91 decimal)
    0x5C: 'KP_N4',  # Keypad 4 (92 decimal)
    0x5D: 'KP_N5',  # Keypad 5 (93 decimal)
    0x5E: 'KP_N6',  # Keypad 6 (94 decimal)
    0x5F: 'KP_N7',  # Keypad 7 (95 decimal)
    0x60: 'KP_N8',  # Keypad 8 (96 decimal)
    0x61: 'KP_N9',  # Keypad 9 (97 decimal)
    0x63: 'KP_DOT',  # Keypad . (99 decimal)
    0x65: 'K_APP',  # Application/Menu
    0x67: 'KP_EQUAL',  # Keypad = (103 decimal)
    0x7F: 'C_MUTE',  # Mute (127 - note: this is consumer, not keyboard)
    0x80: 'C_VOL_UP',  # Volume Up (128 - consumer)
    0x81: 'C_VOL_DN',  # Volume Down (129 - consumer)
    0xB6: 'C_AL_CALC',  # Calculator (182 decimal - consumer)
    0xB7: 'C_AL_FILES',  # My Computer/Files (183 decimal - consumer)
    0xBB: 'C_AL_EMAIL',  # Mail (187 decimal - consumer)
    0xC7: 'C_AL_LOCK',  # Lock Screen (199 decimal - consumer)
    
    # Modifiers (0xE0-0xE7)
    0xE0: 'LCTRL', 0xE1: 'LSHFT', 0xE2: 'LALT', 0xE3: 'LGUI',
    0xE4: 'RCTRL', 0xE5: 'RSHFT', 0xE6: 'RALT', 0xE7: 'RGUI',
}

# Consumer page keycodes (0x000C0000 | usage)
CONSUMER_USAGE_TO_ZMK = {
    0xB5: 'C_NEXT',
    0xB6: 'C_PREV',
    0xB7: 'C_STOP',
    0xB8: 'C_EJECT',
    0xCD: 'C_PP',      # Play/Pause
    0xE2: 'C_MUTE',
    0xE9: 'C_VOL_UP',
    0xEA: 'C_VOL_DN',
    0x6F: 'C_BRI_UP',
    0x70: 'C_BRI_DN',
    # Application launch codes
    0x183: 'C_AL_FILES',   # My Computer (183 hex = 387 decimal)
    0x18A: 'C_AL_EMAIL',   # Mail (18A hex = 394 decimal)
    0x192: 'C_AL_CALC',    # Calculator (192 hex = 402 decimal)
    0x19E: 'C_AL_LOCK',    # Lock (19E hex = 414 decimal)
}

def parse_hid_usage(hid_str: str) -> Optional[str]:
    """Parse HidUsage string and return ZMK keycode."""
    # Format: "HidUsage { page: N, id: N, modifiers: N }"
    
    # Extract the id value (this is the HID usage code)
    id_match = re.search(r'\bid:\s*(\d+)', hid_str)
    page_match = re.search(r'\bpage:\s*(\d+)', hid_str)
    
    if not id_match:
        return None
    
    usage_id = int(id_match.group(1))
    
    # Check page (default is keyboard page 7)
    if page_match:
        page = int(page_match.group(1))
        if page == 12:  # Consumer page
            return CONSUMER_USAGE_TO_ZMK.get(usage_id)
    
    # Keyboard page (page 7 or default)
    return HID_TO_ZMK.get(usage_id)


def parse_behavior_string(behavior_str: str) -> str:
    """Parse a Behavior string representation and convert to ZMK binding."""
    behavior_str = behavior_str.strip()
    
    # Strip "Behavior(" wrapper if present
    if behavior_str.startswith("Behavior(") and behavior_str.endswith(")"):
        behavior_str = behavior_str[9:-1]  # Remove "Behavior(" and ")"
    
    # Handle simple cases
    if behavior_str == "Transparent":
        return "&trans"
    if behavior_str == "None":
        return "&none"
    if behavior_str == "Reset":
        return "&sys_reset"
    if behavior_str == "Bootloader":
        return "&bootloader"
    if behavior_str == "SoftOff":
        return "&soft_off"
    if behavior_str == "StudioUnlock":
        return "&studio_unlock"
    if behavior_str == "CapsWord":
        return "&caps_word"
    if behavior_str == "KeyRepeat":
        return "&key_repeat"
    if behavior_str == "GraveEscape":
        return "&gresc"
    
    # KeyPress
    if behavior_str.startswith("KeyPress("):
        hid_match = re.search(r'KeyPress\((.*?)\)', behavior_str, re.DOTALL)
        if hid_match:
            hid_str = hid_match.group(1)
            keycode = parse_hid_usage(hid_str)
            if keycode:
                return f"&kp {keycode}"
    
    # KeyToggle
    if behavior_str.startswith("KeyToggle("):
        hid_match = re.search(r'KeyToggle\((.*?)\)', behavior_str, re.DOTALL)
        if hid_match:
            hid_str = hid_match.group(1)
            keycode = parse_hid_usage(hid_str)
            if keycode:
                return f"&kt {keycode}"
    
    # MomentaryLayer
    mo_match = re.search(r'MomentaryLayer\s*\{\s*layer_id:\s*(\d+)', behavior_str)
    if mo_match:
        layer_id = mo_match.group(1)
        return f"&mo {layer_id}"
    
    # ToggleLayer
    tg_match = re.search(r'ToggleLayer\s*\{\s*layer_id:\s*(\d+)', behavior_str)
    if tg_match:
        layer_id = tg_match.group(1)
        return f"&tog {layer_id}"
    
    # ToLayer
    to_match = re.search(r'ToLayer\s*\{\s*layer_id:\s*(\d+)', behavior_str)
    if to_match:
        layer_id = to_match.group(1)
        return f"&to {layer_id}"
    
    # StickyLayer
    sl_match = re.search(r'StickyLayer\s*\{\s*layer_id:\s*(\d+)', behavior_str)
    if sl_match:
        layer_id = sl_match.group(1)
        return f"&sl {layer_id}"
    
    # StickyKey
    if behavior_str.startswith("StickyKey("):
        hid_match = re.search(r'StickyKey\((.*?)\)', behavior_str, re.DOTALL)
        if hid_match:
            hid_str = hid_match.group(1)
            keycode = parse_hid_usage(hid_str)
            if keycode:
                return f"&sk {keycode}"
    
    # LayerTap
    lt_match = re.search(r'LayerTap\s*\{\s*layer_id:\s*(\d+),\s*tap:\s*(.*?)\s*\}', behavior_str, re.DOTALL)
    if lt_match:
        layer_id = lt_match.group(1)
        tap_hid = lt_match.group(2)
        keycode = parse_hid_usage(tap_hid)
        if keycode:
            return f"&lt {layer_id} {keycode}"
    
    # ModTap
    mt_match = re.search(r'ModTap\s*\{\s*hold:\s*(.*?),\s*tap:\s*(.*?)\s*\}', behavior_str, re.DOTALL)
    if mt_match:
        hold_hid = mt_match.group(1)
        tap_hid = mt_match.group(2)
        hold_key = parse_hid_usage(hold_hid)
        tap_key = parse_hid_usage(tap_hid)
        if hold_key and tap_key:
            return f"&mt {hold_key} {tap_key}"
    
    # Bluetooth
    bt_match = re.search(r'Bluetooth\s*\{\s*command:\s*(\d+),\s*value:\s*(\d+)', behavior_str)
    if bt_match:
        command = int(bt_match.group(1))
        value = int(bt_match.group(2))
        
        # BT commands (only 0-3 are valid)
        bt_commands = {
            0: 'BT_CLR',
            1: 'BT_SEL',
            2: 'BT_NXT',
            3: 'BT_PRV',
        }
        
        cmd_name = bt_commands.get(command)
        if cmd_name is None:
            # Unknown bluetooth command - just use &none
            print(f"Warning: Unknown BT command {command}, using &none")
            return '&none'
        
        if command == 1:  # BT_SEL needs a value
            return f"&bt {cmd_name} {value}"
        else:
            return f"&bt {cmd_name}"
    
    # OutputSelection
    out_match = re.search(r'OutputSelection\s*\{\s*value:\s*(\d+)', behavior_str)
    if out_match:
        value = int(out_match.group(1))
        out_commands = {0: 'OUT_USB', 1: 'OUT_BLE', 2: 'OUT_TOG'}
        return f"&out {out_commands.get(value, 'OUT_TOG')}"
    
    # ExternalPower
    ep_match = re.search(r'ExternalPower\s*\{\s*value:\s*(\d+)', behavior_str)
    if ep_match:
        value = int(ep_match.group(1))
        ep_commands = {0: 'EP_OFF', 1: 'EP_ON', 2: 'EP_TOG'}
        return f"&ext_power {ep_commands.get(value, 'EP_TOG')}"
    
    # MouseKeyPress
    mouse_match = re.search(r'MouseKeyPress\s*\{\s*value:\s*(\d+)', behavior_str)
    if mouse_match:
        value = int(mouse_match.group(1))
        # Mouse button values: 1=left, 2=right, 3=middle
        mouse_buttons = {1: 'MB1', 2: 'MB2', 3: 'MB3', 4: 'MB4', 5: 'MB5'}
        return f"&mkp {mouse_buttons.get(value, f'MB{value}')}"
    
    # Unknown - use transparent and warn
    print(f"Warning: Unknown behavior: {behavior_str[:60]}...")
    return "&trans"


def format_layer_bindings(bindings: List[str], keys_per_row: List[int]) -> str:
    """Format bindings with proper indentation and line breaks."""
    result = []
    index = 0
    
    for row_keys in keys_per_row:
        row_bindings = bindings[index:index + row_keys]
        # Pad bindings to align nicely (max 25 chars per binding for alignment)
        formatted_row = "                "
        for i, b in enumerate(row_bindings):
            if i == len(row_bindings) // 2 and len(keys_per_row) <= 4:
                # Add visual spacing between left and right halves
                formatted_row += "  "
            formatted_row += f"{b:22} "
        result.append(formatted_row.rstrip())
        index += row_keys
    
    return '\n'.join(result)


def convert_studio_to_keymap(studio_data: Dict[str, Any], template_keymap: str) -> str:
    """Convert ZMK Studio JSON to devicetree keymap format."""
    
    layers = studio_data.get('layers', [])
    if not layers:
        print("Warning: No layers found in export")
        return template_keymap
    
    # For the Toucan keyboard: 3 rows of 12 keys, 1 row of 6 keys (thumb keys)
    keys_per_row = [12, 12, 12, 6]
    
    print(f"\nConverting {len(layers)} layers...")
    
    # Build the new keymap content
    new_layers_content = []
    
    for layer_data in layers:
        layer_name = layer_data.get('name', f'layer_{layer_data.get("index", 0)}')
        # Clean up layer name for devicetree (no spaces, lowercase)
        layer_name = re.sub(r'[^a-z0-9_]', '_', layer_name.lower())
        
        display_name = layer_data.get('name', layer_name.upper())
        bindings_data = layer_data.get('bindings', [])
        
        print(f"  Converting layer: {display_name} ({len(bindings_data)} keys)")
        
        if not bindings_data:
            print(f"    Warning: Layer has no bindings, skipping")
            continue
        
        # Convert all bindings
        converted_bindings = []
        for binding_data in bindings_data:
            if isinstance(binding_data, dict):
                behavior = binding_data.get('behavior', {})
                behavior_str = behavior.get('raw', '')
            else:
                # Simple format
                behavior_str = str(binding_data)
            
            converted = parse_behavior_string(behavior_str)
            converted_bindings.append(converted)
        
        # Ensure we have the right number of keys
        while len(converted_bindings) < sum(keys_per_row):
            converted_bindings.append('&trans')
        
        # Format the layer
        formatted_bindings = format_layer_bindings(converted_bindings, keys_per_row)
        
        layer_content = f'''        {layer_name} {{
            display-name = "{display_name}";
            bindings = <
{formatted_bindings}
            >;
        }};'''
        
        new_layers_content.append(layer_content)
    
    # Find and replace the keymap section in the template
    # Match everything between "keymap {" and the closing "};" 
    keymap_pattern = r'(    keymap \{[^\{]*compatible = "zmk,keymap";)(.*?)(    \};)'
    
    new_keymap_section = '\n\n' + '\n\n'.join(new_layers_content) + '\n'
    
    result = re.sub(
        keymap_pattern,
        r'\1' + new_keymap_section + r'\3',
        template_keymap,
        flags=re.DOTALL
    )
    
    if result == template_keymap:
        print("\nWarning: Keymap section not found in template file")
        print("The file might not have the expected structure")
    
    return result


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nError: Please provide the ZMK Studio JSON export file")
        sys.exit(1)
    
    studio_json_path = sys.argv[1]
    
    # Determine output path
    if len(sys.argv) >= 3:
        output_keymap_path = sys.argv[2]
    else:
        output_keymap_path = 'config/toucan.keymap'
    
    # Read the studio export
    try:
        with open(studio_json_path, 'r') as f:
            studio_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Export file not found: {studio_json_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in export file: {e}")
        sys.exit(1)
    
    # Read the template keymap
    try:
        with open(output_keymap_path, 'r') as f:
            template_keymap = f.read()
    except FileNotFoundError:
        print(f"Error: Keymap file not found: {output_keymap_path}")
        print(f"Make sure you're running this from the repository root")
        sys.exit(1)
    
    # Convert
    print(f"Converting ZMK Studio export to keymap format...")
    new_keymap = convert_studio_to_keymap(studio_data, template_keymap)
    
    # Write output
    with open(output_keymap_path, 'w') as f:
        f.write(new_keymap)
    
    print(f"\n✓ Successfully updated keymap: {output_keymap_path}")
    print("\nNext steps:")
    print(f"  1. Review the changes: git diff {output_keymap_path}")
    print("  2. Check for any FIXME comments in the file")
    print("  3. Test build your firmware")
    print("  4. Flash to your keyboard")
    print("  5. Commit: git add " + output_keymap_path + " && git commit -m 'Update keymap from ZMK Studio'")

if __name__ == '__main__':
    main()
