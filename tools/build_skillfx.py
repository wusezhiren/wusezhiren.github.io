# v2: 按 .ani 多图层合成技能特效 → assets/skillfx.png + skillfx.json + skillfx.meta.js
# 层类(LAYERED): 从 PVF 的 effect/animation/<folder>/*.ani 取每层 img+锚点(posX,posY)+帧率, 叠放。
# 单图类(SINGLE): 没有独立.ani, 直接按名字取 NPK 内正确的主视觉 img(native偏移当锚点)。
# 输出数据模型: {clips:{name:{layers:[{anchor:[ax,ay],fps,frames:[[sx,sy,sw,sh,fx,fy],...]}]}}}
import sys,os,json,glob,collections; sys.path.insert(0,os.path.dirname(__file__))
from pvf import Pvf
from ani import parse_ani
from dnf_img import read_npk, read_npk_names, parse_img
from PIL import Image

IP="地下城与勇士/ImagePacks2/"
PFX="sprite_character_swordman_effect_"
OUT="assets"
pv=Pvf("地下城与勇士/Script.pvf")

# ---- 全局 img 索引: basename -> [(npkstem, idx)] (跨所有effect NPK, .ani引用的img可能在别的NPK) ----
print("建立全局img索引...")
base2loc=collections.defaultdict(list)
for f in glob.glob(IP+PFX+"*.NPK"):
    stem=os.path.basename(f)[len(PFX):-4]
    try:
        for i,n,_,_ in read_npk_names(f):
            base2loc[n.split('/')[-1].lower()].append((stem,i))
    except: pass
_npk_cache={}
def npk_data(stem):
    if stem not in _npk_cache:
        _npk_cache[stem]=dict((i,d) for i,d in read_npk(IP+PFX+stem+".NPK"))
    return _npk_cache[stem]
def bad_variant(name):
    n=name.lower()
    return n.startswith('(18)') or n.startswith('(tn)') or '18eye' in n

def load_frames(basename, prefer_npk=None, maxf=14):
    """返回该img的帧列表 [{image,x,y}], 优先 prefer_npk, 跳过(18)/(tn)变体。"""
    bn=basename.lower()
    locs=base2loc.get(bn,[])
    if not locs: return None
    locs=sorted(locs, key=lambda l:(l[0]!=prefer_npk,))  # prefer_npk 优先
    stem,idx=locs[0]
    data=npk_data(stem)[idx]
    P=parse_img(data); F=P['frames']
    def res(i):
        f=F[i]
        if f['image'] is None and 0<=f.get('link',-1)<len(F): return F[f['link']]
        return f
    valid=[i for i in range(len(F)) if res(i)['image'] is not None]
    if len(valid)>maxf:
        step=len(valid)/maxf; valid=[valid[int(k*step)] for k in range(maxf)]
    return [res(i) for i in valid]

def ani_layer(folder, name, prefer_npk):
    raw=pv.read("character/swordman/effect/animation/%s/%s.ani"%(folder,name))
    if raw is None: return None
    a=parse_ani(raw)
    if not a or not a['images']: return None
    img=a['images'][0].split('/')[-1]
    fr=load_frames(img, prefer_npk)
    if not fr: return None
    fps=max(8, round(1000.0/max(20,a['delay'])))
    return dict(frames=fr, ax=a['posX'], ay=a['posY'], fps=fps)

def single_layer(basename, prefer_npk, fps=16):
    fr=load_frames(basename, prefer_npk)
    if not fr: return None
    return dict(frames=fr, ax=0, ay=0, fps=fps)

# ---- 层类: (folder, npk偏好, [(folder,layer)...]) 只取 normal 层 ----
LAYERED={
 'gorecross':      ('gorecross',[('gorecross','slash1'),('gorecross','slash2')]),
 'tripleslash':    ('tripleslash',[('tripleslash','slash1'),('tripleslash','slash2'),('tripleslash','slash3')]),
 'illusionslash':  ('illusionslash',[('illusionslash','upper'),('illusionslash','smash')]),
 'chargecrash':    ('chargecrash',[('chargecrash','charge'),('chargecrash','dash'),('chargecrash','down-slash'),('chargecrash','up-slash'),('chargecrash','dustdash')]),
 'ghoststep':      ('ghoststep',[('ghoststepslash','slash1'),('ghoststepslash','slash2'),('ghoststepslash','skull'),('ghoststep','appear1'),('ghoststep','appear2')]),
 'waveeye':        ('waveeye',[('waveeye','wing1'),('waveeye','wing2'),('waveeye','attack1')]),
 'wavespin':       ('wavespinarea',[('wavespinarea','createbeadnormal'),('wavespinarea','circle'),('wavespinarea','circlefront'),('wavespinarea','hold')]),
 'frenzy':         ('atfrenzy',[('frenzy','cast'),('frenzy','blast'),('frenzy','sword1-1'),('frenzy','sword1-3'),('frenzy','sword1-4'),('frenzy','ball'),('frenzy','buff')]),
}
# ---- 单图类: clip -> (npk偏好, [img basename...]) ----
SINGLE={
 'flashcut':      ('flashcut',['ld_sworda.img','ld_swordb.img','ld_finisheff_b.img']),
 'dragonup':      ('atdragonup',['4sword.img','twister_big.img','blast_normal.img']),
 'revolvingsword':('atrevolvingsword',['revolvingsword.img','revolvingsword_eff.img']),
 'hiddenblade':   ('athiddenblade',['atk_02.img','atk_03.img']),
 'uppercut':      ('atupperslash',['upper_eff.img','upper_dash.img']),
 'mountaincrash': ('atmountaincrash',['mountaincrash_sword.img','mountaincrash_force.img']),
 'souldrain':     ('atsouldrain',['start01.img','firstboom01.img','loop01.img']),
 'bloodseal':     ('atbloodseal',['blood_shot.img','blood_finish.img','blood_bull01.img']),
 'darkslash':     ('atdarkslash',['darkslash_normal.img']),
 'liftslash':     ('atliftslash',['lift_slash.img']),
 'saya':          ('sayaex',['readynormal.img','icenormal.img']),
 'epidemic':      ('epidemicrasa',['rasa.img','rasa_glow.img']),
 'tombstone':     ('tombstoneex',['stonestartupnormal.img','stoneendupnormal.img','explosionnormal125.img']),
 'normalwave':    ('normalwave',['waveboom_normal.img']),
 'icewave':       ('icewaveex',['ice_normal_down.img','ice_dodge_middle.img']),
 'firewave':      ('firewave',['fire_normal.img','blast-front.img','sword_normal.img']),
 'vajra':         ('vajra',['vajra_maincloud.img','vajra_lightning_a.img','vajra_start_eff.img']),
 # buff 标识
 'wavemark':      ('wavemark',['font.img','wave.img']),
 'wavemurderous': ('wavemurderous',['wave.img']),
 'descentsoul':   ('descentsoul',['descentsoul_00.img','descentsoul_light.img']),
}

clips={}
for clip,(prefer,layerspec) in LAYERED.items():
    layers=[]
    for folder,name in layerspec:
        L=ani_layer(folder,name,prefer)
        if L: layers.append(L)
        else: print("  [层缺] %s/%s"%(folder,name))
    if layers: clips[clip]=layers; print("LAYERED %-14s %d层"%(clip,len(layers)))
for clip,(prefer,imgs) in SINGLE.items():
    layers=[]
    for img in imgs:
        L=single_layer(img,prefer)
        if L: layers.append(L)
    if layers: clips[clip]=layers; print("SINGLE  %-14s %d层"%(clip,len(layers)))
    else: print("  [单图缺] %s %s"%(clip,imgs))

# ---- 打包 atlas ----
cells=[]  # (image, ownerRef)
for clip,layers in clips.items():
    for L in layers:
        for f in L['frames']:
            cells.append(f)
pad=1; maxw=2048
order=sorted(range(len(cells)),key=lambda k:-cells[k]['image'].height)
x=y=rowh=0; rects={}
for k in order:
    im=cells[k]['image']; w,h=im.width+pad,im.height+pad
    if x+w>maxw: x=0;y+=rowh;rowh=0
    rects[k]=(x,y,im.width,im.height); x+=w; rowh=max(rowh,h)
H=y+rowh
atlas=Image.new('RGBA',(maxw,H),(0,0,0,0))
for k in order: atlas.alpha_composite(cells[k]['image'],(rects[k][0],rects[k][1]))
idmap={id(cells[k]):rects[k] for k in range(len(cells))}

data={'clips':{}}
for clip,layers in clips.items():
    L2=[]
    for L in layers:
        frs=[]
        for f in L['frames']:
            ax,ay,w,h=idmap[id(f)]
            frs.append([ax,ay,w,h,f['x'],f['y']])
        L2.append({'anchor':[L['ax'],L['ay']],'fps':L['fps'],'frames':frs})
    data['clips'][clip]=L2

atlas.save(OUT+"/skillfx.png")
json.dump(data,open(OUT+"/skillfx.json",'w'),separators=(',',':'))
open(OUT+"/skillfx.meta.js",'w').write("window.SKILLFX_META="+json.dumps(data,separators=(',',':'))+";")
print("\nskillfx v2: atlas %dx%d, %d clips, %d帧, PNG %.0fKB"%(maxw,H,len(clips),len(cells),os.path.getsize(OUT+"/skillfx.png")/1024))
