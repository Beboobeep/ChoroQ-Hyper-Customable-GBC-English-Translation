#!/usr/bin/env python3
"""
Choro Q GBC - 3-Line Text Box Patcher
Applies all ASM patches to enable 3-line text boxes for English translation.

Usage:
    python choroq_3line_patch.py input.gbc output.gbc
"""

import sys
import os

PATCHES = [
    {
        "name": "Y Position Increment",
        "description": "Change newline Y increment from +2 to +1",
        "address": 0x48566,
        "original": bytes([0x3C, 0x3C]),  # inc a; inc a
        "patched": bytes([0x3C, 0x00]),   # inc a; nop
    },
    {
        "name": "Tile Counter Hijack",
        "description": "Redirect tile counter increment to custom code at 7D40",
        "address": 0x4849E,
        "original": bytes([0x21, 0x17, 0xC4]),  # ld hl, C417
        "patched": bytes([0xC3, 0x40, 0x7D]),   # jp 7D40
    },
    {
        "name": "Tile Counter Skip Logic",
        "description": "Skip from tile EF to FB to avoid arrow/border tiles",
        "address": 0x4BD40,
        "original": None,  # Free space, no original check
        "patched": bytes([
            0x21, 0x17, 0xC4,  # ld hl, C417
            0x34,              # inc (hl)
            0x7E,              # ld a, (hl)
            0xFE, 0xEF,        # cp a, EF
            0x20, 0x02,        # jr nz, +2 (skip to ret)
            0x36, 0xFB,        # ld (hl), FB
            0xC9,              # ret
        ]),
    },
    {
        "name": "Arrow Position",
        "description": "Move arrow marker to (X=13, Y=04) for 3-line box",
        "address": 0x483B6,
        "original": bytes([0x12, 0x03]),  # X=12, Y=03
        "patched": bytes([0x13, 0x04]),   # X=13, Y=04
    },
]


def apply_patches(input_path: str, output_path: str, verify: bool = True) -> bool:
    """
    Apply all 3-line text box patches to a Choro Q GBC ROM.
    
    Args:
        input_path: Path to input ROM file
        output_path: Path to output patched ROM file
        verify: If True, verify original bytes before patching
        
    Returns:
        True if successful, False otherwise
    """
    # Read ROM
    try:
        with open(input_path, 'rb') as f:
            rom = bytearray(f.read())
    except FileNotFoundError:
        print(f"Error: Input file '{input_path}' not found.")
        return False
    except Exception as e:
        print(f"Error reading input file: {e}")
        return False
    
    print(f"Loaded ROM: {len(rom)} bytes ({len(rom) / 1024 / 1024:.2f} MB)")
    print()
    
    # Apply patches
    patches_applied = 0
    patches_skipped = 0
    
    for patch in PATCHES:
        name = patch["name"]
        desc = patch["description"]
        addr = patch["address"]
        original = patch["original"]
        patched = patch["patched"]
        
        print(f"[{name}]")
        print(f"  Description: {desc}")
        print(f"  Address: 0x{addr:05X}")
        
        # Check ROM size
        if addr + len(patched) > len(rom):
            print(f"  ERROR: Address 0x{addr:05X} is beyond ROM size!")
            return False
        
        # Get current bytes
        current = bytes(rom[addr:addr + len(patched)])
        
        # Verify original bytes if specified
        if verify and original is not None:
            current_check = bytes(rom[addr:addr + len(original)])
            if current_check == patched[:len(original)]:
                print(f"  Status: Already patched, skipping")
                patches_skipped += 1
                print()
                continue
            elif current_check != original:
                print(f"  WARNING: Original bytes don't match!")
                print(f"    Expected: {original.hex(' ').upper()}")
                print(f"    Found:    {current_check.hex(' ').upper()}")
                print(f"  Applying patch anyway...")
        
        # Apply patch
        rom[addr:addr + len(patched)] = patched
        
        print(f"  Patched: {patched.hex(' ').upper()}")
        patches_applied += 1
        print()
    
    # Write output
    try:
        with open(output_path, 'wb') as f:
            f.write(rom)
    except Exception as e:
        print(f"Error writing output file: {e}")
        return False
    
    print("=" * 50)
    print(f"Patches applied: {patches_applied}")
    print(f"Patches skipped (already applied): {patches_skipped}")
    print(f"Output written to: {output_path}")
    print()
    
    return True


def verify_patches(rom_path: str) -> bool:
    """
    Verify that all patches have been applied to a ROM.
    
    Args:
        rom_path: Path to ROM file to verify
        
    Returns:
        True if all patches are applied, False otherwise
    """
    try:
        with open(rom_path, 'rb') as f:
            rom = f.read()
    except FileNotFoundError:
        print(f"Error: File '{rom_path}' not found.")
        return False
    
    print(f"Verifying patches in: {rom_path}")
    print()
    
    all_applied = True
    
    for patch in PATCHES:
        name = patch["name"]
        addr = patch["address"]
        patched = patch["patched"]
        
        current = rom[addr:addr + len(patched)]
        
        if current == patched:
            status = "✓ Applied"
        else:
            status = "✗ NOT applied"
            all_applied = False
        
        print(f"  {name}: {status}")
    
    print()
    return all_applied


def print_usage():
    print("Choro Q GBC - 3-Line Text Box Patcher")
    print()
    print("Usage:")
    print("  python choroq_3line_patch.py <input.gbc> <output.gbc>  - Apply patches")
    print("  python choroq_3line_patch.py --verify <rom.gbc>        - Verify patches")
    print("  python choroq_3line_patch.py --info                    - Show patch info")
    print()


def print_patch_info():
    print("Choro Q GBC - 3-Line Text Box Patches")
    print("=" * 50)
    print()
    
    for patch in PATCHES:
        print(f"[{patch['name']}]")
        print(f"  Description: {patch['description']}")
        print(f"  Address: 0x{patch['address']:05X}")
        if patch['original']:
            print(f"  Original: {patch['original'].hex(' ').upper()}")
        print(f"  Patched:  {patch['patched'].hex(' ').upper()}")
        print()
    
    print("Summary:")
    print("  - Enables 3 lines of text (Y=01, Y=02, Y=03)")
    print("  - Provides 30 character tiles (D5-EE + FB-FE)")
    print("  - Moves arrow marker to (X=13, Y=04)")
    print()


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    if sys.argv[1] == "--info":
        print_patch_info()
        sys.exit(0)
    
    if sys.argv[1] == "--verify":
        if len(sys.argv) < 3:
            print("Error: --verify requires a ROM path")
            print_usage()
            sys.exit(1)
        success = verify_patches(sys.argv[2])
        sys.exit(0 if success else 1)
    
    if len(sys.argv) < 3:
        print("Error: Both input and output paths required")
        print_usage()
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    if input_path == output_path:
        print("Error: Input and output paths must be different")
        sys.exit(1)
    
    success = apply_patches(input_path, output_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
