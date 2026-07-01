# 解析 DNF PVF 内编译的 .ani 动画(特效图层)。
# 格式: u16 frameCount, u16 imageCount, imageCount×(u32 pathLen + ascii path), 之后帧数据。
# 每帧含: i16 图内帧索引(-1=空帧) + i32 posX + i32 posY + 若干 u16 + i32 delay(ms)。
# 合成只需: 引用的 img 路径 + 层锚点(posX,posY) + 帧率, 混合统一加色。
import struct, re

def parse_ani(b):
    if len(b) < 8: return None
    frameCount, imageCount = struct.unpack_from('<HH', b, 0)
    p = 4
    images = []
    try:
        for _ in range(imageCount):
            plen = struct.unpack_from('<I', b, p)[0]; p += 4
            if plen <= 0 or plen > 400 or p+plen > len(b): break
            path = b[p:p+plen].decode('ascii', 'replace'); p += plen
            images.append(path.replace('\\', '/'))
    except struct.error:
        pass
    # 兜底: 直接正则抓 .img 路径
    if not images:
        for m in re.finditer(rb'[ -~]{6,}\.img', b):
            images.append(m.group(0).decode('ascii', 'replace').replace('\\', '/'))
    # 抓第一处合理的 (posX,posY): 两个相邻 i32 落在 [-2000,2000] 且至少一个非0
    posX = posY = 0
    for off in range(p, min(len(b)-8, p+40)):
        x, y = struct.unpack_from('<ii', b, off)
        if -2000 <= x <= 2000 and -2000 <= y <= 2000 and (x or y):
            posX, posY = x, y; break
    # 帧率: 取第一个像 delay 的值(常见 20~200ms)
    delay = 50
    m = re.search(rb'[\x14\x1e\x28\x32\x3c\x50\x64]\x00\x00\x00', b[p:])
    if m: delay = struct.unpack_from('<i', m.group(0))[0]
    return dict(frameCount=frameCount, images=images, posX=posX, posY=posY,
               delay=max(20, delay))


if __name__ == '__main__':
    import sys
    sys.path.insert(0, __file__.rsplit('/', 1)[0])
    from pvf import Pvf
    pv = Pvf("地下城与勇士/Script.pvf")
    for path in sys.argv[1:] or ["character/swordman/effect/animation/gorecross/slash1.ani"]:
        a = parse_ani(pv.read(path))
        print(path, '->', a)
