import struct
import os

def debug_single_entry(data, start_offset, entry_num):
    print(f"\n{'='*80}")
    print(f"DEBUG ENTRY {entry_num} at offset {start_offset:04X} ({start_offset})")
    print(f"{'='*80}")
    
    pos = start_offset
    
    if pos + 4 > len(data):
        print("Not enough data!")
        return None, pos
    
    # Read potential name_len
    raw_bytes = data[pos:pos+4]
    val = struct.unpack('<I', raw_bytes)[0]
    
    print(f"\nBytes at offset {pos:04X}: {' '.join(f'{b:02X}' for b in raw_bytes)} = {val} (0x{val:08X})")
    
    # Check if this looks like a reasonable name_len
    if 10 < val < 200:
        print(f"-> Looks like a valid name_len: {val}")
        
        # Try to read the name
        name_start = pos + 4
        name_raw = data[name_start:name_start+val]
        
        print(f"\nName bytes ({val} bytes):")
        for i in range(0, min(val, len(name_raw)), 16):
            chunk = name_raw[i:i+16]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            ascii_str = ''.join(chr(b) if 32<=b<127 else '.' for b in chunk)
            print(f"  {i:04X}: {hex_str:<48s} {ascii_str}")
        
        # Find actual string content
        null_pos = name_raw.find(b'\x00')
        if null_pos >= 0:
            actual_name = name_raw[:null_pos].decode('utf-8', errors='ignore')
            padding = val - null_pos - 1
            print(f"\nActual name: '{actual_name}' ({null_pos} chars)")
            print(f"Null terminator at offset {null_pos}, padding after: {padding} bytes")
        else:
            actual_name = name_raw.decode('utf-8', errors='ignore')
            print(f"\nName (no null found): '{actual_name}'")
        
        # Show what comes after the name
        after_name = name_start + val
        print(f"\nAfter name (offset {after_name:04X}), next 32 bytes:")
        for i in range(min(32, len(data)-after_name)):
            if i % 16 == 0:
                print(f"  {after_name+i:04X}: ", end='')
            print(f'{data[after_name+i]:02X} ', end='')
            if (i+1) % 16 == 0:
                print()
        print()
        
        return actual_name, after_name
    
    else:
        print(f"-> Does NOT look like a valid name_len!")
        
        # Show context
        print(f"\nContext around this position:")
        ctx_start = max(0, pos - 8)
        ctx_end = min(len(data), pos + 48)
        
        for i in range(ctx_start, ctx_end):
            if i % 16 == 0:
                print(f"  {i:04X}: ", end='')
            print(f'{data[i]:02X} ', end='')
            if (i+1) % 16 == 0 or i == ctx_end-1:
                ascii_part = data[max(ctx_start,i-15):i+1]
                ascii_str = ''.join(chr(b) if 32<=b<127 else '.' for b in ascii_part)
                print(f' | {ascii_str}')
        
        return None, pos

def main():
    with open(r'd:\download\Nijika\start_bg\scene.pkg', 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes")
    
    # Parse header
    pos = 0
    hdr_len = struct.unpack('<I', data[pos:pos+4])[0]; pos += 4
    version = data[pos:pos+hdr_len].decode('ascii'); pos += hdr_len
    count = struct.unpack('<I', data[pos:pos+4])[0]; pos += 4
    
    print(f"Version: {version}")
    print(f"Entry count: {count}")
    print(f"Header ends at offset {pos:04X}")
    
    # Debug first 3 entries
    for i in range(3):
        name, next_pos = debug_single_entry(data, pos, i+1)
        if name is None:
            print(f"\nFailed to parse entry {i+1}")
            break
        
        # Now try to figure out what follows
        # After name, we expect some metadata then data
        
        # Try reading metadata fields
        test_pos = next_pos
        print(f"\n--- Attempting to parse metadata at offset {test_pos:04X} ---")
        
        vals = []
        for j in range(6):  # Try reading up to 6 uint32 values
            if test_pos + 4 <= len(data):
                v = struct.unpack('<I', data[test_pos:test_pos+4])[0]
                vals.append(v)
                print(f"  [{j}] offset {test_pos:04X}: {v:>12d} (0x{v:08X})")
                test_pos += 4
            else:
                break
        
        # Analyze which combination makes sense
        print(f"\nAnalyzing possible interpretations...")
        
        # Common patterns:
        # Pattern A: [type][data_len] -> data
        # Pattern B: [data_len][type] -> data  
        # Pattern C: [type][data_len][extra] -> data
        
        for pattern_name, offsets in [
            ("A: [type][data_len->data]", [(0, 1)]),
            ("B: [data_len->data][type]", [(1, 0)]),
            ("C: [type][data_len->data][next_nl]", [(0, 1, 2)])
        ]:
            try:
                data_len_idx = offsets[1]
                data_len_candidate = vals[data_len_idx]
                
                is_valid = (100 < data_len_candidate < 50*1024*1024 and 
                           test_pos + data_len_candidate <= len(data))
                
                if is_valid:
                    # Check if data after that length looks reasonable
                    data_start = test_pos
                    data_end = data_start + data_len_candidate
                    
                    # Check if we can find another entry marker after the data
                    if data_end + 4 <= len(data):
                        next_possible_nl = struct.unpack('<I', data[data_end:data_end+4])[0]
                        if 10 < next_possible_nl < 200:
                            print(f"  ✓ {pattern_name}: data_len={data_len_candidate}, next entry likely at {data_end:04X}")
                            pos = data_end
                            break
            except:
                pass
        
        if i == 0:
            input("\nPress Enter to continue to next entry...")

if __name__ == '__main__':
    main()