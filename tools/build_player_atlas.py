# 导出鬼剑士【身体】与【各武器】为独立图集(共用同一脚底锚点), 运行时按职业/装备叠加武器层
# 这样可换武器外观(剑魂光剑/太刀等)+狂战副手血刃(同一武器层二次绘制并染色)
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

def build_single(F, name, footX, footY, scale=1.0):
    """单层逐帧紧致打包, ox/oy 相对传入的统一脚底锚点(像素)。返回 meta dict。"""
    n=len(F)
    cells=[]
    for i in range(n):
        f=resolve(F,i)
        if f['image'] is None: cells.append(None); continue
        im=f['image']
        if scale!=1.0: im=im.resize((max(1,round(f['w']*scale)),max(1,round(f['h']*scale))))
        ox=(f['x']-footX)*scale; oy=(f['y']-footY)*scale
        cells.append((im,round(ox,1),round(oy,1)))
    pad=1; maxw=2048
    order=sorted([i for i,c in enumerate(cells) if c],key=lambda i:-cells[i][0].height)
    x=y=rowh=0; rects={}
    for i in order:
        im=cells[i][0]; w,h=im.width+pad,im.height+pad
        if x+w>maxw: x=0;y+=rowh;rowh=0
        rects[i]=(x,y,im.width,im.height); x+=w; rowh=max(rowh,h)
    H=y+rowh
    atlas=Image.new('RGBA',(maxw,H),(0,0,0,0))
    frames=[None]*n
    for i in order:
        ax,ay,w,h=rects[i]; atlas.alpha_composite(cells[i][0],(ax,ay))
        frames[i]=[ax,ay,w,h,cells[i][1],cells[i][2]]
    atlas.save(OUT+"/"+name+".png")
    meta={'count':n,'scale':scale,'frames':frames}
    json.dump(meta,open(OUT+"/"+name+".json",'w'),separators=(',',':'))
    print("%s: %dx%d, %d帧(%d有效) %.0fKB"%(name,maxw,H,n,len(order),os.path.getsize(OUT+"/"+name+".png")/1024))
    return meta

if __name__=='__main__':
    body=load("sprite_character_swordman_equipment_avatar_skin.NPK",0)
    # 统一脚底锚点 = 身体 frame0 的 中心x + 底部y
    f0=body[0]; footX=f0['x']+f0['w']/2.0; footY=f0['y']+f0['h']
    bmeta=build_single(body,"swordman",footX,footY,1.0)
    # 各武器层(共用同一锚点)
    WEAPONS={
      'lswd':   "sprite_character_swordman_equipment_weapon_lswd.NPK",   # 太刀(默认)
      'beamswd':"sprite_character_swordman_equipment_weapon_beamswd.NPK",# 光剑(剑魂)
    }
    wmeta={}
    for key,npk in WEAPONS.items():
        wmeta[key]=build_single(load(npk,0),"weapon_"+key,footX,footY,1.0)
    # 合并 meta.js (file:// 可用)
    open(OUT+"/swordman.meta.js",'w').write("window.SWORDMAN_META="+json.dumps(bmeta,separators=(',',':'))+";")
    open(OUT+"/weapons.meta.js",'w').write("window.WEAPON_META="+json.dumps(wmeta,separators=(',',':'))+";")
    print("done. weapons:",list(wmeta.keys()))
