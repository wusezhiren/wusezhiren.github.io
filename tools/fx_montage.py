# 批量渲染特效 NPK 的接触表(每个NPK一行, img0 取若干帧), 用于肉眼匹配技能
import sys,os; sys.path.insert(0,os.path.dirname(__file__))
from dnf_img import read_npk, parse_img
from PIL import Image, ImageDraw
BASE="地下城与勇士/ImagePacks2/sprite_character_swordman_effect_"
OUT=sys.argv[1] if len(sys.argv)>1 else "/tmp/fx.png"
names=sys.argv[2:]
def res(F,i):
    f=F[i]
    if f['image'] is None and 0<=f.get('link',-1)<len(F): return F[f['link']]
    return f
cw,ch=130,120; cols=8
rowh=ch+4; labelw=170
sheet=Image.new('RGBA',(labelw+cw*cols, rowh*len(names)),(18,18,26,255))
d=ImageDraw.Draw(sheet)
for r,nm in enumerate(names):
    y0=r*rowh
    d.text((4,y0+4),nm,fill=(255,230,80,255))
    try:
        e=read_npk(BASE+nm+".NPK")
        # 选帧最多的 img 作为主特效
        best=0;bestn=0
        for i,(n,dat) in enumerate(e):
            try:
                fr=parse_img(dat)['frames']; cnt=sum(1 for f in fr if f['image'] is not None)
                if cnt>bestn: bestn=cnt;best=i
            except: pass
        F=parse_img(e[best][1])['frames']
        valid=[i for i in range(len(F)) if res(F,i)['image'] is not None]
        d.text((4,y0+22),'img%d/%d f%d'%(best,len(e),len(valid)),fill=(150,150,160,255))
        step=max(1,len(valid)//cols)
        pick=valid[::step][:cols]
        for c,i in enumerate(pick):
            f=res(F,i); im=f['image']
            s=min(cw/max(1,im.width),(ch-2)/max(1,im.height),1.0)
            im2=im.resize((max(1,int(im.width*s)),max(1,int(im.height*s))))
            sheet.alpha_composite(im2,(labelw+c*cw+(cw-im2.width)//2, y0+(ch-im2.height)//2))
    except Exception as ex:
        d.text((labelw+4,y0+40),'ERR '+str(ex)[:40],fill=(255,80,80,255))
sheet.save(OUT); print('saved',OUT,'rows',len(names))
