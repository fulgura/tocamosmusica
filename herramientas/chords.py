import re, itertools
NAMES=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
PCN={'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}
OPEN=[4,9,2,7,11,4]
def pc(n):
    v=PCN[n[0].upper()]
    if len(n)>1: v+= 1 if n[1]=='#' else -1
    return v%12
QUAL={'':([0,4,7],[]),'m':([0,3,7],[]),'7':([0,4,7,10],[7]),'m7':([0,3,7,10],[7]),'maj7':([0,4,7,11],[7]),
      '5':([0,7],[]),'sus4':([0,5,7],[]),'sus2':([0,2,7],[]),'dim':([0,3,6],[]),'m6':([0,3,7,9],[7]),'6':([0,4,7,9],[7])}
ALIAS={'':'','m':'m','min':'m','7':'7','m7':'m7','7M':'maj7','maj7':'maj7','M7':'maj7','5':'5','4':'sus4','sus4':'sus4','sus2':'sus2',
       'dim':'dim','°':'dim','º':'dim','m6':'m6','6':'6'}
TOK=re.compile(r'^([A-G][#b]?)([^/]*?)(?:/([A-Ga-g][#b]?))?$')
def canon(tok):
    """token -> (key, rootpc, qual, basspc) or None. key uses sharp spelling."""
    t=tok.strip('()').rstrip('.')
    m=TOK.match(t)
    if not m: return None
    r,q,b=m.groups()
    if q not in ALIAS: return None
    q=ALIAS[q]
    rp=pc(r); bp=pc(b) if b else rp
    key=NAMES[rp]+q+('/'+NAMES[bp] if b and bp!=rp else '')
    return key,rp,q,bp
def valid(fr,rp,q,bp):
    ivs,opt=QUAL[q]
    chord={(rp+i)%12 for i in ivs}|{bp}; req={(rp+i)%12 for i in ivs if i not in opt}
    snd=[(i,(OPEN[i]+f)%12) for i,f in enumerate(fr) if f>=0]
    if len(snd)<3: return False
    pcs={p for _,p in snd}
    if not pcs<=chord or not req<=pcs: return False
    return snd[0][1]==bp
def barre(fr):
    fz=[(i,f) for i,f in enumerate(fr) if f>0]
    if not fz: return None
    m=min(f for _,f in fz); idx=[i for i,f in fz if f==m]
    if len(idx)<2 or (len(idx)==2 and len(fz)<=4): return None
    lo,hi=min(idx),max(idx)
    for i in range(lo,hi+1):
        if fr[i]<m: return None   # muted(-1) or open(0) inside
    return [m,lo,hi]
def fingers(fr):
    b=barre(fr); fz=[(i,f) for i,f in enumerate(fr) if f>0]
    if b: return 1+len({i for i,f in fz if f>b[0]})
    return len(fz)
def span_ok(fr):
    fz=[f for f in fr if f>0]
    return not fz or max(fz)-min(fz)<=3
def pack(fr):
    fz=[f for f in fr if f>0]
    base=1 if (not fz or max(fz)<=4) else min(fz)
    return {'f':list(fr),'b':barre(fr),'base':base}
CUR={'C':[-1,3,2,0,1,0],'D':[-1,-1,0,2,3,2],'G':[3,2,0,0,0,3],'E':[0,2,2,1,0,0],'A':[-1,0,2,2,2,0],'Am':[-1,0,2,2,1,0],'Em':[0,2,2,0,0,0],
 'Dm':[-1,-1,0,2,3,1],'C7':[-1,3,2,3,1,0],'D7':[-1,-1,0,2,1,2],'E7':[0,2,0,1,0,0],'G7':[3,2,0,0,0,1],'A7':[-1,0,2,0,2,0],'B7':[-1,2,1,2,0,2],
 'Cmaj7':[-1,3,2,0,0,0],'Dmaj7':[-1,-1,0,2,2,2],'Gmaj7':[3,2,0,0,0,2],'Amaj7':[-1,0,2,1,2,0],'Em7':[0,2,2,0,3,0],'Am7':[-1,0,2,0,1,0],
 'Dm7':[-1,-1,0,2,1,1],'Asus4':[-1,0,2,2,3,0],'Asus2':[-1,0,2,2,0,0],'Dsus4':[-1,-1,0,2,3,3],'Dsus2':[-1,-1,0,2,3,0],'Esus4':[0,2,2,2,0,0],
 'E5':[0,2,2,-1,-1,-1],'A5':[-1,0,2,2,-1,-1],'D5':[-1,-1,0,2,3,-1],'G5':[3,5,5,-1,-1,-1],'B5':[-1,2,4,4,-1,-1],
 'Bm':[-1,2,4,4,3,2],'F':[1,3,3,2,1,1],'Fmaj7':[-1,-1,3,2,1,0],'Cm':[-1,3,5,5,4,3],'Gm':[3,5,5,3,3,3],'Bm7':[-1,2,0,2,0,2],'F#m':[2,4,4,2,2,2],
 'D/F#':[2,-1,0,2,3,2],'G/B':[-1,2,0,0,3,3],'E/G#':[4,2,2,1,0,0],'A/G':[3,-1,2,2,2,0],'Em6':[0,2,2,0,2,0],'Am6':[-1,0,2,2,1,2]}
ESH={'':[0,2,2,1,0,0],'m':[0,2,2,0,0,0],'7':[0,2,0,1,0,0],'m7':[0,2,0,0,0,0],'maj7':[0,2,1,1,0,0],'sus4':[0,2,2,2,0,0],'5':[0,2,2,None,None,None],'m6':[0,2,2,0,2,0],'6':[0,2,2,1,2,0]}
ASH={'':[None,0,2,2,2,0],'m':[None,0,2,2,1,0],'7':[None,0,2,0,2,0],'m7':[None,0,2,0,1,0],'maj7':[None,0,2,1,2,0],'sus4':[None,0,2,2,3,0],'sus2':[None,0,2,2,0,0],'5':[None,0,2,2,None,None],'m6':[None,0,2,2,1,2],'6':[None,0,2,2,2,2]}
def shape(tpl,r): return tuple(-1 if o is None else r+o for o in tpl)
def solve(rp,q,bp,n=2):
    best=[]
    for base in range(0,10):
        opts=[]
        for s in range(6):
            o=[-1]+([0] if True else [])+list(range(max(base,1),base+4))
            opts.append(sorted(set(o)))
        for fr in itertools.product(*opts):
            if not valid(fr,rp,q,bp) or not span_ok(fr) or fingers(fr)>4: continue
            snd=sum(1 for f in fr if f>=0)
            if snd<4 and len(QUAL[q][0])>2: continue
            fz=[f for f in fr if f>0]
            if any(f==0 for f in fr) and fz and max(fz)>5: continue
            # no muted string between sounding strings
            first=next(i for i,f in enumerate(fr) if f>=0); last=max(i for i,f in enumerate(fr) if f>=0)
            if any(fr[i]<0 for i in range(first,last+1)): continue
            best.append(((max(fz) if fz else 0, 6-snd, fingers(fr), base),fr))
    best.sort(); out=[]
    for _,fr in best:
        if fr not in out: out.append(fr)
        if len(out)>=n: break
    return out
def variants(key,rp,q,bp):
    out=[]
    def add(fr):
        fr=tuple(fr)
        if fr in out: return
        if valid(fr,rp,q,bp) and span_ok(fr) and fingers(fr)<=4: out.append(fr)
    if key in CUR: add(CUR[key])
    if rp==bp:
        cand=[]
        if q in ESH: cand.append(shape(ESH[q],(rp-4)%12))
        if q in ASH: cand.append(shape(ASH[q],(rp-9)%12))
        def low(fr): 
            fz=[f for f in fr if f>0]; return min(fz) if fz else 0
        cand=[c for c in cand if max(c)<=13]
        cand.sort(key=low)
        for c in cand: add(c)
    if not out:
        for fr in solve(rp,q,bp,2): out.append(fr)
    return [pack(v) for v in out[:3]]
def notes(rp,q,bp):
    ivs=QUAL[q][0]; ns=[NAMES[(rp+i)%12] for i in ivs]
    if bp!=rp: ns=[NAMES[bp]]+[x for x in ns if x!=NAMES[bp]]
    return ' '.join(ns)
def entry(key,rp,q,bp):
    v=variants(key,rp,q,bp)
    return {'v':v,'n':notes(rp,q,bp)}
import os,json
CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'acordes_cache.json')
def build_dict(used):
    try: cache=json.load(open(CACHE,encoding='utf-8'))
    except Exception: cache={}
    dirty=False
    def get(k,rp,q,bp):
        nonlocal dirty
        if k not in cache: cache[k]=entry(k,rp,q,bp); dirty=True
        return cache[k]
    D={}
    for rp in range(12):
        for q in QUAL:
            k=NAMES[rp]+q; D[k]=get(k,rp,q,rp)
    for k in used:
        c=canon(k)
        for t in range(12):
            rp=(c[1]+t)%12; bp=(c[3]+t)%12
            kk=NAMES[rp]+c[2]+('/'+NAMES[bp] if bp!=rp else '')
            if kk not in D: D[kk]=get(kk,rp,c[2],bp)
    if dirty:
        json.dump(cache,open(CACHE,'w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
    return D
