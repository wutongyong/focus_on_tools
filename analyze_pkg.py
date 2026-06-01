import struct
import os

def try_multiple_formats(pkg_path):
    with open(pkg_path, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes\n")
    
    # 格式1：基于之前观察到的模式
    print("=" * 80)
    print("FORMAT ATTEMPT 1: [4B hdr_len][version][4B count][entries...]")
    print("=" * 80)
    
    pos = 0
    hdr_len = struct.unpack('<I', data[pos:pos+4])[0]
    version = data[pos+4:pos+4+hdr_len].decode('ascii')
    count = struct.unpack('<I', data[pos+4+hdr_len:pos+8+hdr_len])[0]
    
    print(f"Header len: {hdr_len}")
    print(f"Version: {version}")
    print(f"Count: {count}")
    
    pos = 8 + hdr_len
    
    entries1 = []
    for i in range(min(count, 5)):  # 只读前5个测试
        if pos + 20 > len(data):
            break
        
        nl = struct.unpack('<I', data[pos:pos+4])[0]
        pos += 4
        
        if nl > 500 or nl <= 0:
            print(f"\n[{i+1}] Bad name_len: {nl} at offset {pos-4}")
            break
        
        name = data[pos:pos+nl].rstrip(b'\x00').decode('utf-8', errors='ignore')
        pos += nl
        
        v1 = struct.unpack('<I', data[pos:pos+4])[0]
        v2 = struct.unpack('<I', data[pos+4:pos+8])[0]
        v3 = struct.unpack('<I', data[pos+8:pos+12])[0]
        
        print(f"[{i+1}] '{name}' | vals: {v1}, {v2}, {v3}")
        
        # 尝试判断哪个组合合理
        # 组合A: v1=type, v2=data_len, v3=next_name_len
        valid_a = (v2 > 10 and v2 < 50*1024*1024 and v3 > 0 and v3 < 500)
        # 组合B: v1=data_len, v2=type, v3=next_name_len  
        valid_b = (v1 > 10 and v1 < 50*1024*1024 and v3 > 0 and v3 < 500)
        
        if valid_a:
            print(f"     -> Format A: type={v1}, data_len={v2}, next_name={v3} ✓")
            entries1.append({'name': name, 'data_len': v2, 'type': v1})
            pos += 12
        elif valid_b:
            print(f"     -> Format B: data_len={v1}, type={v2}, next_name={v3} ✓")
            entries1.append({'name': name, 'data_len': v1, 'type': v2})
            pos += 12
        else:
            print(f"     -> Cannot determine format")
            pos += 12
    
    # 格式2：假设每个条目只有name和连续的数据
    print("\n" + "=" * 80)
    print("FORMAT ATTEMPT 2: Looking for pattern in raw data")
    print("=" * 80)
    
    # 搜索已知的文件名模式来定位数据
    patterns = [
        b'materials/',
        b'shaders/',
        b'models/',
        b'.json',
        b'.tex',
        b'.vert',
        b'.frag'
    ]
    
    found_positions = []
    for pat in patterns:
        idx = 0
        while True:
            idx = data.find(pat, idx)
            if idx == -1:
                break
            
            # 检查前面是否有长度前缀
            if idx >= 4:
                possible_len = struct.unpack('<I', data[idx-4:idx])[0]
                if 0 < possible_len < 300 and abs(possible_len - len(pat)) < 100:
                    found_positions.append((idx-4, pat.decode(), possible_len))
            
            idx += 1
    
    print(f"\nFound {len(found_positions)} potential entry starts:")
    for offset, pat, length in sorted(found_positions)[:15]:
        context_start = max(0, offset-4)
        context_end = min(len(data), offset+60)
        context = data[context_start:context_end]
        
        hex_str = ' '.join(f'{b:02X}' for b in context[:20])
        ascii_str = ''.join(chr(b) if 32<=b<127 else '.' for b in context)
        
        print(f"  Offset {offset:04X}: len={length:3d} | {pat:<12s} | {hex_str} | {ascii_str}")

if __name__ == '__main__':
    try_multiple_formats(r'd:\download\Nijika\start_bg\scene.pkg')