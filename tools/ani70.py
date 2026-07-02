# 结构化解析 DNF PVF 内编译的 70ani(特效层与身体动作通用)。
# 布局(逆向自 DOF 70 Script.pvf):
#   u16 frameCount, u16 imageCount, imageCount×(u32 pathLen + ascii path)
#   u16 nGlobalAttr, nGlobalAttr×attr
#   每帧: u16 boxCount; boxCount×(u16 boxKw + 6×i32)
#         i16 imgIdx(-1=空帧; >=0 时再跟 u16 imgFrame)
#         i32 posX; i32 posY; u16 nattr; nattr×attr
#   attr = u16 kw + 参数, 参数宽度按 kw:
#     kw0 LOOP(u8) kw1 SHADOW(u8) kw7 IMAGE RATE(2×float) kw8 IMAGE ROTATE(float)
#     kw9 RGBA(4字节) kw10 INTERPOLATION(u8) kw11 GRAPHIC EFFECT(u16, 2=加色)
#     kw12 DELAY(i32 ms) kw16 PLAY SOUND(i32 len + ascii) kw24 (u16)
#   稀有 kw 宽度不定, 逐文件回溯 + 数值合理性校验裁决。
import struct

KNOWN_KW = {0: 1, 1: 1, 7: 8, 8: 4, 9: 4, 10: 1, 11: 2, 12: 4, 16: 'str', 24: 2, 25: 0}
_CAND = (4, 2, 8, 1, 0, 'str')


def _parse(b, kw_sizes, unknown_out=None):
    if not b or len(b) < 8:
        return None
    fc, ic = struct.unpack_from('<HH', b, 0)
    p = 4
    imgs = []
    for _ in range(ic):
        if p + 4 > len(b):
            return None
        pl = struct.unpack_from('<I', b, p)[0]
        if pl <= 0 or pl > 400 or p + 4 + pl > len(b):
            return None
        p += 4
        imgs.append(b[p:p + pl].decode('ascii', 'replace').replace('\\', '/'))
        p += pl
    pos = [p]
    n = len(b)

    class _EOF(Exception):
        pass

    def rd(fmt, sz):
        if pos[0] + sz > n:
            raise _EOF
        v = struct.unpack_from(fmt, b, pos[0])[0]
        pos[0] += sz
        return v

    def attr():
        kw = rd('<H', 2)
        sz = kw_sizes.get(kw)
        if sz is None:
            if unknown_out is not None:
                unknown_out.append(kw)
            raise _EOF
        if sz == 0:
            return kw, True
        if sz == 'str':
            ln = rd('<i', 4)
            if ln < 0 or ln > 2000:
                raise _EOF
            s = b[pos[0]:pos[0] + ln].decode('ascii', 'replace')
            pos[0] += ln
            return kw, s
        if sz == 8:
            return kw, (rd('<f', 4), rd('<f', 4))
        if sz == 1:
            return kw, rd('<B', 1)
        if sz == 2:
            return kw, rd('<H', 2)
        return kw, rd('<i', 4)

    frames = []
    gattrs = []
    try:
        ng = rd('<H', 2)
        if ng > 20:
            return None
        for _ in range(ng):
            gattrs.append(attr())
        for _ in range(fc):
            nbox = rd('<H', 2)
            if nbox > 40:
                return None
            boxes = []
            for _ in range(nbox):
                bkw = rd('<H', 2)
                boxes.append((bkw, [rd('<i', 4) for _ in range(6)]))
            img_idx = rd('<h', 2)
            img_frame = -1
            if img_idx >= 0:
                img_frame = rd('<H', 2)
            px = rd('<i', 4)
            py = rd('<i', 4)
            if not (-4000 <= px <= 4000 and -4000 <= py <= 4000):
                return None
            if img_idx >= ic + 4 or img_frame > 4096:
                return None
            na = rd('<H', 2)
            if na > 25:
                return None
            delay = 100
            attrs = {}
            for _ in range(na):
                kw, v = attr()
                if kw == 12:
                    if not (0 <= v <= 100000000):
                        return None
                    delay = v
                else:
                    attrs.setdefault(kw, []).append(v)
            frames.append(dict(imgIdx=max(0, img_idx) if img_idx >= 0 else -1,
                               imgFrame=img_frame, x=px, y=py,
                               delay=max(10, delay), attrs=attrs, boxes=boxes))
    except _EOF:
        return None
    if len(frames) != fc or pos[0] != n:
        return None
    return dict(frames=frames, images=imgs, gattrs=dict(gattrs), fc=fc)


def parse_ani70(b, extra_kw=None):
    """结构化解析编译 70ani; 稀有属性宽度逐文件回溯裁决。失败返回 None。"""
    base = dict(KNOWN_KW)
    if extra_kw:
        base.update(extra_kw)
    budget = [0]

    def bt(sizes):
        budget[0] += 1
        if budget[0] > 4000:
            return None
        unk = []
        r = _parse(b, sizes, unk)
        if r is not None:
            return r
        if not unk:
            return None
        kw = unk[0]
        for cand in _CAND:
            nxt = dict(sizes)
            nxt[kw] = cand
            r = bt(nxt)
            if r is not None:
                return r
        return None

    return bt(base)
