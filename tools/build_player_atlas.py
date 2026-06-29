# 导出鬼剑士(身体+武器)精灵图集 + JSON, 逐帧紧致裁切打包
# 每帧记录相对"脚底锚点"的绘制偏移, 内存友好
import sys,json,math,os; sys.path.insert(0,os.path.dirname(__file__))
from dnf_img import read_npk, parse_img
from PIL import Image

BASE="地下城与勇士/ImagePacks2/"
OUT="assets"
os.makedirs(OUT,exist_ok=True)

def load(npk,idx=0):
    return parse_img(read_npk(BASE+npk)[idx][1])['frames']

def resolve(F,i):
    f=F[i]
    if f['image'] is None and 0<=f.get('link',-1)<len(F): return F[f['link']]
    return f

def build(layers, name, scale=1.0):
    """layers: [frames,...] 同帧索引叠加; 第一层 frame0 定脚底锚点"""
    base=layers[0]
    n=len(base)
    # 脚底锚点(画布坐标): 站立帧身体中心x + 底部y
    f0=base[0]
    footX=f0['x']+f0['w']/2.0
    footY=f0['y']+f0['h']
    cells=[]  # 每帧: (PIL image or None, ox, oy)  ox,oy = 左上相对脚底(已缩放)
    for i in range(n):
        # 求该帧所有层的画布并集 bbox
        minx=miny=10**9; maxx=maxy=-10**9; has=False
        for F in layers:
            if i>=len(F): continue
            f=resolve(F,i)
            if f['image'] is None: continue
            has=True
            minx=min(minx,f['x']); miny=min(miny,f['y'])
            maxx=max(maxx,f['x']+f['w']); maxy=max(maxy,f['y']+f['h'])
        if not has:
            cells.append(None); continue
        cw,ch=maxx-minx,maxy-miny
        cell=Image.new('RGBA',(cw,ch),(0,0,0,0))
        for F in layers:
            if i>=len(F): continue
            f=resolve(F,i)
            if f['image'] is None: continue
            cell.alpha_composite(f['image'],(f['x']-minx,f['y']-miny))
        if scale!=1.0:
            cell=cell.resize((max(1,round(cw*scale)),max(1,round(ch*scale))))
        ox=(minx-footX)*scale; oy=(miny-footY)*scale
        cells.append((cell,round(ox,1),round(oy,1)))
    # shelf 打包(按高度降序)
    pad=1
    order=sorted([i for i,c in enumerate(cells) if c],key=lambda i:-cells[i][0].height)
    maxw=2048
    x=y=rowh=0
    rects={}
    for i in order:
        im=cells[i][0]; w,h=im.width+pad,im.height+pad
        if x+w>maxw: x=0; y+=rowh; rowh=0
        rects[i]=(x,y,im.width,im.height); x+=w; rowh=max(rowh,h)
    atlasH=y+rowh
    atlas=Image.new('RGBA',(maxw,atlasH),(0,0,0,0))
    frames=[None]*n
    for i in order:
        ax,ay,w,h=rects[i]; atlas.alpha_composite(cells[i][0],(ax,ay))
        frames[i]=[ax,ay,w,h,cells[i][1],cells[i][2]]  # sx,sy,sw,sh,ox,oy
    atlas.save(OUT+"/"+name+".png")
    meta={'count':n,'scale':scale,'frames':frames}  # foot 锚点即每帧 ox,oy 原点
    json.dump(meta,open(OUT+"/"+name+".json",'w'),separators=(',',':'))
    sz=os.path.getsize(OUT+"/"+name+".png")
    print("%s: atlas %dx%d, %d帧(%d有效), PNG %.0fKB"%(name,maxw,atlasH,n,len(order),sz/1024))

if __name__=='__main__':
    body=load("sprite_character_swordman_equipment_avatar_skin.NPK",0)
    weap=load("sprite_character_swordman_equipment_weapon_lswd.NPK",0)
    build([body,weap], "swordman", scale=1.0)
