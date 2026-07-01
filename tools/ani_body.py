# 解析 DNF 角色身体技能动画 .ani(character/swordman/animation/<skill>.ani)
# 格式(逆向自 Script.pvf 解密数据):
#   u16 frameCount, u16 imageCount, imageCount×(u32 pathLen + ascii path)
#   u16 globalFlag(=0)
#   每帧: u16 boxCount; boxCount×(u16 boxKw + 6×i32); u16 flag0; u16 imgFrame; i32 posX; i32 posY; u16 flag1; u16 delayKw; i32 delay
# imgFrame = sm_body 帧号(即身体图集索引); posX/posY = 绘制偏移; delay = 毫秒。
import struct

def parse_body_ani(b):
    if not b or len(b) < 8: return None
    fc, ic, plen = struct.unpack_from('<HHI', b, 0)
    p = 8 + plen
    # 跳过额外 image 路径(通常 ic=1)
    for _ in range(ic - 1):
        if p + 4 > len(b): break
        pl = struct.unpack_from('<I', b, p)[0]; p += 4 + pl
    i = p
    n = len(b)
    class _EOF(Exception): pass
    def u16():
        nonlocal i
        if i < 0 or i + 2 > n: raise _EOF
        v = struct.unpack_from('<H', b, i)[0]; i += 2; return v
    def i32():
        nonlocal i
        if i < 0 or i + 4 > n: raise _EOF
        v = struct.unpack_from('<i', b, i)[0]; i += 4; return v
    frames = []
    # 每帧: u16 boxCount; boxCount×(u16 kw + 6 i32); u16 flag0; u16 imgFrame; i32 posX; i32 posY;
    #       u16 attrCount; attrCount×attr, 其中 attr=(u16 kw + i32 arg), 但 kw==16 为字符串(i32 len + bytes)。
    try:
        u16()  # globalFlag
        for _ in range(fc):
            nbox = u16()
            if nbox > 40: break
            boxes = []
            for _ in range(nbox):
                u16()  # box kw
                boxes.append([i32() for _ in range(6)])
            flag0 = u16(); img = u16(); px = i32(); py = i32(); nattr = u16()
            if nattr > 20 or img > 209: break
            delay = 100
            for _ in range(nattr):
                kw = u16()
                if kw == 16:  # 字符串属性(音效/标记名)
                    ln = i32()
                    if ln < 0 or ln > 2000: raise _EOF
                    i += ln
                else:
                    v = i32()
                    if kw == 12: delay = v
            frames.append(dict(img=img, x=px, y=py, delay=max(10, delay), boxes=boxes))
    except _EOF:
        pass
    return dict(ok=(len(frames) == fc and i == n), frames=frames, fc=fc, consumed=i, total=n,
               reason='' if len(frames) == fc else 'partial')
    return dict(ok=(len(frames) == fc), frames=frames, fc=fc,
               consumed=i, total=len(b), reason='' if len(frames) == fc else 'short')


if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from pvf import Pvf
    pv = Pvf("地下城与勇士/Script.pvf")
    base = [e['path'] for e in pv.entries
            if e['path'].startswith('character/swordman/animation/') and e['path'].endswith('.ani')]
    okc = 0; tail_ok = 0
    for pth in base:
        r = parse_body_ani(pv.read(pth))
        if r and r['ok']:
            okc += 1
            if r['consumed'] == r['total']: tail_ok += 1
    print("身体动画总数 %d, 帧数吻合 %d, 且消耗到EOF %d" % (len(base), okc, tail_ok))
    # 抽样展示
    for kw in ['gorecross', 'tripleslash1', 'moonlightslashfull', 'waveeyeattack1', 'upperslashafter', 'chargecrashupper']:
        hit = [p for p in base if p.split('/')[-1][:-4] == kw]
        if hit:
            r = parse_body_ani(pv.read(hit[0]))
            print("  %-22s 帧%d ok=%s 图号=%s" % (kw, len(r['frames']), r['ok'], [f['img'] for f in r['frames']]))
