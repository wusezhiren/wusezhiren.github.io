# DNF Script.pvf 解码器(读 .ani 等脚本)。算法源自 PvfPlayer(ariakeumi) 逆向。
import struct, sys, os

def ror32(v,s): v&=0xFFFFFFFF; return ((v>>s)|(v<<(32-s)))&0xFFFFFFFF

def decrypt_block(buf, key):
    key&=0xFFFFFFFF
    out=bytearray(buf)
    n=len(out)&~3
    for i in range(0,n,4):
        enc=struct.unpack_from('<I',out,i)[0]
        dec=ror32((key ^ enc ^ 0x81A79011)&0xFFFFFFFF,6)
        struct.pack_into('<I',out,i,dec)
    return bytes(out)

class Pvf:
    def __init__(self, path):
        self.f=open(path,'rb').read()
        guidsize=struct.unpack_from('<i',self.f,0)[0]
        off=4+guidsize
        self.guid=self.f[4:4+guidsize]
        self.fileVersion,self.dirTreeLength,self.dirTreeChecksum,self.numFiles=struct.unpack_from('<iiii',self.f,off)
        off+=16
        self.headLen=off
        self.dataStart=self.headLen+self.dirTreeLength
        self._parse_tree()
    def _parse_tree(self):
        tree=self.f[self.headLen:self.headLen+self.dirTreeLength]
        dec=decrypt_block(tree, self.dirTreeChecksum)
        self.entries=[]; self.byPath={}
        p=0
        for _ in range(self.numFiles):
            fileNumber,pathLen=struct.unpack_from('<ii',dec,p); p+=8
            path=dec[p:p+pathLen].decode('ascii','replace'); p+=pathLen
            fileLen,fileChk,relOff=struct.unpack_from('<iii',dec,p); p+=12
            e=dict(num=fileNumber,path=path.replace('\\','/').lower(),length=fileLen,chk=fileChk,off=relOff)
            self.entries.append(e); self.byPath[e['path']]=e
    def read(self, path):
        e=self.byPath.get(path.replace('\\','/').lower())
        if not e: return None
        raw=self.f[self.dataStart+e['off']: self.dataStart+e['off']+ ((e['length']+3)&~3)]
        return decrypt_block(raw, e['chk'])[:e['length']]

if __name__=='__main__':
    pv=Pvf(sys.argv[1] if len(sys.argv)>1 else "地下城与勇士/Script.pvf")
    print("guid",pv.guid[:20],"ver",pv.fileVersion,"files",pv.numFiles,"treeLen",pv.dirTreeLength)
    print("--- 前20条路径 ---")
    for e in pv.entries[:20]: print("  ",e['num'],repr(e['path']),"len",e['length'])
    # 统计含 swordman 的脚本
    sw=[e['path'] for e in pv.entries if 'swordman' in e['path']]
    print("swordman 相关条目:",len(sw))
    for p in sw[:20]: print("   ",p)
