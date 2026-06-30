# 平铺一个特效 NPK 的【所有 img】(每 img 取中间有效帧), 用于挑主特效图
import sys,os; sys.path.insert(0,os.path.dirname(__file__))
from dnf_img import read_npk, parse_img
from PIL import Image, ImageDraw
BASE="地下城与勇士/ImagePacks2/sprite_character_swordman_effect_"
OUT=sys.argv[1]; npk=sys.argv[2]
e=read_npk(BASE+npk+".NPK")
def res(F,i):
    f=F[i]
    if f['image'] is None and 0<=f.get('link',-1)<len(F): return F[f['link']]
    return f
cells=[]
for i,(n,dat) in enumerate(e):
    try:
        F=parse_img(dat)['frames']
        valid=[k for k in range(len(F)) if res(F,k)['image'] is not None]
        if not valid: continue
        mid=valid[len(valid)//2]; f=res(F,mid)
        cells.append((i,f['image'],len(valid),f['w'],f['h']))
    except: pass
cw,ch=150,150; cols=8; rows=(len(cells)+cols-1)//cols
sheet=Image.new('RGBA',(cols*cw,rows*ch),(18,18,26,255)); d=ImageDraw.Draw(sheet)
for k,(i,im,nv,w,h) in enumerate(cells):
    cx=(k%cols)*cw; cy=(k//cols)*ch
    s=min(cw/max(1,im.width),(ch-22)/max(1,im.height),1.0)
    im2=im.resize((max(1,int(im.width*s)),max(1,int(im.height*s))))
    sheet.alpha_composite(im2,(cx+(cw-im2.width)//2,cy+20+(ch-20-im2.height)//2))
    d.text((cx+2,cy+2),'img%d f%d %dx%d'%(i,nv,w,h),fill=(255,230,80,255))
sheet.save(OUT); print('saved',OUT,'imgs',len(cells))
