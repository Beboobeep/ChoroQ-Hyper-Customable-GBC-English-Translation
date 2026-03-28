#!/usr/bin/env python3
"""
Choro Q - Hyper Customable GBC
Text Pointer & Text Extraction

Scans the entire ROM for text pointers in the format: <LO> <HI> <BANK>
Validates pointers by checking for FB XX FA (face code) at target location.
Extracts the text at each pointer location and outputs in translation format.

"""

import sys
import os

INPUT_ROM = "Choro Q - Hyper Customable GB (Japan)_CleanCopy.gbc"
OUTPUT_FILE = "choroq_needs_all_english.txt"


#ENCODING

CHAR_MAP = {
    0x00: 'あ', 0x01: 'い', 0x02: 'う', 0x03: 'え', 0x04: 'お',
    0x05: 'か', 0x06: 'き', 0x07: 'く', 0x08: 'け', 0x09: 'こ',
    0x0A: 'さ', 0x0B: 'し', 0x0C: 'す', 0x0D: 'せ', 0x0E: 'そ',
    0x0F: 'た', 0x10: 'ち', 0x11: 'つ', 0x12: 'て', 0x13: 'と',
    0x14: 'な', 0x15: 'に', 0x16: 'ぬ', 0x17: 'ね', 0x18: 'の',
    0x19: 'は', 0x1A: 'ひ', 0x1B: 'ふ', 0x1C: 'へ', 0x1D: 'ほ',
    0x1E: 'ま', 0x1F: 'み', 0x20: 'む', 0x21: 'め', 0x22: 'も',
    0x23: 'や', 0x24: 'わ', 0x25: 'ゆ', 0x26: 'を', 0x27: 'よ',
    0x28: 'ら', 0x29: 'り', 0x2A: 'る', 0x2B: 'れ', 0x2C: 'ろ',
    0x2D: 'ぁ', 0x2E: 'ぃ', 0x2F: 'っ', 0x30: 'ぇ', 0x31: 'ぉ',
    0x32: 'ゃ', 0x33: 'ん', 0x34: 'ゅ', 0x35: 'っ', 0x36: 'ょ',
    0x37: '０', 0x38: '１', 0x39: '２', 0x3A: '３', 0x3B: '４',
    0x3C: '５', 0x3D: '６', 0x3E: '７', 0x3F: '８', 0x40: '９',
    0x41: 'Ａ', 0x42: 'Ｂ', 0x43: 'Ｃ', 0x44: 'Ｄ', 0x45: 'Ｅ',
    0x46: 'Ｆ', 0x47: 'Ｇ', 0x48: 'Ｈ', 0x49: 'Ｉ', 0x4A: 'Ｊ',
    0x4B: 'Ｋ', 0x4C: 'Ｌ', 0x4D: 'Ｍ', 0x4E: 'Ｎ', 0x4F: 'Ｏ',
    0x50: 'Ｐ', 0x51: 'Ｑ', 0x52: 'Ｒ', 0x53: 'Ｓ', 0x54: 'Ｔ',
    0x55: 'Ｕ', 0x56: 'Ｖ', 0x57: 'Ｗ', 0x58: 'Ｘ', 0x59: 'Ｙ',
    0x5A: 'Ｚ', 0x5B: '★', 0x5C: '-', 0x5D: '~', 0x5E: '・',
    0x5F: '♥', 0x60: '!', 0x61: '&', 0x62: '「', 0x63: '」',
    0x64: '?', 0x65: '゜', 0x66: '゛', 0x67: '゜', 0x68: '"',
    0x69: 'ア', 0x6A: 'イ', 0x6B: 'ウ', 0x6C: 'エ', 0x6D: 'オ',
    0x6E: 'カ', 0x6F: 'キ', 0x70: 'ク', 0x71: 'ケ', 0x72: 'コ',
    0x73: 'サ', 0x74: 'シ', 0x75: 'ス', 0x76: 'セ', 0x77: 'ソ',
    0x78: 'タ', 0x79: 'チ', 0x7A: 'ツ', 0x7B: 'テ', 0x7C: 'ト',
    0x7D: 'ナ', 0x7E: 'ニ', 0x7F: 'ヌ', 0x80: 'ネ', 0x81: 'ノ',
    0x82: 'ハ', 0x83: 'ヒ', 0x84: 'フ', 0x85: 'ヘ', 0x86: 'ホ',
    0x87: 'マ', 0x88: 'ミ', 0x89: 'ム', 0x8A: 'メ', 0x8B: 'モ',
    0x8C: 'ヤ', 0x8D: 'ユ', 0x8E: 'ワ', 0x8F: 'ヨ', 0x90: 'ョ',
    0x91: 'ラ', 0x92: 'リ', 0x93: 'ル', 0x94: 'レ', 0x95: 'ロ',
    0x96: 'ヰ', 0x97: 'ィ', 0x98: 'ゥ', 0x99: 'ェ', 0x9A: 'ォ',
    0x9B: 'ャ', 0x9C: 'ン', 0x9D: 'ュ', 0x9E: 'ッ', 0x9F: 'ョ',
    0xA0: '/', 0xA1: '#', 0xA2: '\'', 0xA3: '。', 0xA4: ' ',
    0xA5: '▼', 0xA6: '■', 0xA7: '(', 0xA8: ')', 0xA9: '→',
    0xAC: '.', 0xAD: ',', 0xB0: '*', 0xB1: '←', 0xB2: '▲',
}

# Dakuten combinations
DAKUTEN = {
    'か': 'が', 'き': 'ぎ', 'く': 'ぐ', 'け': 'げ', 'こ': 'ご',
    'さ': 'ざ', 'し': 'じ', 'す': 'ず', 'せ': 'ぜ', 'そ': 'ぞ',
    'た': 'だ', 'ち': 'ぢ', 'つ': 'づ', 'て': 'で', 'と': 'ど',
    'は': 'ば', 'ひ': 'び', 'ふ': 'ぶ', 'へ': 'べ', 'ほ': 'ぼ',
    'カ': 'ガ', 'キ': 'ギ', 'ク': 'グ', 'ケ': 'ゲ', 'コ': 'ゴ',
    'サ': 'ザ', 'シ': 'ジ', 'ス': 'ズ', 'セ': 'ゼ', 'ソ': 'ゾ',
    'タ': 'ダ', 'チ': 'ヂ', 'ツ': 'ヅ', 'テ': 'デ', 'ト': 'ド',
    'ハ': 'バ', 'ヒ': 'ビ', 'フ': 'ブ', 'ヘ': 'ベ', 'ホ': 'ボ',
    'ウ': 'ヴ',
}

# Handakuten combinations
HANDAKUTEN = {
    'は': 'ぱ', 'ひ': 'ぴ', 'ふ': 'ぷ', 'へ': 'ぺ', 'ほ': 'ぽ',
    'ハ': 'パ', 'ヒ': 'ピ', 'フ': 'プ', 'ヘ': 'ペ', 'ホ': 'ポ',
}


def decode_text(data, start, max_len=2000):
    
    result = []
    raw = []
    i = start
    
    while i < len(data) and i < start + max_len:
        b = data[i]
        raw.append(b)
        
        if b == 0xFF:
            result.append('<STOP>')
            break
        
        if b == 0xFB and i + 3 < len(data) and data[i + 2] == 0xFA:
            face1 = data[i + 1]
            face2 = data[i + 3]
            result.append(f'<FACE:{face1:02X},{face2:02X}>')
            raw.extend([data[i + 1], data[i + 2], data[i + 3]])
            i += 4
            continue
        
        if 0xE0 <= b <= 0xEF:
            result.append(f'[E{b - 0xE0:X}]')
            i += 1
            continue
        
        if b == 0xFC:
            result.append('▼\n')
            i += 1
            continue
        
        if b == 0xFD:
            result.append('[END]')
            i += 1
            continue
        
        if b == 0xFE:
            result.append('\n')
            i += 1
            continue
        
        if b in CHAR_MAP:
            char = CHAR_MAP[b]
            
            # Check for dakuten/handakuten
            if i + 1 < len(data):
                next_b = data[i + 1]
                if next_b == 0x66 and char in DAKUTEN:
                    char = DAKUTEN[char]
                    raw.append(next_b)
                    i += 1
                elif next_b == 0x65 and char in HANDAKUTEN:
                    char = HANDAKUTEN[char]
                    raw.append(next_b)
                    i += 1
            
            result.append(char)
        else:
            # Unknown byte
            result.append(f'[{b:02X}]')
        
        i += 1
    
    return ''.join(result), bytes(raw), len(raw)


def has_face_code(data, rom_addr):
    
    if rom_addr + 3 >= len(data):
        return False
    return data[rom_addr] == 0xFB and data[rom_addr + 2] == 0xFA


def find_dialogue_pointers(data):
    
    pointers = []
    
    for i in range(len(data) - 2):
        lo = data[i]
        hi = data[i + 1]
        bank = data[i + 2]
        
        if bank > 0x7F:
            continue
        
        cpu_addr = (hi << 8) | lo
        
        if cpu_addr < 0x4000 or cpu_addr > 0x7FFF:
            continue
        
        rom_addr = (bank * 0x4000) + (cpu_addr - 0x4000)
        
        if rom_addr >= len(data) - 4:
            continue
        
        # Check for FB XX FA face code
        if not has_face_code(data, rom_addr):
            continue
        
        pointers.append({
            'ptr_offset': i,
            'ptr_bytes': bytes([lo, hi, bank]),
            'bank': bank,
            'cpu_addr': cpu_addr,
            'rom_addr': rom_addr,
        })
    
    return pointers


def main():
    
    if len(sys.argv) >= 3:
        rom_path = sys.argv[1]
        output_path = sys.argv[2]
    elif len(sys.argv) == 2:
        rom_path = sys.argv[1]
        output_path = OUTPUT_FILE
    else:
        rom_path = INPUT_ROM
        output_path = OUTPUT_FILE
    
    print("Choro Q Text Extraction")
    print("=" * 80)
    print(f"Input ROM: {rom_path}")
    print(f"Output: {output_path}")
    print()
    
    if not os.path.exists(rom_path):
        print(f"ERROR: ROM file not found: {rom_path}")
        return
    
    with open(rom_path, 'rb') as f:
        data = f.read()
    
    print(f"ROM size: {len(data)} bytes (0x{len(data):X})")
    
    all_pointers = find_dialogue_pointers(data)
    print(f"Total dialogue pointers found: {len(all_pointers)}")
    
    for ptr in all_pointers:
        text, raw, length = decode_text(data, ptr['rom_addr'])
        ptr['text'] = text
        ptr['raw'] = raw
        ptr['length'] = length
    
    # Remove duplicates (same ROM address) - keep first occurrence
    seen_rom_addrs = set()
    unique_pointers = []
    for ptr in all_pointers:
        if ptr['rom_addr'] not in seen_rom_addrs:
            seen_rom_addrs.add(ptr['rom_addr'])
            unique_pointers.append(ptr)
    
    print(f"Unique text locations: {len(unique_pointers)}")
    
    unique_pointers.sort(key=lambda x: x['rom_addr'])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Choro Q - Hyper Customable GBC\n")
        f.write("# ALL TEXT NEEDING ENGLISH TRANSLATION\n")
        f.write(f"# Total blocks: {len(unique_pointers)}\n")
        f.write("# " + "=" * 76 + "\n\n")
        
        for idx, ptr in enumerate(unique_pointers):
            f.write("=" * 80 + "\n")
            f.write(f"TEXT BLOCK #{idx:04d}\n")
            f.write("=" * 80 + "\n")
            
            # Pointer info
            f.write("--- POINTER INFO ---\n")
            f.write(f"PTR_OFFSET:  0x{ptr['ptr_offset']:06X}\n")
            f.write(f"PTR_BYTES:   {' '.join(f'{b:02X}' for b in ptr['ptr_bytes'])}\n")
            f.write(f"BANK:        0x{ptr['bank']:02X} ({ptr['bank']})\n")
            f.write(f"TEXT_CPU:    0x{ptr['cpu_addr']:04X}\n")
            f.write(f"TEXT_ROM:    0x{ptr['rom_addr']:06X}\n")
            f.write(f"TEXT_LENGTH: {ptr['length']} bytes\n")
            
            # Raw bytes
            f.write("--- RAW BYTES ---\n")
            raw_hex = ' '.join(f'{b:02X}' for b in ptr['raw'])
            # Wrap at 48 chars
            for i in range(0, len(raw_hex), 48):
                f.write(raw_hex[i:i+48] + "\n")
            
            # Japanese text
            f.write("--- JAPANESE ---\n")
            f.write(ptr['text'] + "\n")
            f.write("---\n")
            
            # English placeholder
            f.write("--- ENGLISH TRANSLATION ---\n")
            f.write("\n")
            f.write("---\n")
            f.write("\n")
    
    print(f"\nOutput written to: {output_path}")
    
    # Print summary by bank
    by_bank = {}
    for ptr in unique_pointers:
        bank = ptr['bank']
        if bank not in by_bank:
            by_bank[bank] = 0
        by_bank[bank] += 1
    
    print("\nSummary by bank:")
    print("-" * 40)
    print(f"{'Bank':<12} {'ROM Start':<12} {'Count':<8}")
    print("-" * 40)
    for bank in sorted(by_bank.keys()):
        bank_start = bank * 0x4000
        print(f"0x{bank:02X}         0x{bank_start:06X}     {by_bank[bank]:<8}")
    
    print("-" * 40)
    print(f"{'TOTAL':<24} {len(unique_pointers):<8}")


if __name__ == '__main__':
    main()
