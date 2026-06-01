import struct
import os

def simple_unpack(pkg_path, output_dir):
    with open(pkg_path, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes\n")
    
    pos = 0
    
    # Header: [4B hdr_len][version][4B entry_count]
    hdr_len = struct.unpack('<I', data[pos:pos+4])[0]; pos += 4
    version = data[pos:pos+hdr_len].decode('ascii'); pos += hdr_len
    count = struct.unpack('<I', data[pos:pos+4])[0]; pos += 4
    
    print(f"Version: {version}, Count: {count}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    entries = []
    
    for i in range(count):
        if pos + 16 > len(data):
            print(f"\n[{i+1}] End of file at offset {pos}")
            break
        
        # Entry format:
        # [4B name_len][name_with_null][4B type_or_zero][4B data_len][DATA]
        
        name_len = struct.unpack('<I', data[pos:pos+4])[0]
        pos += 4
        
        if name_len == 0 or name_len > 1000 or pos + name_len > len(data):
            print(f"\n[{i+1}] Bad name_len={name_len} at offset {pos-4}")
            break
        
        # Extract filename (strip null terminators)
        name_bytes = data[pos:pos+name_len]
        null_idx = name_bytes.find(b'\x00')
        if null_idx >= 0:
            filename = name_bytes[:null_idx].decode('utf-8', errors='ignore')
        else:
            filename = name_bytes.decode('utf-8', errors='ignore')
        
        pos += name_len
        
        # Read type and data_len
        type_val = struct.unpack('<I', data[pos:pos+4])[0]; pos += 4
        data_len = struct.unpack('<I', data[pos:pos+4])[0]; pos += 4
        
        # Validate data_len
        if data_len == 0 or data_len > 100*1024*1024 or pos + data_len > len(data):
            print(f"\n[{i+1}] Bad data_len={data_len} for '{filename}' at offset {pos-4}")
            
            # Debug info
            print(f"  Type: {type_val}, Remaining bytes: {len(data)-pos}")
            if pos + 16 <= len(data):
                next_bytes = data[pos:pos+16]
                print(f"  Next 16 bytes: {' '.join(f'{b:02X}' for b in next_bytes)}")
            break
        
        # Extract file data
        file_data = data[pos:pos+data_len]
        pos += data_len
        
        entries.append({
            'name': filename,
            'type': type_val,
            'length': data_len,
            'data': file_data
        })
        
        if (i+1) % 10 == 0 or i < 3:
            size_str = f"{data_len}B"
            if data_len >= 1024:
                size_str = f"{data_len/1024:.1f}KB"
            if data_len >= 1024*1024:
                size_str = f"{data_len/1024/1024:.2f}MB"
            print(f"[{i+1:3d}] {filename:<65s} ({size_str:>10s})")
    
    print(f"\n{'='*80}")
    print(f"Parsed {len(entries)} entries, extracting files...")
    print(f"{'='*80}\n")
    
    extracted = 0
    for idx, entry in enumerate(entries):
        try:
            filepath = os.path.join(output_dir, *entry['name'].split('/'))
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(entry['data'])
            
            extracted += 1
            
            if extracted <= 20 or extracted % 10 == 0:
                size_str = f"{entry['length']}B"
                if entry['length'] >= 1024:
                    size_str = f"{entry['length']/1024:.1f}KB"
                if entry['length'] >= 1024*1024:
                    size_str = f"{entry['length']/1024/1024:.2f}MB"
                
                print(f"[{extracted:3d}] {entry['name']}")
            
        except Exception as e:
            print(f"[{idx+1}] ERROR: {entry['name']}: {e}")
    
    print(f"\n{'='*80}")
    print(f"✓ Extracted {extracted}/{len(entries)} files to: {output_dir}")
    return extracted

if __name__ == '__main__':
    result = simple_unpack(
        r'd:\download\Nijika\start_bg\scene.pkg',
        r'd:\download\Nijika\start_bg\extracted'
    )