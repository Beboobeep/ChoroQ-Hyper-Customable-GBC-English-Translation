#!/usr/bin/env python3
"""
Choro Q - Hyper Customable GB
UNIFIED TEXT REINSERTION TOOL

Supports the new choroq_full_translation_file.txt format with 1451 blocks.

Text Modules:
1. Main dialogue (Banks 0x50-0x5A) -> Free space 0x16B470-0x1C7FFF
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
import sys

# =============================================================================
# CONFIGURATION - Edit these paths to match your setup
# =============================================================================

INPUT_ROM = "Choro Q - Hyper Customable GBC_Hacked_Copy_JP.gbc"
OUTPUT_ROM = "Choro Q - Hyper Customable GB_Englishteesst.gbc"

# Translation files for each module
TRANSLATION_FILES = {
    'full_dialogue': "choroq_full_translation_file.txt",  # New unified file
    'locations': "choroq_location_translation.txt",
    'shop': "ChoroQ_Shop_Text_Dump_Translated.txt",
    'names': "choroq_names_translation.txt",
    'submenu': "choroq_submenu_translation.txt",
    'bank12': "choroq_bank12_inplace.txt",
    'sublocations': "choroq_subLocations_translation.txt",
}

# Set to False to skip specific modules
MODULES_ENABLED = {
    'full_dialogue': True,   # Main dialogue + part descriptions from unified file
    'locations': True,
    'shop': True,
    'names': True,
    'submenu': True,
    'bank12': True,
    'sublocations': True,
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

    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
    'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
    'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
    'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
    'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59,
    'z': 0x5A,
    
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
# ENCODING FUNCTIONS
# =============================================================================

def encode_dialogue_text(text):
    """Encode dialogue text with full control code support."""
    result = []
    text = text.strip()
    
    # Normalize control markers
    text = text.replace('\n▼\n', '▼').replace('\n▼', '▼').replace('▼\n', '▼')
    text = text.replace('\n---\n', '---').replace('\n---', '---').replace('---\n', '---')
    text = text.replace('\n[END]\n', '[END]').replace('\n[END]', '[END]').replace('[END]\n', '[END]')
    # Handle <STOP> tag - remove it as FF terminator is added automatically
    text = text.replace('<STOP>', '')
    
    i = 0
    while i < len(text):
        # <FACE:XX,YY>
        face_match = re.match(r'<FACE:([0-9A-Fa-f]{2}),([0-9A-Fa-f]{2})>', text[i:])
        if face_match:
            result.extend([0xFB, int(face_match.group(1), 16), 0xFA, int(face_match.group(2), 16)])
            i += face_match.end()
            continue
        
        # [E0]-[EF] variables
        var_match = re.match(r'\[(E[0-9A-Fa-f])\]', text[i:])
        if var_match:
            var_name = var_match.group(1).upper()
            if var_name in VARIABLE_BYTES:
                result.append(VARIABLE_BYTES[var_name])
            i += var_match.end()
            continue
        
        # [END]
        if text[i:i+5] == '[END]':
            result.append(CTRL_END)
            i += 5
            continue
        
        # ---
        if text[i:i+3] == '---':
            result.append(CTRL_SECTION)
            i += 3
            continue
        
        # ▼
        if text[i] == '▼':
            result.append(CTRL_WAIT)
            i += 1
            continue
        
        # Newline
        if text[i] == '\n':
            result.append(CTRL_NEWLINE)
            i += 1
            continue
        
        # Regular character
        char = text[i].upper()
        if char in CHAR_TO_BYTE:
            result.append(CHAR_TO_BYTE[char])
        else:
            print(f"    Warning: Unknown char '{text[i]}' (0x{ord(text[i]):02X})")
            result.append(0xA4)
        i += 1
    
    # Ensure ends with FF
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
# MODULE: FULL DIALOGUE (New unified format - Banks 0x06, 0x27-0x29, 0x50-0x5A, 0x78)
# =============================================================================

# Free space regions for text insertion
FREE_SPACE_DIALOGUE = (0x16B470, 0x1C7FFF)    # Main dialogue (banks 0x50-0x5A)
FREE_SPACE_PARTS = (0x0A5BEE, 0x0BFFFF)       # Part descriptions (banks 0x27-0x29)

# Banks that use each free space region
DIALOGUE_BANKS = {0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x78}
PARTS_BANKS = {0x27, 0x28, 0x29}
# Bank 0x06 blocks are handled by sublocations module


def parse_full_translation_file(filepath):
    """
    Parse the new unified translation file format.
    
    Returns blocks grouped by target region:
    - 'dialogue': Banks 0x50-0x5A, 0x78 -> write to 0x16B470+
    - 'parts': Banks 0x27-0x29 -> write to 0x0A5BEE+
    - 'bank06': Bank 0x06 -> handled separately
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    dialogue_blocks = []
    parts_blocks = []
    bank06_blocks = []
    
    # Pattern for the new format
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
        
        # Skip blocks with no English translation
        if not english:
            continue
        
        # Skip placeholder text
        if english == '[Enter your translation here]':
            continue
        
        # Skip blocks that are just the Japanese repeated or face-only
        if english.startswith('<FACE:') and english.endswith('<STOP>') and '\n' not in english:
            # This is a face-only block, include it
            pass
        
        block = {
            'block_num': block_num,
            'ptr_offset': ptr_offset,
            'bank': bank,
            'english': english,
        }
        
        # Route to appropriate list based on bank
        if bank in DIALOGUE_BANKS:
            dialogue_blocks.append(block)
        elif bank in PARTS_BANKS:
            parts_blocks.append(block)
        elif bank == 0x06:
            bank06_blocks.append(block)
        else:
            # Unknown bank, add to dialogue by default
            dialogue_blocks.append(block)
    
    return dialogue_blocks, parts_blocks, bank06_blocks


def reinsert_full_dialogue(rom_data, filepath):
    """
    Reinsert text from the unified translation file.
    
    Handles both main dialogue (banks 0x50-0x5A) and part descriptions (banks 0x27-0x29).
    Uses correct 3-byte pointer format: LO HI BANK (no leading 0x22).
    """
    if not os.path.exists(filepath):
        print(f"  Skipping: {filepath} not found")
        return 0, 0
    
    dialogue_blocks, parts_blocks, bank06_blocks = parse_full_translation_file(filepath)
    
    total_count = 0
    total_bytes = 0
    
    # Process dialogue blocks (banks 0x50-0x5A, 0x78)
    if dialogue_blocks:
        print(f"  Processing {len(dialogue_blocks)} dialogue blocks...")
        current_pos = FREE_SPACE_DIALOGUE[0]
        count = 0
        
        for block in dialogue_blocks:
            encoded = encode_dialogue_text(block['english'])
            
            if current_pos + len(encoded) > FREE_SPACE_DIALOGUE[1]:
                print(f"    ERROR: Out of space at block #{block['block_num']}")
                break
            
            # Write text
            rom_data[current_pos:current_pos + len(encoded)] = encoded
            
            # Update pointer (3-byte format: LO HI BANK)
            new_bank = current_pos // 0x4000
            cpu_addr = (current_pos % 0x4000) + 0x4000
            
            rom_data[block['ptr_offset']] = cpu_addr & 0xFF
            rom_data[block['ptr_offset'] + 1] = (cpu_addr >> 8) & 0xFF
            rom_data[block['ptr_offset'] + 2] = new_bank
            
            current_pos += len(encoded)
            count += 1
        
        bytes_used = current_pos - FREE_SPACE_DIALOGUE[0]
        print(f"    Dialogue: {count} blocks, {bytes_used} bytes (0x{FREE_SPACE_DIALOGUE[0]:06X}-0x{current_pos-1:06X})")
        total_count += count
        total_bytes += bytes_used
    
    # Process parts blocks (banks 0x27-0x29)
    if parts_blocks:
        print(f"  Processing {len(parts_blocks)} part description blocks...")
        current_pos = FREE_SPACE_PARTS[0]
        count = 0
        
        for block in parts_blocks:
            encoded = encode_dialogue_text(block['english'])
            
            if current_pos + len(encoded) > FREE_SPACE_PARTS[1]:
                print(f"    ERROR: Out of space at block #{block['block_num']}")
                break
            
            # Write text
            rom_data[current_pos:current_pos + len(encoded)] = encoded
            
            # Update pointer (3-byte format: LO HI BANK)
            new_bank = current_pos // 0x4000
            cpu_addr = (current_pos % 0x4000) + 0x4000
            
            rom_data[block['ptr_offset']] = cpu_addr & 0xFF
            rom_data[block['ptr_offset'] + 1] = (cpu_addr >> 8) & 0xFF
            rom_data[block['ptr_offset'] + 2] = new_bank
            
            current_pos += len(encoded)
            count += 1
        
        bytes_used = current_pos - FREE_SPACE_PARTS[0]
        print(f"    Parts: {count} blocks, {bytes_used} bytes (0x{FREE_SPACE_PARTS[0]:06X}-0x{current_pos-1:06X})")
        total_count += count
        total_bytes += bytes_used
    
    # Bank 0x06 blocks - just report, handled by sublocations module
    if bank06_blocks:
        print(f"  Note: {len(bank06_blocks)} bank 0x06 blocks found (handled by sublocations module)")
    
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
        r'\[END\]',
        re.MULTILINE
    )
    
    for match in pattern.finditer(content):
        english = match.group(7).strip()
        if english:
            entries.append({
                'ptr_offset': int(match.group(2), 16),
                'english': english,
            })
    
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
        r'\[END\]',
        re.MULTILINE
    )
    
    for match in pattern.finditer(content):
        english = match.group(8).strip()
        if english:
            entries.append({
                'ptr_offset': int(match.group(2), 16),
                'english': english,
            })
    
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
        r'\[END\]',
        re.MULTILINE
    )
    
    for match in pattern.finditer(content):
        english = match.group(7).strip()
        if english:
            entries.append({
                'ptr_offset': int(match.group(2), 16),
                'english': english,
            })
    
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
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("CHORO Q - UNIFIED TEXT REINSERTION TOOL")
    print("=" * 70)
    print()
    
    # Parse arguments
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
    
    total_strings = 0
    total_bytes = 0
    
    # Module definitions
    modules = [
        ("full_dialogue", "Full Dialogue + Parts", reinsert_full_dialogue, TRANSLATION_FILES['full_dialogue']),
        ("locations", "Location Names", reinsert_locations, TRANSLATION_FILES['locations']),
        ("shop", "Shop/Item Names", reinsert_shop, TRANSLATION_FILES['shop']),
        ("names", "Character Names", reinsert_names, TRANSLATION_FILES['names']),
        ("submenu", "Sub-Menu Text", reinsert_submenu, TRANSLATION_FILES['submenu']),
        ("bank12", "Bank 0x12 Text", reinsert_bank12, TRANSLATION_FILES['bank12']),
        ("sublocations", "Sub-Locations", reinsert_sublocations, TRANSLATION_FILES['sublocations']),
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
