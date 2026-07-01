# 抽取技能特效精灵 → 单张图集 assets/skillfx.png + skillfx.json + skillfx.meta.js
# 每个 clip 保留每帧的原生偏移(IMG 帧 x,y), 运行时以"施放点"为原点 +偏移*scale 绘制(加色混合)
import sys,os,json; sys.path.insert(0,os.path.dirname(__file__))
from dnf_img import read_npk, parse_img
from PIL import Image
BASE="地下城与勇士/ImagePacks2/sprite_character_swordman_effect_"
OUT="assets"

# clip名 : (npk, img索引(None=自动按主特效面积选), 最多帧数)
SPEC = {
 # 剑魂
 'tripleslash':   ('tripleslash',   None, 12),
 'flashcut':      ('flashcut',      6, 12),     # 白色X斩(拔刀)
 'dragonup':      ('atdragonup',    None, 14),
 'revolvingsword':('atrevolvingsword',None,12),
 'illusionslash': ('illusionslash', None, 12),
 'hiddenblade':   ('athiddenblade', 1, 10),
 'uppercut':      ('atupperslash',  None, 10),  # 上挑(通用Z)
 # 狂战
 'gorecross':     ('gorecross',     1, 12),     # 火焰十字
 'mountaincrash': ('atmountaincrash',None, 10),
 'souldrain':     ('atsouldrain',   None, 12),
 'frenzy':        ('atfrenzy',      None, 8),
 'bloodseal':     ('atbloodseal',   None, 12),
 'chargecrash':   ('chargecrash',   None, 12),
 # 鬼泣
 'darkslash':     ('atdarkslash',   None, 10),
 'liftslash':     ('atliftslash',   None, 10),
 'saya':          ('sayaex',        6, 12),      # 冰爆
 'epidemic':      ('epidemicrasa',  None, 12),
 'ghoststep':     ('ghoststep',     4, 12),      # 蓝色鬼魂身影
 'tombstone':     ('tombstoneex',   None, 12),
 # 阿修罗
 'normalwave':    ('normalwave',    None, 10),
 'icewave':       ('icewaveex',     None, 6),
 'firewave':      ('firewave',      None, 12),
 'waveeye':       ('waveeye',       None, 12),
 'wavespin':      ('wavespinarea',  None, 10),
 'vajra':         ('vajra',         None, 14),
 # buff / 标识
 'wavemark':      ('wavemark',      None, 4),
 'wavemurderous': ('wavemurderous', None, 4),
 'descentsoul':   ('descentsoul',   None, 8),
}

def res(F,i):
    f=F[i]
    if f['image'] is None and 0<=f.get('link',-1)<len(F): return F[f['link']]
    return f

def load_clip(npk, imgidx, maxf):
    e=read_npk(BASE+npk+".NPK")
    if imgidx is None:
        # 选"主特效图": 按有效帧的平均画面面积最大(主效果通常最大最完整, 子层是小火花/拖影)
        best,bestscore=0,-1
        for i,(n,d) in enumerate(e):
            try:
                fr=parse_img(d)['frames']
                areas=[f['w']*f['h'] for f in fr if f['image'] is not None]
                if len(areas)<2: continue   # 跳过单帧(多为静态大闪光)
                score=(sum(areas)/len(areas))*min(len(areas),8)  # 又大又有动画者为主特效
                if score>bestscore: bestscore,best=score,i
            except: pass
        imgidx=best
    F=parse_img(e[imgidx][1])['frames']
    valid=[i for i in range(len(F)) if res(F,i)['image'] is not None]
    if len(valid)>maxf:
        step=len(valid)/maxf
        valid=[valid[int(k*step)] for k in range(maxf)]
    out=[]
    for i in valid:
        f=res(F,i)
        out.append({'im':f['image'],'fx':f['x'],'fy':f['y']})
    return out

# 收集所有帧, shelf 打包
clips={}; allcells=[]
for name,(npk,idx,mf) in SPEC.items():
    try:
        frames=load_clip(npk,idx,mf)
        clips[name]=frames
        for fr in frames: allcells.append((name,fr))
    except Exception as ex:
        print("跳过",name,ex)

pad=1; maxw=2048
order=sorted(range(len(allcells)),key=lambda k:-allcells[k][1]['im'].height)
x=y=rowh=0; rects={}
for k in order:
    im=allcells[k][1]['im']; w,h=im.width+pad,im.height+pad
    if x+w>maxw: x=0;y+=rowh;rowh=0
    rects[k]=(x,y,im.width,im.height); x+=w; rowh=max(rowh,h)
H=y+rowh
atlas=Image.new('RGBA',(maxw,H),(0,0,0,0))
for k in order:
    ax,ay,w,h=rects[k]; atlas.alpha_composite(allcells[k][1]['im'],(ax,ay))
# 写每帧矩形回 clips
meta={}
ci=0
for name,frames in clips.items():
    arr=[]
    for fr in frames:
        # 找它在 allcells 的索引
        pass
    meta[name]=[]
# 重新映射: 用 id() 对齐
idmap={id(allcells[k][1]):rects[k] for k in range(len(allcells))}
for name,frames in clips.items():
    arr=[]
    for fr in frames:
        ax,ay,w,h=idmap[id(fr)]
        arr.append([ax,ay,w,h,fr['fx'],fr['fy']])
    meta[name]=arr

atlas.save(OUT+"/skillfx.png")
data={'frames':meta}
json.dump(data,open(OUT+"/skillfx.json",'w'),separators=(',',':'))
open(OUT+"/skillfx.meta.js",'w').write("window.SKILLFX_META="+json.dumps(data,separators=(',',':'))+";")
print("skillfx: atlas %dx%d, %d clips, PNG %.0fKB"%(maxw,H,len(clips),os.path.getsize(OUT+"/skillfx.png")/1024))
for n,a in meta.items(): print("  %-16s %d帧"%(n,len(a)))
