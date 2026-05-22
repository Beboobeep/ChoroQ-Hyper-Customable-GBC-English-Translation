#!/usr/bin/env python3
"""
Choro Q - Hyper Customable GB
UNIFIED REINSERTION TOOL (Code Hacks + Text)
==============================================

Applies ALL patches to a clean ROM in one pass:
  Phase 1: ASM/Code Hacks (must run first)
  Phase 2: Text Reinsertion (all modules)

Code Hack Patches:
  1. Dialogue Arrow Relocation - Moves ▼ arrow for 3-line text boxes
  2. 3-Line Dialogue Text - Enables 3 lines instead of 2
  3. List Menu Part Text Relocation - Adjusts part description positioning
  4. Lower Shop Price Text Removal - Removes redundant price display
  5. MODS Menu Part Category Removal - Removes category prefix
  6. Shop Item Graphic Relocation - Moves item preview graphic
  7. Upper Shop Text Relocation - Repositions stats/price display

Text Modules:
  1. Main dialogue (Banks 0x50-0x5A, 0x78) -> Free space 0x16B470-0x1C7FFF
  2. Part descriptions (Banks 0x27-0x29) -> Free space 0x0A5BEE-0x0BFFFF
  3. Location names (Bank 0x17) -> In-place 0x05C142-0x05C1F3
  4. Shop/Item names (Bank 0x72) -> 0x1CA200+
  5. Character names (Bank 0x1C) -> 0x0715C0+
  6. Sub-menu text (Bank 0x11) -> 0x045A00+
  7. Parts/Titles (Bank 0x12) text -> In-place
  8. Sub-locations (Bank 0x06) -> pointer + in-place

Usage: python3 choroq_reinsert_all.py [input_rom] [output_rom]
"""

import os
import re
import struct
import sys

# =============================================================================
# CONFIGURATION
# =============================================================================

INPUT_ROM = "Choro Q - Hyper Customable GB (Japan)_CleanCopy.gbc"
OUTPUT_ROM = "Choro Q - Hyper Customable GB (English).gbc"

# Translation files for each module
TRANSLATION_FILES = {
    'full_dialogue': r"C:\Users\thewo\hello\CURRENT\ONLY CURRENT EXTRACTED TXT FILES HERE\choroq_full_translation_file.txt",
    'locations': r"C:\Users\thewo\hello\CURRENT\ONLY CURRENT EXTRACTED TXT FILES HERE\choroq_location_translation.txt",
    'shop': r"C:\Users\thewo\hello\CURRENT\ONLY CURRENT EXTRACTED TXT FILES HERE\ChoroQ_Shop_Text_Dump_Translated.txt",
    'names': r"C:\Users\thewo\hello\CURRENT\ONLY CURRENT EXTRACTED TXT FILES HERE\choroq_names_translation.txt",
    'submenu': r"C:\Users\thewo\hello\CURRENT\ONLY CURRENT EXTRACTED TXT FILES HERE\choroq_submenu_translation.txt",
    'bank12': r"C:\Users\thewo\hello\CURRENT\ONLY CURRENT EXTRACTED TXT FILES HERE\choroq_bank12_inplace.txt",
    'sublocations': r"C:\Users\thewo\hello\CURRENT\ONLY CURRENT EXTRACTED TXT FILES HERE\choroq_subLocations_translation.txt",
    'title_screen': r"C:\Users\thewo\hello\CURRENT\ONLY PUT FINISHED HACKED GRAPHICS HERE\choroq_title_grayscale_ENG.bmp",
}

# Set to False to skip specific modules
MODULES_ENABLED = {
    'code_hacks': True,      # ASM patches (Phase 1)
    'full_dialogue': True,   # Main dialogue + part descriptions
    'locations': True,
    'shop': True,
    'names': True,
    'submenu': True,
    'bank12': True,
    'sublocations': True,
    'title_screen': True,    # Title screen graphic replacement
}

# =============================================================================
# CHARACTER ENCODING MAP
# =============================================================================

CHAR_TO_BYTE = {
    'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45,
    'F': 0x46, 'G': 0x47, 'H': 0x48, 'I': 0x49, 'J': 0x4A,
    'K': 0x4B, 'L': 0x4C, 'M': 0x4D, 'N': 0x4E, 'O': 0x4F,
    'P': 0x50, 'Q': 0x51, 'R': 0x52, 'S': 0x53, 'T': 0x54,
    'U': 0x55, 'V': 0x56, 'W': 0x57, 'X': 0x58, 'Y': 0x59,
    'Z': 0x5A,

    'a': 0x00, 'b': 0x01, 'c': 0x02, 'd': 0x03, 'e': 0x04,
    'f': 0x05, 'g': 0x06, 'h': 0x07, 'i': 0x08, 'j': 0x09,
    'k': 0x0A, 'l': 0x0B, 'm': 0x0C, 'n': 0x0D, 'o': 0x0E,
    'p': 0x0F, 'q': 0x10, 'r': 0x11, 's': 0x12, 't': 0x13,
    'u': 0x14, 'v': 0x15, 'w': 0x16, 'x': 0x17, 'y': 0x18,
    'z': 0x19,

    '0': 0x37, '1': 0x38, '2': 0x39, '3': 0x3A, '4': 0x3B,
    '5': 0x3C, '6': 0x3D, '7': 0x3E, '8': 0x3F, '9': 0x40,

    ' ': 0xA4, '!': 0x60, '&': 0x61, '?': 0x64, '.': 0xAC,
    ',': 0xAD, '-': 0x5C, '・': 0x5E, '♥': 0x5F, '\'': 0xA2,
    '「': 0x62, '」': 0x63, ':': 0x5C, ';': 0x5C, '(': 0xA7,
    ')': 0xA8, '[': 0x62, ']': 0x63, '/': 0xA0, '#': 0xA1,
    '*': 0xB0, '★': 0x5B, '~': 0x5D, '_': 0xA4,
}

# Control codes
CTRL_NEWLINE = 0xFE
CTRL_WAIT = 0xFC
CTRL_SECTION = 0xFD
CTRL_END = 0xFF

# Variable placeholders
VARIABLE_BYTES = {
    'E0': 0xE0, 'E1': 0xE1, 'E2': 0xE2, 'E3': 0xE3,
    'E4': 0xE4, 'E5': 0xE5, 'E6': 0xE6, 'E7': 0xE7,
    'E8': 0xE8, 'E9': 0xE9, 'EA': 0xEA, 'EB': 0xEB,
    'EC': 0xEC, 'ED': 0xED, 'EE': 0xEE, 'EF': 0xEF,
}


# =============================================================================
# PHASE 1: CODE HACKS
# =============================================================================

CODE_PATCHES = {
    "arrow_relocation": {
        "description": "Dialogue arrow position adjustment",
        "patches": [
            (0x483B6, [0x12], [0x13]),
            (0x483B7, [0x03], [0x04]),
        ]
    },

    "3line_text": {
        "description": "3-line dialogue text box support",
        "patches": [
            (0x48566, [0x3C, 0x3C], [0x3C, 0x00]),
            (0x4849E, [0x21, 0x17, 0xC4], [0xC3, 0x40, 0x7D]),
            (0x4BD40, None, [
                0x21, 0x17, 0xC4, 0x34, 0x7E, 0xFE, 0xEF,
                0x20, 0x02, 0x36, 0xFB, 0xC9
            ]),
        ]
    },

    "list_menu_text": {
        "description": "List menu part description relocation",
        "patches": [
            (0x49EEA, [0x07], [0x01]),
            (0x49EE4, [0x13], [0x09]),
        ]
    },

    "shop_price_filter": {
        "description": "Lower shop price removal and upper 'G' tile addition",
        "patches": [
            (0x49E61, [0xCD, 0xA2, 0x12], [0xC3, 0x00, 0x7D]),
            (0x4BD00, None, [
                0x7A, 0xFE, 0x5E, 0x20, 0x0C,
                0x7C, 0xFE, 0x99, 0x20, 0x12,
                0x7D, 0xFE, 0x05, 0x28, 0x0A,
                0x18, 0x0B,
                0xFE, 0x6D, 0x38, 0x04,
                0xFE, 0x78, 0x38, 0x03,
                0xCD, 0xA2, 0x12,
                0xC3, 0x64, 0x5E
            ]),
        ]
    },

    "mods_category_removal": {
        "description": "MODS menu part category text removal",
        "patches": [
            (0x48E64, [0xCD, 0x97, 0x0A, 0x36, 0xF9, 0x23, 0x36, 0x07, 0x23],
                      [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]),
        ]
    },

    "shop_graphic": {
        "description": "Shop item graphic relocation",
        "patches": [
            (0x4A109, [0x81], [0xA0]),
        ]
    },

    "shop_text_relocation": {
        "description": "Upper shop text relocation and reformatting",
        "patches": [
            (0x4A035, [0x07], [0x06]),
            (0x49FDE, [0x36, 0xF9, 0x23, 0x36, 0x13, 0x23],
                      [0x00, 0x00, 0x00, 0x00, 0x00, 0x00]),
            (0x4A00B, [0xEA, 0xD3, 0xC8], [0x00, 0x00, 0x00]),
            (0x4A010, [0x07], [0x01]),
            (0x49FBE, [0xCD, 0x34, 0x13], [0x00, 0x00, 0x00]),
            (0x49E47, [0x0E], [0x01]),
        ]
    },
}


def apply_code_hacks(rom_data):
    """Apply all ASM/code patches. Returns (applied_count, error_count)."""
    applied = 0
    errors = 0

    for patch_name, patch_info in CODE_PATCHES.items():
        print(f"  {patch_name}: {patch_info['description']}")
        patch_ok = True

        for rom_addr, expected, new_bytes in patch_info["patches"]:
            if expected is not None:
                actual = list(rom_data[rom_addr:rom_addr + len(expected)])
                if actual == new_bytes:
                    print(f"    0x{rom_addr:06X}: Already patched")
                    continue
                if actual != expected:
                    print(f"    0x{rom_addr:06X}: MISMATCH expected {expected}, found {actual}")
                    patch_ok = False
                    errors += 1
                    continue

            for i, byte in enumerate(new_bytes):
                rom_data[rom_addr + i] = byte
            print(f"    0x{rom_addr:06X}: OK ({len(new_bytes)} bytes)")

        if patch_ok:
            applied += 1

    return applied, errors


# =============================================================================
# PHASE 2: TEXT ENCODING FUNCTIONS
# =============================================================================

def encode_dialogue_text(text):
    """Encode dialogue text with full control code support."""
    result = []
    text = text.strip()

    # Normalize control markers
    text = text.replace('\n▼\n', '▼').replace('\n▼', '▼').replace('▼\n', '▼')
    text = text.replace('\n---\n', '---').replace('\n---', '---').replace('---\n', '---')
    text = text.replace('\n[END]\n', '[END]').replace('\n[END]', '[END]').replace('[END]\n', '[END]')
    text = text.replace('<STOP>', '')

    i = 0
    while i < len(text):
        face_match = re.match(r'<FACE:([0-9A-Fa-f]{2}),([0-9A-Fa-f]{2})>', text[i:])
        if face_match:
            result.extend([0xFB, int(face_match.group(1), 16), 0xFA, int(face_match.group(2), 16)])
            i += face_match.end()
            continue

        var_match = re.match(r'\[(E[0-9A-Fa-f])\]', text[i:])
        if var_match:
            var_name = var_match.group(1).upper()
            if var_name in VARIABLE_BYTES:
                result.append(VARIABLE_BYTES[var_name])
            i += var_match.end()
            continue

        if text[i:i+5] == '[END]':
            result.append(CTRL_SECTION)
            i += 5
            continue

        if text[i:i+3] == '---':
            result.append(CTRL_SECTION)
            i += 3
            continue

        if text[i] == '▼':
            result.append(CTRL_WAIT)
            i += 1
            continue

        if text[i] == '\n':
            result.append(CTRL_NEWLINE)
            i += 1
            continue

        char = text[i].upper()
        if char in CHAR_TO_BYTE:
            result.append(CHAR_TO_BYTE[char])
        else:
            print(f"    Warning: Unknown char '{text[i]}' (0x{ord(text[i]):02X})")
            result.append(0xA4)
        i += 1

    if not result or result[-1] != CTRL_END:
        result.append(CTRL_END)

    return bytes(result)


def encode_simple_string(text):
    """Encode simple string with FF terminator."""
    result = []
    i = 0
    while i < len(text):
        if text[i] == '[' and i + 3 < len(text) and text[i+3] == ']':
            var_code = text[i+1:i+3].upper()
            if var_code in VARIABLE_BYTES:
                result.append(VARIABLE_BYTES[var_code])
                i += 4
                continue

        char = text[i].upper()
        if char in CHAR_TO_BYTE:
            result.append(CHAR_TO_BYTE[char])
        else:
            result.append(0xA4)
        i += 1

    result.append(CTRL_END)
    return bytes(result)


def encode_padded_string(text, max_len):
    """Encode string with space padding to fixed length."""
    result = []
    for char in text:
        c = char.upper()
        if c in CHAR_TO_BYTE:
            result.append(CHAR_TO_BYTE[c])
        else:
            result.append(0xA4)

    while len(result) < max_len:
        result.append(0xA4)

    result.append(CTRL_END)
    return bytes(result)


# =============================================================================
# MODULE: FULL DIALOGUE (Banks 0x06, 0x27-0x29, 0x50-0x5A, 0x78)
# =============================================================================

FREE_SPACE_DIALOGUE = (0x16B470, 0x1C7FFF)
FREE_SPACE_PARTS = (0x0A5BEE, 0x0BFFFF)
DIALOGUE_BANKS = {0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x78}
PARTS_BANKS = {0x27, 0x28, 0x29}


def parse_full_translation_file(filepath):
    """Parse the unified translation file format."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    dialogue_blocks = []
    parts_blocks = []
    bank06_blocks = []

    pattern = re.compile(
        r'={80}\nTEXT BLOCK #(\d+)\n={80}\n'
        r'--- POINTER INFO ---\n'
        r'PTR_OFFSET:\s+0x([0-9A-Fa-f]+)\n'
        r'PTR_BYTES:\s+([0-9A-Fa-f ]+)\n'
        r'BANK:\s+0x([0-9A-Fa-f]+)\s+\(\d+\)\n'
        r'TEXT_CPU:\s+0x([0-9A-Fa-f]+)\n'
        r'TEXT_ROM:\s+0x([0-9A-Fa-f]+)\n'
        r'TEXT_LENGTH:\s+(\d+)\s+bytes\n'
        r'--- RAW BYTES ---\n'
        r'(.*?)\n'
        r'--- JAPANESE ---\n'
        r'(.*?)\n'
        r'---\n'
        r'--- ENGLISH TRANSLATION ---\n'
        r'(.*?)\n'
        r'---',
        re.DOTALL
    )

    for match in pattern.finditer(content):
        block_num = int(match.group(1))
        ptr_offset = int(match.group(2), 16)
        bank = int(match.group(4), 16)
        english = match.group(10).strip()

        if not english or english == '[Enter your translation here]':
            continue

        block = {
            'block_num': block_num,
            'ptr_offset': ptr_offset,
            'bank': bank,
            'english': english,
        }

        if bank in DIALOGUE_BANKS:
            dialogue_blocks.append(block)
        elif bank in PARTS_BANKS:
            parts_blocks.append(block)
        elif bank == 0x06:
            bank06_blocks.append(block)
        else:
            dialogue_blocks.append(block)

    return dialogue_blocks, parts_blocks, bank06_blocks


def reinsert_full_dialogue(rom_data, filepath):
    """Reinsert main dialogue and part descriptions."""
    if not os.path.exists(filepath):
        print(f"  Skipping: {filepath} not found")
        return 0, 0

    dialogue_blocks, parts_blocks, bank06_blocks = parse_full_translation_file(filepath)
    total_count = 0
    total_bytes = 0

    if dialogue_blocks:
        print(f"  Processing {len(dialogue_blocks)} dialogue blocks...")
        current_pos = FREE_SPACE_DIALOGUE[0]
        count = 0

        for block in dialogue_blocks:
            encoded = encode_dialogue_text(block['english'])

            if current_pos + len(encoded) > FREE_SPACE_DIALOGUE[1]:
                print(f"    ERROR: Out of space at block #{block['block_num']}")
                break

            rom_data[current_pos:current_pos + len(encoded)] = encoded

            new_bank = current_pos // 0x4000
            cpu_addr = (current_pos % 0x4000) + 0x4000

            rom_data[block['ptr_offset']] = cpu_addr & 0xFF
            rom_data[block['ptr_offset'] + 1] = (cpu_addr >> 8) & 0xFF
            rom_data[block['ptr_offset'] + 2] = new_bank

            current_pos += len(encoded)
            count += 1

        bytes_used = current_pos - FREE_SPACE_DIALOGUE[0]
        print(f"    Dialogue: {count} blocks, {bytes_used} bytes "
              f"(0x{FREE_SPACE_DIALOGUE[0]:06X}-0x{current_pos-1:06X})")
        total_count += count
        total_bytes += bytes_used

    if parts_blocks:
        print(f"  Processing {len(parts_blocks)} part description blocks...")
        current_pos = FREE_SPACE_PARTS[0]
        count = 0

        for block in parts_blocks:
            encoded = encode_dialogue_text(block['english'])

            if current_pos + len(encoded) > FREE_SPACE_PARTS[1]:
                print(f"    ERROR: Out of space at block #{block['block_num']}")
                break

            rom_data[current_pos:current_pos + len(encoded)] = encoded

            new_bank = current_pos // 0x4000
            cpu_addr = (current_pos % 0x4000) + 0x4000

            rom_data[block['ptr_offset']] = cpu_addr & 0xFF
            rom_data[block['ptr_offset'] + 1] = (cpu_addr >> 8) & 0xFF
            rom_data[block['ptr_offset'] + 2] = new_bank

            current_pos += len(encoded)
            count += 1

        bytes_used = current_pos - FREE_SPACE_PARTS[0]
        print(f"    Parts: {count} blocks, {bytes_used} bytes "
              f"(0x{FREE_SPACE_PARTS[0]:06X}-0x{current_pos-1:06X})")
        total_count += count
        total_bytes += bytes_used

    if bank06_blocks:
        print(f"  Note: {len(bank06_blocks)} bank 0x06 blocks (handled by sublocations)")

    return total_count, total_bytes


# =============================================================================
# MODULE: LOCATION NAMES (Bank 0x17)
# =============================================================================

LOC_BANK_START = 0x05C000
LOC_STRING_START = 0x05C142
LOC_STRING_END = 0x05C1F3


def parse_location_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    entries = []
    pattern = re.compile(
        r'\[ENTRY:(\d+)\]\s*\n'
        r'PTR_OFFSET:\s*0x([0-9A-Fa-f]+)\s*\n'
        r'STR_ROM:\s*0x([0-9A-Fa-f]+)\s*\n'
        r'STR_LEN:\s*(\d+)\s*\n'
        r'RAW:\s*([0-9A-Fa-f ]*)\s*\n'
        r'JAPANESE:\s*(.*?)\s*\n'
        r'ENGLISH:\s*(.*?)\s*\n'
        r'\[END\]', re.MULTILINE
    )
    for match in pattern.finditer(content):
        english = match.group(7).strip()
        if english:
            entries.append({'ptr_offset': int(match.group(2), 16), 'english': english})
    return entries


def reinsert_locations(rom_data, filepath):
    if not os.path.exists(filepath):
        print(f"  Skipping: {filepath} not found")
        return 0, 0
    entries = parse_location_file(filepath)
    if not entries:
        return 0, 0
    current_pos = LOC_STRING_START
    count = 0
    for entry in entries:
        encoded = encode_simple_string(entry['english'])
        if current_pos + len(encoded) > LOC_STRING_END + 1:
            print(f"  ERROR: Out of space in location area")
            break
        rom_data[current_pos:current_pos + len(encoded)] = encoded
        cpu_addr = (current_pos - LOC_BANK_START) + 0x4000
        rom_data[entry['ptr_offset']] = cpu_addr & 0xFF
        rom_data[entry['ptr_offset'] + 1] = (cpu_addr >> 8) & 0xFF
        current_pos += len(encoded)
        count += 1
    return count, current_pos - LOC_STRING_START


# =============================================================================
# MODULE: SHOP/ITEM NAMES (Bank 0x72)
# =============================================================================

SHOP_BANK_START = 0x1C8000
SHOP_STRING_START = 0x1CA200
SHOP_BANK_END = 0x1CBFFF


def parse_shop_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    entries = []
    pattern = re.compile(
        r'\[BLOCK:(\d+)\]\s*\n'
        r'PTR_OFFSET:\s*0x([0-9A-Fa-f]+)\s*\n'
        r'TEXT_ROM:\s*0x([0-9A-Fa-f]+)\s*\n'
        r'TEXT_CPU:\s*0x([0-9A-Fa-f]+)\s*\n'
        r'TEXT_LEN:\s*(\d+)\s*\n'
        r'RAW:\s*([0-9A-Fa-f ]*)\s*\n'
        r'JAPANESE:\s*(.*?)\s*\n'
        r'ENGLISH:\s*(.*?)\s*\n'
        r'\[END\]', re.MULTILINE
    )
    for match in pattern.finditer(content):
        english = match.group(8).strip()
        if english:
            entries.append({'ptr_offset': int(match.group(2), 16), 'english': english})
    return entries


def reinsert_shop(rom_data, filepath):
    if not os.path.exists(filepath):
        print(f"  Skipping: {filepath} not found")
        return 0, 0
    entries = parse_shop_file(filepath)
    if not entries:
        return 0, 0
    current_pos = SHOP_STRING_START
    count = 0
    for entry in entries:
        encoded = encode_simple_string(entry['english'])
        if current_pos + len(encoded) > SHOP_BANK_END:
            print(f"  ERROR: Out of space in shop area")
            break
        rom_data[current_pos:current_pos + len(encoded)] = encoded
        cpu_addr = (current_pos - SHOP_BANK_START) + 0x4000
        rom_data[entry['ptr_offset']] = cpu_addr & 0xFF
        rom_data[entry['ptr_offset'] + 1] = (cpu_addr >> 8) & 0xFF
        current_pos += len(encoded)
        count += 1
    return count, current_pos - SHOP_STRING_START


# =============================================================================
# MODULE: CHARACTER NAMES (Bank 0x1C)
# =============================================================================

NAME_BANK_START = 0x070000
NAME_STRING_START = 0x0715C0
NAME_BANK_END = 0x073FFF


def parse_name_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    entries = []
    pattern = re.compile(
        r'\[ENTRY:(\d+)\]\s*\n'
        r'PTR_OFFSET:\s*0x([0-9A-Fa-f]+)\s*\n'
        r'STR_ROM:\s*0x([0-9A-Fa-f]+)\s*\n'
        r'STR_LEN:\s*(\d+)\s*\n'
        r'RAW:\s*([0-9A-Fa-f ]*)\s*\n'
        r'JAPANESE:\s*(.*?)\s*\n'
        r'ENGLISH:\s*(.*?)\s*\n'
        r'\[END\]', re.MULTILINE
    )
    for match in pattern.finditer(content):
        english = match.group(7).strip()
        if english:
            entries.append({'ptr_offset': int(match.group(2), 16), 'english': english})
    return entries


def reinsert_names(rom_data, filepath):
    if not os.path.exists(filepath):
        print(f"  Skipping: {filepath} not found")
        return 0, 0
    entries = parse_name_file(filepath)
    if not entries:
        return 0, 0
    current_pos = NAME_STRING_START
    count = 0
    for entry in entries:
        encoded = encode_simple_string(entry['english'])
        if current_pos + len(encoded) > NAME_BANK_END:
            print(f"  ERROR: Out of space in name area")
            break
        rom_data[current_pos:current_pos + len(encoded)] = encoded
        cpu_addr = (current_pos - NAME_BANK_START) + 0x4000
        rom_data[entry['ptr_offset']] = cpu_addr & 0xFF
        rom_data[entry['ptr_offset'] + 1] = (cpu_addr >> 8) & 0xFF
        current_pos += len(encoded)
        count += 1
    return count, current_pos - NAME_STRING_START


# =============================================================================
# MODULE: SUB-MENU TEXT (Bank 0x11)
# =============================================================================

SUBMENU_BANK_START = 0x044000
SUBMENU_STRING_START = 0x045A00
SUBMENU_STRING_END = 0x047FFF


def parse_submenu_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    entries = []
    pattern = r'\[ENTRY:(\d+)\](.*?)\[END\]'
    for match in re.findall(pattern, content, re.DOTALL):
        block = match[1]
        ptr_match = re.search(r'PTR_OFFSETS:\s*(.+)', block)
        ptrs = []
        if ptr_match:
            ptr_str = ptr_match.group(1).strip()
            if ptr_str != 'NONE':
                for p in ptr_str.split(','):
                    p = p.strip()
                    if p.startswith('0x'):
                        ptrs.append(int(p, 16))
        en_match = re.search(r'ENGLISH:\s*(.+)', block)
        english = en_match.group(1).strip() if en_match else ''
        if english and ptrs:
            entries.append({'ptrs': ptrs, 'english': english})
    return entries


def reinsert_submenu(rom_data, filepath):
    if not os.path.exists(filepath):
        print(f"  Skipping: {filepath} not found")
        return 0, 0
    entries = parse_submenu_file(filepath)
    if not entries:
        return 0, 0
    current_pos = SUBMENU_STRING_START
    count = 0
    for entry in entries:
        encoded = encode_simple_string(entry['english'])
        if current_pos + len(encoded) > SUBMENU_STRING_END:
            print(f"  ERROR: Out of space in submenu area")
            break
        rom_data[current_pos:current_pos + len(encoded)] = encoded
        cpu_addr = (current_pos - SUBMENU_BANK_START) + 0x4000
        for ptr in entry['ptrs']:
            rom_data[ptr] = cpu_addr & 0xFF
            rom_data[ptr + 1] = (cpu_addr >> 8) & 0xFF
        current_pos += len(encoded)
        count += 1
    return count, current_pos - SUBMENU_STRING_START


# =============================================================================
# MODULE: BANK 0x12 IN-PLACE TEXT
# =============================================================================

def parse_bank12_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    entries = []
    pattern = r'\[ENTRY:(\d+)\](.*?)\[END\]'
    for match in re.findall(pattern, content, re.DOTALL):
        block = match[1]
        rom_match = re.search(r'STR_ROM:\s*(0x[0-9A-Fa-f]+)', block)
        len_match = re.search(r'MAX_LEN:\s*(\d+)', block)
        en_match = re.search(r'ENGLISH:\s*(.+)', block)
        if rom_match and len_match and en_match:
            english = en_match.group(1).strip()
            if english:
                entries.append({
                    'str_rom': int(rom_match.group(1), 16),
                    'max_len': int(len_match.group(1)),
                    'english': english,
                })
    return entries


def reinsert_bank12(rom_data, filepath):
    if not os.path.exists(filepath):
        print(f"  Skipping: {filepath} not found")
        return 0, 0
    entries = parse_bank12_file(filepath)
    if not entries:
        return 0, 0
    count = 0
    total_bytes = 0
    for entry in entries:
        if len(entry['english']) > entry['max_len']:
            print(f"  ERROR: '{entry['english']}' too long ({len(entry['english'])} > {entry['max_len']})")
            continue
        encoded = encode_padded_string(entry['english'], entry['max_len'])
        rom_data[entry['str_rom']:entry['str_rom'] + len(encoded)] = encoded
        count += 1
        total_bytes += len(encoded)
    return count, total_bytes


# =============================================================================
# MODULE: SUB-LOCATIONS (Bank 0x06)
# =============================================================================

SUBLOC_BANK_START = 0x018000
SUBLOC_STRING_START = 0x018480
SUBLOC_STRING_END = 0x01BFFF


def parse_subloc_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    ptr_entries = []
    inline_entries = []
    pattern = r'\[ENTRY:(\d+)\](.*?)\[END\]'
    for match in re.findall(pattern, content, re.DOTALL):
        block = match[1]
        ptr_match = re.search(r'PTR_OFFSET:\s*(\S+)', block)
        rom_match = re.search(r'STR_ROM:\s*(0x[0-9A-Fa-f]+)', block)
        len_match = re.search(r'STR_LEN:\s*(\d+)', block)
        en_match = re.search(r'ENGLISH:\s*(.+)', block)
        if not en_match:
            continue
        english = en_match.group(1).strip()
        if not english:
            continue
        ptr_offset = None
        if ptr_match:
            ptr_str = ptr_match.group(1).strip()
            if ptr_str != 'NONE':
                ptr_offset = int(ptr_str, 16)
        entry = {
            'english': english,
            'str_rom': int(rom_match.group(1), 16) if rom_match else 0,
            'str_len': int(len_match.group(1)) if len_match else 0,
        }
        if ptr_offset is not None:
            entry['ptr_offset'] = ptr_offset
            ptr_entries.append(entry)
        else:
            inline_entries.append(entry)
    return ptr_entries, inline_entries


def reinsert_sublocations(rom_data, filepath):
    if not os.path.exists(filepath):
        print(f"  Skipping: {filepath} not found")
        return 0, 0
    ptr_entries, inline_entries = parse_subloc_file(filepath)
    current_pos = SUBLOC_STRING_START
    count = 0
    total_bytes = 0
    for entry in ptr_entries:
        encoded = encode_simple_string(entry['english'])
        if current_pos + len(encoded) > SUBLOC_STRING_END:
            print(f"  ERROR: Out of space in sublocation area")
            break
        rom_data[current_pos:current_pos + len(encoded)] = encoded
        cpu_addr = (current_pos - SUBLOC_BANK_START) + 0x4000
        rom_data[entry['ptr_offset']] = cpu_addr & 0xFF
        rom_data[entry['ptr_offset'] + 1] = (cpu_addr >> 8) & 0xFF
        current_pos += len(encoded)
        count += 1
        total_bytes += len(encoded)
    for entry in inline_entries:
        if len(entry['english']) + 1 > entry['str_len']:
            print(f"  ERROR: '{entry['english']}' too long")
            continue
        encoded = encode_padded_string(entry['english'], entry['str_len'] - 1)
        rom_data[entry['str_rom']:entry['str_rom'] + len(encoded)] = encoded
        count += 1
        total_bytes += len(encoded)
    return count, total_bytes


# =============================================================================
# MODULE: TITLE SCREEN GRAPHIC
# =============================================================================

# ROM addresses for title screen
TITLE_TILES_BANK0_START = 0x090790
TITLE_TILES_BANK1_START = 0x0912E0
TITLE_TILES_SIZE = 2176  # 136 tiles x 16 bytes
TITLE_TILEMAP_START = 0x091024
TITLE_TILEMAP_ROW15 = 0x091150
TITLE_ATTRMAP_START = 0x09118C
TITLE_GRID_W = 20
TITLE_GRID_H = 18
TITLE_MAX_TILES = 136

TITLE_PALETTE_MAP = [
    #  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
    [ 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0 ],  # row 0
    [ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0 ],  # row 1
    [ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0 ],  # row 2
    [ 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0 ],  # row 3
    [ 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 ],  # row 4
    [ 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 0 ],  # row 5
    [ 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0 ],  # row 6
]


def read_bmp(filepath):
    """Read a BMP file and return (width, height, pixels)."""
    with open(filepath, 'rb') as f:
        sig = f.read(2)
        if sig != b'BM':
            raise ValueError("Not a BMP file")
        file_size = struct.unpack('<I', f.read(4))[0]
        f.read(4)
        pixel_offset = struct.unpack('<I', f.read(4))[0]
        dib_size = struct.unpack('<I', f.read(4))[0]
        width = struct.unpack('<i', f.read(4))[0]
        height = struct.unpack('<i', f.read(4))[0]
        planes = struct.unpack('<H', f.read(2))[0]
        bpp = struct.unpack('<H', f.read(2))[0]
        compression = struct.unpack('<I', f.read(4))[0]
        if compression != 0:
            raise ValueError(f"Compressed BMP not supported")
        f.seek(pixel_offset)
        top_down = height < 0
        abs_height = abs(height)

        if bpp == 24:
            row_size = ((width * 3 + 3) // 4) * 4
            pixels = []
            for y in range(abs_height):
                row_data = f.read(row_size)
                row = [(row_data[x*3+2], row_data[x*3+1], row_data[x*3]) for x in range(width)]
                pixels.append(row)
            if not top_down:
                pixels.reverse()
        elif bpp == 8:
            f.seek(14 + dib_size)
            palette = []
            for _ in range(256):
                b, g, r, _ = struct.unpack('BBBB', f.read(4))
                palette.append((r, g, b))
            f.seek(pixel_offset)
            row_size = ((width + 3) // 4) * 4
            pixels = []
            for y in range(abs_height):
                row_data = f.read(row_size)
                pixels.append([palette[row_data[x]] for x in range(width)])
            if not top_down:
                pixels.reverse()
        elif bpp == 32:
            pixels = []
            for y in range(abs_height):
                row_data = f.read(width * 4)
                pixels.append([(row_data[x*4+2], row_data[x*4+1], row_data[x*4]) for x in range(width)])
            if not top_down:
                pixels.reverse()
        else:
            raise ValueError(f"Unsupported BMP bit depth: {bpp}")

    return width, height if top_down else abs_height, pixels


def reinsert_title_screen(rom_data, filepath):
    """Reinsert title screen graphic from a 160x144 4-color grayscale BMP."""
    if not os.path.exists(filepath):
        print(f"  Skipping: {filepath} not found")
        return 0, 0

    width, height, pixels = read_bmp(filepath)
    if width != 160 or height != 144:
        print(f"  ERROR: Image must be 160x144, got {width}x{height}")
        return 0, 0

    # Map colors to indices (lightest=0, darkest=3)
    unique = set()
    for row in pixels:
        for c in row:
            unique.add(c)

    sorted_colors = sorted(unique, key=lambda c: c[0]+c[1]+c[2], reverse=True)
    if len(sorted_colors) <= 4:
        color_map = {c: i for i, c in enumerate(sorted_colors)}
    else:
        def nearest_idx(c):
            b = (c[0]+c[1]+c[2]) / (255*3)
            if b > 0.75: return 0
            elif b > 0.50: return 1
            elif b > 0.25: return 2
            else: return 3
        color_map = {c: nearest_idx(c) for c in unique}

    indices = [[color_map[pixels[y][x]] for x in range(160)] for y in range(144)]

    # Extract tiles with deduplication
    tile_set = []
    tile_lookup = {}
    tilemap = []

    for ty in range(TITLE_GRID_H):
        row = []
        for tx in range(TITLE_GRID_W):
            tile = tuple(indices[ty*8+py][tx*8+px] for py in range(8) for px in range(8))
            # Encode to 2bpp
            data = bytearray(16)
            for r in range(8):
                lo = hi = 0
                for bit in range(8):
                    color = tile[r*8+bit]
                    if color & 1: lo |= (1 << (7-bit))
                    if color & 2: hi |= (1 << (7-bit))
                data[r*2] = lo
                data[r*2+1] = hi
            encoded = bytes(data)

            if encoded in tile_lookup:
                row.append(tile_lookup[encoded])
            else:
                idx = len(tile_set)
                tile_set.append(encoded)
                tile_lookup[encoded] = idx
                row.append(idx)
        tilemap.append(row)

    print(f"  Unique tiles: {len(tile_set)} / {TITLE_MAX_TILES}")

    if len(tile_set) > TITLE_MAX_TILES:
        print(f"  ERROR: Too many unique tiles ({len(tile_set)} > {TITLE_MAX_TILES})")
        return 0, 0

    # Pad to 136 tiles
    blank = bytes(16)
    while len(tile_set) < TITLE_MAX_TILES:
        tile_set.append(blank)

    # Build tile ROM data
    tile_rom_data = bytearray()
    for tile in tile_set:
        tile_rom_data.extend(tile)

    # Write tiles to both VRAM banks
    rom_data[TITLE_TILES_BANK0_START:TITLE_TILES_BANK0_START + TITLE_TILES_SIZE] = tile_rom_data
    rom_data[TITLE_TILES_BANK1_START:TITLE_TILES_BANK1_START + TITLE_TILES_SIZE] = tile_rom_data
    print(f"  Wrote tiles Bank 0+1: {TITLE_TILES_SIZE} bytes each")

    # Write tilemap rows 0-7
    for row in range(8):
        for col in range(TITLE_GRID_W):
            rom_data[TITLE_TILEMAP_START + row * TITLE_GRID_W + col] = tilemap[row][col]
    print(f"  Wrote tilemap rows 0-7: 0x{TITLE_TILEMAP_START:06X}")

    # Write tilemap row 15
    for col in range(TITLE_GRID_W):
        rom_data[TITLE_TILEMAP_ROW15 + col] = tilemap[15][col]
    print(f"  Wrote tilemap row 15: 0x{TITLE_TILEMAP_ROW15:06X}")

    # Write attribute map rows 0-6
    new_attrmap = bytearray()
    for row in TITLE_PALETTE_MAP:
        for val in row:
            new_attrmap.append(val)
    rom_data[TITLE_ATTRMAP_START:TITLE_ATTRMAP_START + len(new_attrmap)] = new_attrmap

    pal_counts = [0, 0, 0]
    for b in new_attrmap:
        if b < 3: pal_counts[b] += 1
    print(f"  Attribute map: pal0={pal_counts[0]} pal1={pal_counts[1]} pal2={pal_counts[2]}")

    total_bytes = TITLE_TILES_SIZE * 2 + 160 + 20 + len(new_attrmap)
    return 1, total_bytes


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("CHORO Q - UNIFIED REINSERTION TOOL")
    print("Code Hacks + Text Insertion")
    print("=" * 70)
    print()

    if len(sys.argv) >= 3:
        input_rom = sys.argv[1]
        output_rom = sys.argv[2]
    elif len(sys.argv) == 2:
        input_rom = sys.argv[1]
        output_rom = OUTPUT_ROM
    else:
        input_rom = INPUT_ROM
        output_rom = OUTPUT_ROM

    print(f"Input ROM:  {input_rom}")
    print(f"Output ROM: {output_rom}")
    print()

    if not os.path.exists(input_rom):
        print(f"ERROR: Input ROM not found: {input_rom}")
        return 1

    with open(input_rom, 'rb') as f:
        rom_data = bytearray(f.read())
    print(f"ROM size: {len(rom_data)} bytes (0x{len(rom_data):X})")
    print()

    # =========================================================================
    # PHASE 1: CODE HACKS
    # =========================================================================
    print("-" * 70)
    print("PHASE 1: CODE HACKS")
    print("-" * 70)

    if MODULES_ENABLED.get('code_hacks', True):
        applied, errors = apply_code_hacks(rom_data)
        print(f"\n  Applied: {applied}/{len(CODE_PATCHES)}, Errors: {errors}")
    else:
        print("  SKIPPED (disabled)")
    print()

    # =========================================================================
    # PHASE 2: TEXT REINSERTION
    # =========================================================================
    print("-" * 70)
    print("PHASE 2: TEXT REINSERTION")
    print("-" * 70)
    print()

    total_strings = 0
    total_bytes = 0

    modules = [
        ("full_dialogue", "Full Dialogue + Parts", reinsert_full_dialogue, TRANSLATION_FILES['full_dialogue']),
        ("locations", "Location Names", reinsert_locations, TRANSLATION_FILES['locations']),
        ("shop", "Shop/Item Names", reinsert_shop, TRANSLATION_FILES['shop']),
        ("names", "Character Names", reinsert_names, TRANSLATION_FILES['names']),
        ("submenu", "Sub-Menu Text", reinsert_submenu, TRANSLATION_FILES['submenu']),
        ("bank12", "Bank 0x12 Text", reinsert_bank12, TRANSLATION_FILES['bank12']),
        ("sublocations", "Sub-Locations", reinsert_sublocations, TRANSLATION_FILES['sublocations']),
        ("title_screen", "Title Screen Graphic", reinsert_title_screen, TRANSLATION_FILES['title_screen']),
    ]

    for key, name, func, filepath in modules:
        if not MODULES_ENABLED.get(key, True):
            print(f"[{name}]")
            print(f"  SKIPPED (disabled)")
            print()
            continue

        print(f"[{name}]")
        print(f"  File: {filepath}")
        count, bytes_used = func(rom_data, filepath)
        print(f"  Strings: {count}, Bytes: {bytes_used}")
        total_strings += count
        total_bytes += bytes_used
        print()

    # =========================================================================
    # WRITE OUTPUT
    # =========================================================================
    with open(output_rom, 'wb') as f:
        f.write(rom_data)

    print("=" * 70)
    print("REINSERTION COMPLETE")
    print("=" * 70)
    print(f"Total strings inserted: {total_strings}")
    print(f"Total bytes written:    {total_bytes}")
    print(f"Output ROM: {output_rom}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
