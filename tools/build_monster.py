# 通用怪物精灵图集导出: 单层, 逐帧紧致裁切打包 + 带帧号 montage
import json,math,os,sys; sys.path.insert(0,os.path.dirname(__file__))
from dnf_img import read_npk, parse_img
from PIL import Image, ImageDraw
BASE="地下城与勇士/ImagePacks2/"; OUT="assets"; os.makedirs(OUT,exist_ok=True)
def resolve(F,i):
    f=F[i]
    if f['image'] is None and 0<=f.get('link',-1)<len(F): return F[f['link']]
    return f
def build(npk, name, img_idx=0, scale=1.0, montage=True):
    F=parse_img(read_npk(BASE+npk)[img_idx][1])['frames']; n=len(F)
    # 站立帧(0)定脚底锚点
    f0=resolve(F,0); footX=f0['x']+f0['w']/2.0; footY=f0['y']+f0['h']
    cells=[]
    for i in range(n):
        f=resolve(F,i)
        if f['image'] is None: cells.append(None); continue
        im=f['image']
        if scale!=1.0: im=im.resize((max(1,round(im['w']*scale)) if False else max(1,round(f['w']*scale)),max(1,round(f['h']*scale))))
        ox=(f['x']-footX)*scale; oy=(f['y']-footY)*scale
        cells.append((im,round(ox,1),round(oy,1)))
    pad=1; order=sorted([i for i,c in enumerate(cells) if c],key=lambda i:-cells[i][0].height)
    maxw=2048; x=y=rowh=0; rects={}
    for i in order:
        im=cells[i][0]; w,h=im.width+pad,im.height+pad
        if x+w>maxw: x=0;y+=rowh;rowh=0
        rects[i]=(x,y,im.width,im.height); x+=w; rowh=max(rowh,h)
    atlas=Image.new('RGBA',(maxw,y+rowh),(0,0,0,0)); frames=[None]*n
    for i in order:
        ax,ay,w,h=rects[i]; atlas.alpha_composite(cells[i][0],(ax,ay))
        frames[i]=[ax,ay,w,h,cells[i][1],cells[i][2]]
    atlas.save(OUT+"/"+name+".png")
    json.dump({'count':n,'scale':scale,'frames':frames},open(OUT+"/"+name+".json",'w'),separators=(',',':'))
    sz=os.path.getsize(OUT+"/"+name+".png")
    print("%s: atlas %dx%d, %d帧(%d有效), %.0fKB"%(name,maxw,y+rowh,n,len(order),sz/1024))
    if montage:
        cols=14; cell=72; rows=math.ceil(n/cols)
        m=Image.new('RGBA',(cols*cell,rows*cell),(35,40,52,255)); dr=ImageDraw.Draw(m)
        for i in range(n):
            bx=(i%cols)*cell; by=(i//cols)*cell
            if cells[i]:
                im=cells[i][0]; s=min((cell-14)/max(im.width,1),(cell-14)/max(im.height,1),1)
                im2=im.resize((max(1,int(im.width*s)),max(1,int(im.height*s)))); m.alpha_composite(im2,(bx+(cell-im2.width)//2,by+cell-12-im2.height))
            dr.text((bx+2,by+2),str(i),fill=(255,210,80))
        m.save("tools/_extract/"+name+"_idx.png")
if __name__=='__main__':
    picks=[
     ("sprite_monster_eventgoblin.NPK","mon_gob",0),
     ("sprite_monster_abnova_stone_orc.NPK","mon_orc",0),
     ("sprite_monster_darkelftemple_grave_archer.NPK","mon_archer",0),
     ("sprite_monster_abnova_lion.NPK","mon_charger",0),
     ("sprite_monster_slime.NPK","mon_bomber",0),
     ("sprite_monster_abnova_named_kavika.NPK","mon_boss",0),
    ]
    for npk,name,idx in picks:
        try: build(npk,name,idx)
        except Exception as e: print(name,"ERR",e)
