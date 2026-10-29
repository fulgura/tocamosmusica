import json,re,html,urllib.parse
import os,sys
B=os.path.dirname(os.path.abspath(__file__))+'/'
ROOT=os.path.dirname(B.rstrip('/'))+'/'
sys.path.insert(0,B)
import chords as CD
M=[('d','Diego Correa','Guitarra · Voz','Diego'),('s','Sebastian Vazquez Montoto','Batería','Seba'),('g','Sergio Alvarez','Bajo · Voz','Sergio'),('a','Agustín Alvarez','Teclado','Agustín'),('j','Juan Alvarez','Guitarra · Voz','Juan'),('c','Cyntia','Voz','Cyn')]
LAB={'d':'Guitarra','s':'Batería','g':'Bajo','a':'Teclado','j':'Guitarra','c':'Voz'}
DATA=json.load(open(ROOT+'datos/canciones.json',encoding='utf-8'))
C={s['id']:{'text':s['chart']} for s in DATA if s.get('chart')}
songs=[dict(id=s['id'],title=s['title'],artist=s.get('artist') or '',r=s.get('ronda',0),chart=(s['id'] if s.get('chart') else None),pl=s.get('players',{}),note=s.get('nota') or '',tent=set(s.get('tentativos',[])),fuente=s.get('fuente')) for s in DATA]
# tentative from '?' marks: P(tent=True) gave plain dict; mark via tent set
LABELS={'intro','interlude','solo','outro','intervalo','puente','estribillo','final','coro','verso'}
TOKRE=CD.TOKRE
def classify(l):
    toks=TOKRE.findall(l)
    if not toks: return None
    ch=[];bad=0
    for t in toks:
        if CD.canon(t): ch.append(t); continue
        tl=t.lower().rstrip(':')
        if tl in LABELS or re.match(r'^x\d+$',t) or re.match(r'^[\d.,:]+$',t): continue
        if len(t)<=5 and not t[0].islower() and not re.match(r'^[A-Za-zÁ-ú]{4,}$',t): bad+=1; continue
        return None
    if not ch or bad>1: return None
    return True
USED=[]; FIRST={}
def render_chart(txt,seen=None):
    out=[]
    for l in txt.split('\n'):
        if classify(l):
            parts=[];pos=0
            def addt(x):
                if not x: return
                if parts and parts[-1][0]=='t': parts[-1]=('t',parts[-1][1]+x)
                else: parts.append(('t',x))
            for m in TOKRE.finditer(l):
                t=m.group(0); c=CD.canon(t)
                addt(l[pos:m.start()])
                if c:
                    core=t.rstrip('.')
                    parts.append(('c',c[0],core))
                    addt(t[len(core):])
                    if c[0] not in USED: USED.append(c[0]); FIRST[c[0]]=re.sub(r'/([a-g])',lambda m:'/'+m.group(1).upper(),core)
                    if seen is not None and c[0] not in [x[0] for x in seen]: seen.append((c[0],core))
                else: addt(t)
                pos=m.end()
            addt(l[pos:])
            res=''.join('<span class="tx">%s</span>'%html.escape(p[1]) if p[0]=='t' else '<span class="cd" tabindex="0" role="button" data-c="%s" data-n="%s">%s</span>'%(html.escape(p[1]),html.escape(p[2]),html.escape(p[2])) for p in parts)
            out.append('<span class="ch">%s</span>'%res)
        elif re.match(r'^\s*\[[^\]]+\]\s*$',l): out.append('<span class="sec">%s</span>'%html.escape(l))
        else: out.append(html.escape(l))
    return '\n'.join(out)
def gq(s):
    return 'https://www.google.com/search?q='+urllib.parse.quote('acordes '+s['title']+' '+s['artist'])
RN={1:'Ronda 1',2:'Ronda 2',3:'Ronda 3',0:'Fuera de las rondas'}
# matrix
rows=[]; cards=[]
for r in (1,2,3,0):
    ss=[s for s in songs if s['r']==r]
    if r==0:
        pass
    rows.append('<tbody data-r="%d"><tr class="rh"><th colspan="9" scope="colgroup"><span class="rt r%d">%s</span><span class="rc">%d temas</span></th></tr>'%(r,r,RN[r],len(ss)))
    for i,s in enumerate(ss,1):
        who=[k for k in s['pl']]
        # '?' for tentative
        cells=[]
        for k,_,_,_ in M:
            if k in s['pl']:
                tent = k in s['tent']
                detail=s['pl'][k] if s['pl'][k] not in ('?',) else ''
                lab=LAB[k]
                if k=='c' and not detail and False: pass
                txt=lab+(' <small>%s</small>'%html.escape(detail) if detail else '')
                cells.append('<td class="p %s%s" data-m="%s">%s</td>'%(k,' t' if tent else '',k,('<span class="pill%s">%s%s</span>'%(' tent' if tent else '',txt,'<i> ?</i>' if tent else ''))))
            else:
                cells.append('<td class="n" data-m="%s"><span class="dot"></span></td>'%k)
        nm='<a href="#s-%s">%s</a>'%(s['id'],html.escape(s['title']))
        art=('<span class="art">%s</span>'%html.escape(s['artist'])) if s['artist'] else ''
        have = s['chart'] is not None
        link='<a class="go" href="#s-%s">Acordes</a>'%s['id'] if have else '<a class="go miss" href="%s" target="_blank" rel="noopener">Buscar online</a>'%gq(s)
        n_s = '<td class="num">%d</td>'%i if r else '<td class="num">·</td>'
        rows.append('<tr class="sr" data-players="%s">%s<th scope="row" class="tt">%s%s</th>%s<td class="lk">%s</td></tr>'%(' '.join(who),n_s,nm,art,''.join(cells),link))
    rows.append('</tbody>')
    for s in ss:
        who=[k for k in s['pl']]
        chips=''.join('<span class="chip %s%s">%s</span>'%(k,' tent' if k in s['tent'] else '',html.escape(dict((m[0],m[3]) for m in M)[k])) for k in who)
        if s['chart']:
            seen=[]; rc=render_chart(C[s['chart']]['text'],seen)
            strip='<div class="used" aria-label="Acordes de este tema">%s</div>'%''.join('<span class="cd cc" tabindex="0" role="button" data-c="%s" data-n="%s">%s</span>'%(html.escape(k),html.escape(n),html.escape(n)) for k,n in seen) if seen else ''
            tono='<div class="tono"><span class="lbl">Tono de este tema</span><button type="button" class="tb" data-d="-1" aria-label="Bajar un semitono">−½</button><output class="tv">Original</output><button type="button" class="tb" data-d="1" aria-label="Subir un semitono">+½</button><button type="button" class="tb tr">Original</button></div>' if seen else ''
            body=strip+tono+'<pre class="chart">%s</pre>'%rc
        else:
            body='<p class="nochart">Los acordes de este tema todavía no están en el archivo Tocamos Canciones. Mientras tanto: <a href="%s" target="_blank" rel="noopener">buscar los acordes online</a>.</p>'%gq(s)
        ext='' if not s['chart'] else '<a class="ext" href="%s" target="_blank" rel="noopener">Ver versión online</a>'%gq(s)
        if s.get('fuente'):
            from urllib.parse import urlparse
            ext='<a class="ext" href="%s" target="_blank" rel="noopener">Fuente: %s</a>'%(html.escape(s['fuente']),html.escape(urlparse(s['fuente']).netloc.replace('www.','')))
        cards.append('<details class="song" id="s-%s" data-players="%s"><summary><span class="rt r%d">%s</span><span class="st">%s</span>%s<span class="chips">%s</span></summary><div class="sb">%s%s%s</div></details>'%(s['id'],' '.join(who),s['r'],'R%d'%s['r'] if s['r'] else 'Extra',html.escape(s['title']),('<span class="art">%s</span>'%html.escape(s['artist'])) if s['artist'] else '',chips,('<p class="note">%s</p>'%html.escape(s['note'])) if s['note'] else '',ext,body))
heads=''.join('<th scope="col" class="mh" data-m="%s"><span>%s</span><small>%s</small></th>'%(k,short,LAB[k] if k!='d' else 'Gtr · Voz') for k,_,_,short in M)
tbl='<table class="mx"><thead><tr><th class="num">#</th><th scope="col" class="tt">Tema</th>%s<th scope="col">Acordes</th></tr></thead>%s</table>'%(heads,''.join(rows))
def cnt(k): return sum(1 for s in songs if s['r'] and k in s['pl'] and k not in s['tent'])
members=''.join('<li class="mem %s"><b>%s</b><span>%s</span><em>%d temas</em></li>'%(k,html.escape(n),html.escape(i),cnt(k)) for k,n,i,_ in M)
filt='<button class="f on" data-f="all" type="button">Todos</button>'+''.join('<button class="f" data-f="%s" type="button">%s</button>'%(k,short) for k,_,_,short in M)
T=open(B+'plantilla.html',encoding='utf-8').read()
DICT=json.dumps(CD.build_dict(USED),sort_keys=True,separators=(',',':'),ensure_ascii=False)
T=T.replace('__DICT__',DICT).replace('__USED__',json.dumps([[k,FIRST[k]] for k in sorted(USED,key=lambda k:(CD.canon(k)[1],list(CD.QUAL).index(CD.canon(k)[2]),k))],ensure_ascii=False)).replace('__META__',json.dumps(CD.para_pagina(),ensure_ascii=False,separators=(',',':'))).replace('__MEMBERS__',members).replace('__FILTER__',filt).replace('__MATRIX__',tbl).replace('__SONGS__','\n'.join(cards)).replace('__N__',str(len([s for s in songs if s['r']])))
open(ROOT+'index.html','w',encoding='utf-8').write(T)
print(len(T))
