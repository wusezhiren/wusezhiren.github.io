# DNF NPK / IMG (Neople Img File) 解码器
import struct, zlib
from PIL import Image

NPK_MAGIC=b'NeoplePack_Bill\x00'
IMG_MAGIC=b'Neople Img File\x00'

_NPK_NAME_KEY=(b"puchikon@neople dungeon and fighter "+b"DNF"*80)[:256]

def read_npk(path):
    """返回 [(index, bytes_of_img)], 不依赖文件名解密"""
    d=open(path,'rb').read()
    assert d[:16]==NPK_MAGIC, "not NPK"
    cnt=struct.unpack('<I', d[16:20])[0]
    out=[]
    for i in range(cnt):
        off,size=struct.unpack('<II', d[20+i*264:20+i*264+8])
        out.append((i, d[off:off+size]))
    return out

def read_npk_names(path):
    """返回 [(index, img内部路径名, off, size)]。文件名用 puchikon 密钥 XOR 解密。"""
    d=open(path,'rb').read()
    assert d[:16]==NPK_MAGIC, "not NPK"
    cnt=struct.unpack('<I', d[16:20])[0]
    out=[]
    for i in range(cnt):
        rec=d[20+i*264:20+i*264+264]
        off,size=struct.unpack('<II', rec[0:8])
        raw=rec[8:264]
        name=bytes(raw[j]^_NPK_NAME_KEY[j] for j in range(256)).split(b'\x00')[0].decode('ascii','replace')
        out.append((i, name, off, size))
    return out

def _argb1555(buf,w,h):
    out=bytearray(w*h*4)
    for i in range(w*h):
        v=buf[i*2]|(buf[i*2+1]<<8)
        a=255 if (v>>15)&1 else 0
        r=((v>>10)&0x1f)<<3; g=((v>>5)&0x1f)<<3; b=(v&0x1f)<<3
        out[i*4:i*4+4]=bytes((r,g,b,a))
    return bytes(out)

def _argb4444(buf,w,h):
    out=bytearray(w*h*4)
    for i in range(w*h):
        v=buf[i*2]|(buf[i*2+1]<<8)
        a=((v>>12)&0xf)*17; r=((v>>8)&0xf)*17; g=((v>>4)&0xf)*17; b=(v&0xf)*17
        out[i*4:i*4+4]=bytes((r,g,b,a))
    return bytes(out)

def _argb8888(buf,w,h):
    out=bytearray(w*h*4)
    for i in range(w*h):
        b,g,r,a=buf[i*4],buf[i*4+1],buf[i*4+2],buf[i*4+3]
        out[i*4:i*4+4]=bytes((r,g,b,a))
    return bytes(out)

def parse_img(img):
    """解析 v2 IMG, 返回 frames: list of dict{w,h,x,y,fw,fh,image(PIL or None for link),link}"""
    assert img[:16]==IMG_MAGIC, "not IMG"
    index_size,_z,ver,cnt=struct.unpack('<4I', img[16:32])
    frames=[]
    p=32
    metas=[]
    for i in range(cnt):
        form=struct.unpack('<i', img[p:p+4])[0]
        if form==0x11:  # LINK: form(4)+target(4)
            link=struct.unpack('<i', img[p+4:p+8])[0]; p+=8
            metas.append(('link',link)); continue
        comp,w,h,size,x,y,fw,fh=struct.unpack('<8i', img[p+4:p+36]); p+=36
        metas.append((form,comp,w,h,size,x,y,fw,fh))
    data=img[32+index_size:]
    dp=0
    for m in metas:
        if m[0]=='link':
            frames.append({'link':m[1],'w':0,'h':0,'x':0,'y':0,'fw':0,'fh':0,'image':None})
            continue
        (form,comp,w,h,size,x,y,fw,fh)=m
        raw=data[dp:dp+size]; dp+=size
        if comp==6:
            try: raw=zlib.decompress(raw)
            except: pass
        if w*h==0:
            frames.append({'link':-1,'w':0,'h':0,'x':x,'y':y,'fw':fw,'fh':fh,'image':None}); continue
        if form==0x0e:   px=_argb1555(raw,w,h)
        elif form==0x0f: px=_argb4444(raw,w,h)
        elif form==0x10: px=_argb8888(raw,w,h)
        else: px=bytes(w*h*4)  # 未支持格式占位
        im=Image.frombytes('RGBA',(w,h),px)
        frames.append({'link':-1,'w':w,'h':h,'x':x,'y':y,'fw':fw,'fh':fh,'image':im,'form':form})
    return {'version':ver,'count':cnt,'frames':frames}

if __name__=='__main__':
    import sys
    imgs=read_npk(sys.argv[1])
    print("NPK 内 IMG 数:",len(imgs))
    idx=int(sys.argv[2]) if len(sys.argv)>2 else 0
    info=parse_img(imgs[idx][1])
    print("img",idx,"ver",info['version'],"frames",info['count'])
    for i,f in enumerate(info['frames'][:12]):
        print(" frame",i,"wh",f['w'],f['h'],"off",f['x'],f['y'],"canvas",f['fw'],f['fh'],"link",f.get('link'))
