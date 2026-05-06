#!/usr/bin/env python3
"""
Export ZMK keymap from keyboard via ZMK Studio RPC protocol.

This script connects to your keyboard over USB (or Bluetooth) and extracts 
the current keymap configuration, saving it as JSON that can then be converted 
to .keymap format using zmk_studio_to_keymap.py.

Requirements:
    pip install zmk-studio-api

Usage:
    # Auto-detect serial port
    python export_zmk_keymap.py

    # Specify serial port
    python export_zmk_keymap.py --port /dev/ttyACM0

    # Use Bluetooth
    python export_zmk_keymap.py --ble

    # Specify output file
    python export_zmk_keymap.py --output my_keymap.json
"""

import argparse
import json
import sys
from typing import Any, Dict, List

try:
    import zmk_studio_api as zmk
except ImportError:
    print("Error: zmk-studio-api is required")
    print("Install with: pip install zmk-studio-api")
    sys.exit(1)


def find_serial_ports() -> List[str]:
    """Find available serial ports."""
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    except ImportError:
        print("Warning: pyserial not found, cannot auto-detect ports")
        return []


def behavior_to_dict(behavior) -> Dict[str, Any]:
    """Convert a Behavior object to a dictionary."""
    # Get the string representation
    behavior_str = str(behavior)
    
    # The behavior is returned as a typed Python enum/object
    # Format it for JSON serialization
    result = {
        "type": type(behavior).__name__,
        "raw": behavior_str
    }
    
    return result


def export_keymap(client: zmk.StudioClient, include_raw: bool = False) -> Dict[str, Any]:
    """Export the full keymap from the keyboard."""
    print("Getting lock state...")
    lock_state = client.get_lock_state()
    print(f"Lock state: {lock_state}")
    
    if str(lock_state) == "LockState.Locked":
        print("\n⚠️  Warning: Device is locked!")
        print("You may need to unlock it in ZMK Studio first.")
        print("Look for the 'studio_unlock' key on your keyboard or unlock via the UI.")
    
    print("\nFetching keymap (this may take a moment)...")
    # Get raw keymap bytes and parse manually
    keymap_bytes = client.get_keymap_bytes()
    print(f"Received {len(keymap_bytes)} bytes of keymap data")
    
    # Try to parse the keymap structure
    # For now, we'll get layer count by querying individual keys
    # The Toucan has 42 keys per layer
    num_keys = 42
    layers = []
    layer_idx = 0
    
    print("\nDetecting layers...")
    while True:
        try:
            # Try to get the first key of this layer to see if it exists
            behavior = client.get_key_at(layer_idx, 0)
            print(f"  Layer {layer_idx} found")
            layer_idx += 1
        except Exception as e:
            if "invalid" in str(e).lower() or "layer" in str(e).lower():
                break
            else:
                print(f"  Error checking layer {layer_idx}: {e}")
                break
    
    num_layers = layer_idx
    print(f"\nFound {num_layers} layers")
    
    # Build the export data
    export_data = {
        "device": {
            "name": "ZMK Keyboard",
        },
        "layers": []
    }
    
    # Export each layer
    for layer_idx in range(num_layers):
        print(f"  Exporting layer {layer_idx}...")
        
        layer_data = {
            "id": layer_idx,
            "name": f"Layer {layer_idx}",
            "index": layer_idx,
            "bindings": []
        }
        
        # Get each key in the layer
        for key_pos in range(num_keys):
            try:
                behavior = client.get_key_at(layer_idx, key_pos)
                binding = {
                    "position": key_pos,
                    "behavior": behavior_to_dict(behavior)
                }
                layer_data["bindings"].append(binding)
            except Exception as e:
                print(f"    Warning: Could not get key at position {key_pos}: {e}")
                binding = {
                    "position": key_pos,
                    "behavior": {"type": "Unknown", "raw": "Transparent"}
                }
                layer_data["bindings"].append(binding)
        
        export_data["layers"].append(layer_data)
    
    # Optionally include raw data
    if include_raw:
        print("\nFetching raw data...")
        export_data["_raw"] = {
            "keymap_bytes": keymap_bytes.hex(),
            "layouts_bytes": client.get_physical_layouts_bytes().hex(),
        }
    
    print(f"\n✓ Successfully exported {len(export_data['layers'])} layers")
    return export_data


def convert_to_zmk_format(export_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert the export format to a structure more compatible with 
    zmk_studio_to_keymap.py converter.
    """
    layers = []
    
    for layer_data in export_data["layers"]:
        layer = {
            "name": layer_data["name"],
            "bindings": []
        }
        
        # Convert bindings
        for binding_data in layer_data["bindings"]:
            behavior = binding_data["behavior"]
            behavior_str = behavior.get("raw", "")
            
            # Parse the behavior into a simpler format
            # This is a simplified conversion - the full version would be in zmk_studio_to_keymap.py
            layer["bindings"].append(behavior_str)
        
        layers.append(layer)
    
    return {
        "device": export_data["device"],
        "layers": layers
    }


def main():
    parser = argparse.ArgumentParser(
        description="Export ZMK keymap from keyboard via ZMK Studio RPC"
    )
    parser.add_argument(
        '--port', '-p',
        help='Serial port (e.g., /dev/ttyACM0 or COM3)'
    )
    parser.add_argument(
        '--ble', '-b',
        action='store_true',
        help='Use Bluetooth instead of serial'
    )
    parser.add_argument(
        '--output', '-o',
        default='zmk_keymap_export.json',
        help='Output JSON file (default: zmk_keymap_export.json)'
    )
    parser.add_argument(
        '--raw',
        action='store_true',
        help='Include raw protobuf bytes in export'
    )
    parser.add_argument(
        '--format',
        choices=['full', 'simple'],
        default='full',
        help='Output format: full (detailed) or simple (for converter)'
    )
    
    args = parser.parse_args()
    
    # Connect to keyboard
    try:
        if args.ble:
            print("Scanning for Bluetooth devices...")
            devices = zmk.StudioClient.list_ble_devices()
            if not devices:
                print("Error: No Bluetooth keyboards found")
                print("Make sure your keyboard is:")
                print("  1. Paired with your computer")
                print("  2. Connected (not just paired)")
                print("  3. Has ZMK Studio enabled (CONFIG_ZMK_STUDIO=y)")
                sys.exit(1)
            
            device_id, local_name = devices[0]
            print(f"Connecting to: {local_name or device_id}")
            client = zmk.StudioClient.open_ble(device_id)
        else:
            # Serial connection
            port = args.port
            if not port:
                # Try to auto-detect
                ports = find_serial_ports()
                if not ports:
                    print("Error: No serial ports found")
                    print("Please specify --port or check your connection")
                    sys.exit(1)
                
                if len(ports) == 1:
                    port = ports[0]
                    print(f"Auto-detected port: {port}")
                else:
                    print("Multiple serial ports found:")
                    for i, p in enumerate(ports):
                        print(f"  {i+1}. {p}")
                    print("\nPlease specify which port to use with --port")
                    sys.exit(1)
            
            print(f"Connecting to {port}...")
            client = zmk.StudioClient.open_serial(port)
        
    except Exception as e:
        print(f"Error connecting to keyboard: {e}")
        print("\nMake sure:")
        print("  1. Your keyboard is connected via USB (or paired via Bluetooth)")
        print("  2. ZMK Studio is enabled in your firmware (CONFIG_ZMK_STUDIO=y)")
        print("  3. You have permission to access the port")
        print("     On Linux: sudo usermod -a -G dialout $USER (then log out/in)")
        sys.exit(1)
    
    # Export the keymap
    try:
        export_data = export_keymap(client, include_raw=args.raw)
        
        # Convert format if requested
        if args.format == 'simple':
            export_data = convert_to_zmk_format(export_data)
        
        # Save to file
        with open(args.output, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\n✓ Exported keymap to: {args.output}")
        print("\nNext steps:")
        print(f"  1. Review the export: cat {args.output}")
        print(f"  2. Convert to keymap: python zmk_studio_to_keymap.py {args.output}")
        print("  3. Review changes: git diff config/toucan.keymap")
        print("  4. Build and flash your firmware")
        
    except Exception as e:
        print(f"\nError exporting keymap: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
