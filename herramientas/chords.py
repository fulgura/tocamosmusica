"""Diccionario de acordes de guitarra.

- canon(tok): reconoce un acorde escrito ("Bbm", "G#°", "D7(9)", "F#/A#") y lo normaliza.
- build_dict(usados): arma las posiciones de cada acorde para la página.

Las posiciones salen, en este orden, de:
  1. datos/acordes.json: posiciones propias de la banda (por ejemplo copiadas de Cifra Club).
  2. CUR: posiciones abiertas conocidas.
  3. Formas móviles (cejilla con raíz en 6ª, 5ª o 4ª cuerda).
  4. Un buscador que prueba todas las posiciones razonables y se queda con las más cómodas.
"""
import hashlib
import itertools
import json
import os
import re

NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
PCN = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
OPEN = [4, 9, 2, 7, 11, 4]  # E A D G B E


def pc(n):
    v = PCN[n[0].upper()]
    for a in n[1:]:
        v += 1 if a == '#' else -1
    return v % 12


# Tipo -> intervalos (semitonos, grado), notas que se pueden omitir, notas extra permitidas.
# El grado sirve para escribir bien las notas (Eb y no D#).
def _q(ivs, opt=(), extra=(), label=''):
    return {'iv': ivs, 'opt': set(opt), 'extra': extra, 'label': label}


QUAL = {
    '':      _q([(0, 1), (4, 3), (7, 5)], label='Mayor'),
    'm':     _q([(0, 1), (3, 3), (7, 5)], label='Menor'),
    '7':     _q([(0, 1), (4, 3), (7, 5), (10, 7)], [7], label='7'),
    'm7':    _q([(0, 1), (3, 3), (7, 5), (10, 7)], [7], label='m7'),
    'maj7':  _q([(0, 1), (4, 3), (7, 5), (11, 7)], [7], label='maj7'),
    '6':     _q([(0, 1), (4, 3), (7, 5), (9, 6)], [7], label='6'),
    'm6':    _q([(0, 1), (3, 3), (7, 5), (9, 6)], [7], label='m6'),
    'sus4':  _q([(0, 1), (5, 4), (7, 5)], label='sus4'),
    'sus2':  _q([(0, 1), (2, 2), (7, 5)], label='sus2'),
    '7sus4': _q([(0, 1), (5, 4), (7, 5), (10, 7)], [7], label='7sus4'),
    'add9':  _q([(0, 1), (4, 3), (7, 5), (2, 9)], [7], label='add9'),
    'madd9': _q([(0, 1), (3, 3), (7, 5), (2, 9)], [7], label='m(add9)'),
    '9':     _q([(0, 1), (4, 3), (7, 5), (10, 7), (2, 9)], [7], label='9'),
    'm9':    _q([(0, 1), (3, 3), (7, 5), (10, 7), (2, 9)], [7], label='m9'),
    'maj9':  _q([(0, 1), (4, 3), (7, 5), (11, 7), (2, 9)], [7], label='maj9'),
    '5':     _q([(0, 1), (7, 5)], label='5 (power)'),
    # "°" en las cifras populares casi siempre se toca con la séptima disminuida.
    'dim':   _q([(0, 1), (3, 3), (6, 5)], extra=[(9, 7)], label='° (dim)'),
    'dim7':  _q([(0, 1), (3, 3), (6, 5), (9, 7)], label='°7'),
    'm7b5':  _q([(0, 1), (3, 3), (6, 5), (10, 7)], label='m7(b5)'),
    'aug':   _q([(0, 1), (4, 3), (8, 5)], label='aum (+)'),
    '7b5':   _q([(0, 1), (4, 3), (6, 5), (10, 7)], label='7(b5)'),
    '7#5':   _q([(0, 1), (4, 3), (8, 5), (10, 7)], label='7(#5)'),
    '7b9':   _q([(0, 1), (4, 3), (7, 5), (10, 7), (1, 9)], [7], label='7(b9)'),
    '7#9':   _q([(0, 1), (4, 3), (7, 5), (10, 7), (3, 9)], [7], label='7(#9)'),
    'mmaj7': _q([(0, 1), (3, 3), (7, 5), (11, 7)], [7], label='m(maj7)'),
    '69':    _q([(0, 1), (4, 3), (7, 5), (9, 6), (2, 9)], [7], label='6/9'),
    'm69':   _q([(0, 1), (3, 3), (7, 5), (9, 6), (2, 9)], [7], label='m6/9'),
    '9sus4': _q([(0, 1), (5, 4), (7, 5), (10, 7), (2, 9)], [7], label='9sus4'),
    'add11': _q([(0, 1), (4, 3), (7, 5), (5, 11)], [7], label='add11'),
    # 11 sin tercera (choca con la 11ª), como se toca en la práctica; la 9ª y la 5ª son opcionales.
    '11':    _q([(0, 1), (7, 5), (10, 7), (2, 9), (5, 11)], [7, 2], label='11'),
    'm11':   _q([(0, 1), (3, 3), (7, 5), (10, 7), (5, 11)], [7], extra=[(2, 9)], label='m11'),
    '13':    _q([(0, 1), (4, 3), (7, 5), (10, 7), (9, 13)], [7], extra=[(2, 9)], label='13'),
}

# Cómo se muestra cada tipo en el selector de la página (si no está, se usa la clave).
SUF = {'dim': '°', 'dim7': '°7', 'm7b5': 'm7(b5)', 'aug': '+', 'madd9': 'm(add9)', '7b5': '7(b5)', '7#5': '7(#5)',
       '7b9': '7(b9)', '7#9': '7(#9)', 'mmaj7': 'm(maj7)', '69': '6/9', 'm69': 'm6/9'}

# Cómo se escribe cada tipo en las cifras (sin paréntesis, que se sacan antes de buscar).
ALIAS = {
    '': '', 'M': '', 'maj': '', 'mayor': '',
    'm': 'm', 'min': 'm', '-': 'm',
    '7': '7', 'm7': 'm7', 'min7': 'm7', '-7': 'm7',
    'maj7': 'maj7', '7M': 'maj7', 'M7': 'maj7', 'Maj7': 'maj7', '7+': 'maj7', 'Δ': 'maj7', 'Δ7': 'maj7',
    '6': '6', 'm6': 'm6',
    '4': 'sus4', 'sus': 'sus4', 'sus4': 'sus4',
    '2': 'sus2', 'sus2': 'sus2',
    '74': '7sus4', '7sus4': '7sus4', '7sus': '7sus4', '4/7': '7sus4', '7/4': '7sus4',
    'add9': 'add9', 'add2': 'add9', '9add': 'add9', 'add9no3': 'sus2',
    'madd9': 'madd9', 'm9add': 'madd9', 'madd2': 'madd9', 'm2': 'madd9',
    '9': '9', '79': '9', '7/9': '9',
    'm9': 'm9', 'm79': 'm9', 'm7/9': 'm9',
    'maj9': 'maj9', '7M9': 'maj9', 'M9': 'maj9', 'maj79': 'maj9',
    '5': '5',
    'dim': 'dim', '°': 'dim', 'º': 'dim', 'o': 'dim',
    'dim7': 'dim7', '°7': 'dim7', 'º7': 'dim7', 'o7': 'dim7',
    'm7b5': 'm7b5', 'm7-5': 'm7b5', 'ø': 'm7b5', 'ø7': 'm7b5', 'm75-': 'm7b5', 'm7b5ø': 'm7b5',
    'aug': 'aug', '+': 'aug', '+5': 'aug', '5+': 'aug', '#5': 'aug', 'aum': 'aug',
    '7b5': '7b5', '7-5': '7b5', '7/b5': '7b5',
    '7#5': '7#5', '7+5': '7#5', '7/#5': '7#5', '7aug': '7#5', 'aug7': '7#5',
    '7b9': '7b9', '7-9': '7b9', '7/b9': '7b9',
    '7#9': '7#9', '7+9': '7#9', '7/#9': '7#9',
    'mmaj7': 'mmaj7', 'm7M': 'mmaj7', 'mM7': 'mmaj7', 'm7+': 'mmaj7', 'mMaj7': 'mmaj7', 'minmaj7': 'mmaj7',
    '69': '69', '6/9': '69', '6add9': '69', 'm69': 'm69', 'm6/9': 'm69',
    '9sus4': '9sus4', '9sus': '9sus4', '9/4': '9sus4',
    'add11': 'add11', 'add4': 'add11',
    '11': '11', '711': '11', '7/11': '11', '9/11': '11',
    'm11': 'm11', 'm711': 'm11', 'm7/11': 'm11',
    '13': '13', '713': '13', '7/13': '13', '9/13': '13',
    # Con paréntesis y sin séptima, como en Cifra Club: C(9) es Cadd9 y no C9.
    '(9)': 'add9', 'm(9)': 'madd9', '(11)': 'add11',
}

# Un token de acorde. La primera alternativa permite paréntesis dentro del acorde: D7(9), Am7(b5).
TOKRE = re.compile(r'[A-G][#b]?[^\s\[\]\(\)\|]*?(?:\([^\s()]*\)[^\s\[\]\(\)\|]*?)?(?:/[A-G][#b]?)?(?=$|[\s\[\]\(\)\|\-])'
                   r'|[^\s\[\]\(\)\|\-]+')
_CH = re.compile(r'^([A-G][#b]?)(.*?)(?:/([A-Ga-g][#b]?))?$')


def canon(tok):
    """Token -> (clave, raíz, tipo, bajo, raíz escrita, bajo escrito) o None.

    La clave usa sostenidos (es la clave interna del diccionario); la raíz y el bajo
    escritos conservan cómo está en la cifra (Bb, Ab) para mostrarlo igual.
    """
    t = tok.rstrip('.')
    if t.startswith('(') and t.endswith(')') and t.count('(') == 1:
        t = t[1:-1]
    m = _CH.match(t)
    if not m:
        return None
    r, q, b = m.groups()
    if q not in ALIAS:  # primero tal cual (C(9) = Cadd9), después sin paréntesis (D7(9) = D9)
        q = q.replace('(', '').replace(')', '')
    if q not in ALIAS:
        return None
    q = ALIAS[q]
    rp = pc(r)
    bp = pc(b) if b else rp
    key = NAMES[rp] + q + ('/' + NAMES[bp] if b and bp != rp else '')
    return key, rp, q, bp, r, (b if b and bp != rp else None)


def tones(rp, q):
    d = QUAL[q]
    allowed = {(rp + s) % 12 for s, _ in d['iv']} | {(rp + s) % 12 for s, _ in d['extra']}
    req = {(rp + s) % 12 for s, _ in d['iv'] if s not in d['opt']}
    return allowed, req


def valid(fr, rp, q, bp):
    allowed, req = tones(rp, q)
    allowed = allowed | {bp}
    snd = [(i, (OPEN[i] + f) % 12) for i, f in enumerate(fr) if f >= 0]
    if len(snd) < 3:
        return False
    pcs = {p for _, p in snd}
    if not pcs <= allowed or not req <= pcs:
        return False
    if bp != rp and bp not in pcs:
        return False
    return snd[0][1] == bp


def barre(fr):
    fz = [(i, f) for i, f in enumerate(fr) if f > 0]
    if not fz:
        return None
    m = min(f for _, f in fz)
    idx = [i for i, f in fz if f == m]
    if len(idx) < 2 or (len(idx) == 2 and len(fz) <= 4):
        return None
    lo, hi = min(idx), max(idx)
    for i in range(lo, hi + 1):
        if fr[i] < m:
            return None  # cuerda al aire o apagada dentro de la cejilla
    return [m, lo, hi]


def fingers(fr):
    b = barre(fr)
    fz = [(i, f) for i, f in enumerate(fr) if f > 0]
    if b:
        return 1 + len({i for i, f in fz if f > b[0] or not (b[1] <= i <= b[2])})
    return len(fz)


def assign_fingers(fr, b):
    """Dedo para cada cuerda (0 = ninguno): de los trastes más bajos a los más altos,
    y en el mismo traste de la cuerda más grave a la más aguda."""
    d = [0] * 6
    nxt = 1
    if b:
        for i in range(b[1], b[2] + 1):
            if fr[i] == b[0]:
                d[i] = 1
        nxt = 2
    rest = sorted(((f, i) for i, f in enumerate(fr) if f > 0 and not d[i]))
    for f, i in rest:
        d[i] = min(nxt, 4)
        nxt += 1
    return d


def span(fr):
    fz = [f for f in fr if f > 0]
    return max(fz) - min(fz) if fz else 0


def playable(fr):
    return span(fr) <= 3 and fingers(fr) <= 4


def pack(fr, dedos=None):
    fz = [f for f in fr if f > 0]
    base = 1 if (not fz or max(fz) <= 4) else min(fz)
    b = barre(fr)
    return {'f': list(fr), 'b': b, 'base': base, 'd': list(dedos) if dedos else assign_fingers(fr, b)}


def parse_frets(s):
    """'4 X 3 4 3 X', '4x343x' o '8 10 10 9 8 8' -> tupla de 6 trastes (-1 = no se toca)."""
    s = s.strip()
    parts = s.split() if ' ' in s else list(s)
    if len(parts) != 6:
        raise ValueError('La posición %r no tiene 6 cuerdas' % s)
    return tuple(-1 if p.lower() == 'x' else int(p) for p in parts)


# Posiciones abiertas conocidas (6ª cuerda a 1ª).
CUR = {k: parse_frets(v) for k, v in {
    'C': 'x32010', 'D': 'xx0232', 'G': '320003', 'E': '022100', 'A': 'x02220', 'F': '133211', 'B': 'x24442',
    'Am': 'x02210', 'Em': '022000', 'Dm': 'xx0231', 'Bm': 'x24432', 'F#m': '244222', 'Cm': 'x35543', 'Gm': '355333',
    'C7': 'x32310', 'D7': 'xx0212', 'E7': '020100', 'G7': '320001', 'A7': 'x02020', 'B7': 'x21202',
    'Cmaj7': 'x32000', 'Dmaj7': 'xx0222', 'Gmaj7': '320002', 'Amaj7': 'x02120', 'Emaj7': '021100', 'Fmaj7': 'xx3210',
    'Em7': '022030', 'Am7': 'x02010', 'Dm7': 'xx0211', 'Bm7': 'x20202',
    'Asus4': 'x02230', 'Asus2': 'x02200', 'Dsus4': 'xx0233', 'Dsus2': 'xx0230', 'Esus4': '022200', 'Csus2': 'x30033',
    'Gsus4': '330013', 'Csus4': 'x33011',
    'A7sus4': 'x02030', 'D7sus4': 'xx0213', 'E7sus4': '020200', 'G7sus4': '330011',
    'Cadd9': 'x32030', 'Gadd9': '300203', 'Dadd9': 'x54230', 'Eadd9': '022102', 'Aadd9': 'x02420', 'Fadd9': 'xx3213',
    'Emadd9': '024000', 'Amadd9': 'x02410',
    'C9': 'x32333', 'E9': '020102', 'G9': '3x0201', 'A9': 'x02423', 'B9': 'x21222',
    'Em9': '020002', 'Am9': 'x05500', 'Cmaj9': 'x30000',
    'E5': '022xxx', 'A5': 'x022xx', 'D5': 'xx023x', 'G5': '355xxx', 'B5': 'x244xx', 'C5': 'x355xx', 'F5': '133xxx',
    'Em6': '022020', 'Am6': 'x02212', 'Dm6': 'xx0201', 'C6': 'x32210', 'D6': 'xx0202', 'E6': '022120', 'G6': '320000', 'A6': 'x02222',
    'Ddim7': 'xx0101', 'Edim7': '012020', 'Bdim': 'x2343x', 'Edim': '0120xx',
    'Bm7b5': 'x2323x', 'Em7b5': '012033', 'Am7b5': 'x0101x', 'F#m7b5': '2x221x',
    'Caug': 'x32110', 'Eaug': '032110', 'Gaug': '321003', 'Daug': 'xx0332', 'Aaug': 'x03221',
    'D/F#': '2x0232', 'G/B': 'x20033', 'E/G#': '422100', 'A/G': '3x2220', 'A/C#': 'x42220', 'C/G': '332010',
    'C/E': '032010', 'C/B': 'x22010', 'Am/G': '3x2210', 'Am/F#': '2x2210', 'Am/E': '002210', 'D/A': 'x00232',
    'D/C': 'x30232', 'G/F#': '2x0003', 'G/D': 'xx0003', 'F/C': 'x33211', 'F/A': 'x03211', 'E/B': 'x22100',
    'Em/D': 'xx0000', 'Em/B': 'x22000', 'A/E': '002220', 'Dm/C': 'x30231', 'Dm/F': '1x0231', 'Bm/A': 'x04432',
    'C/D': 'xx0010', 'G/A': 'x00003',
    'E7#9': '076780', 'B7#9': 'x2123x', 'C69': 'x32233', 'G69': '3x2200', 'A69': 'x02422',
    'Ammaj7': 'x02110', 'Emmaj7': '021000', 'Dmmaj7': 'xx0221', 'G13': '3x345x', 'E13': '020122',
    'E7#5': '0x0110', 'Cadd11': 'x32011', 'A7b9': 'x02323',
}.items()}

# Formas móviles: desplazamiento respecto del traste de la raíz (None = no se toca).
X = None
ESH = {'': [0, 2, 2, 1, 0, 0], 'm': [0, 2, 2, 0, 0, 0], '7': [0, 2, 0, 1, 0, 0], 'm7': [0, 2, 0, 0, 0, 0],
       'maj7': [0, X, 1, 1, 0, X], 'sus4': [0, 2, 2, 2, 0, 0], '5': [0, 2, 2, X, X, X], 'm6': [0, X, -1, 0, 0, X],
       '6': [0, X, -1, 1, 0, X], '7sus4': [0, 2, 0, 2, 0, 0], 'dim': [0, 1, 2, 0, X, X], 'dim7': [0, X, -1, 0, -1, X],
       'm7b5': [0, X, 0, 0, -1, X], 'aug': [0, X, 2, 1, 1, X], '9': [0, X, 0, 1, 0, 2], 'm9': [0, X, 0, 0, 0, 2], '7b5': [0, X, 0, 1, -1, X], '7#5': [0, X, 0, 1, 1, X], '13': [0, X, 0, 1, 2, X],
       'mmaj7': [0, X, 1, 0, 0, X]}
ASH = {'': [X, 0, 2, 2, 2, 0], 'm': [X, 0, 2, 2, 1, 0], '7': [X, 0, 2, 0, 2, 0], 'm7': [X, 0, 2, 0, 1, 0],
       'maj7': [X, 0, 2, 1, 2, 0], 'sus4': [X, 0, 2, 2, 3, 0], 'sus2': [X, 0, 2, 2, 0, 0], '5': [X, 0, 2, 2, X, X],
       'm6': [X, 0, 2, 2, 1, 2], '6': [X, 0, 2, 2, 2, 2], '7sus4': [X, 0, 2, 0, 3, 0], 'dim': [X, 0, 1, 2, 1, X],
       'dim7': [X, 0, 1, -1, 1, X], 'm7b5': [X, 0, 1, 0, 1, X], 'aug': [X, 0, 3, 2, 2, 1], '9': [X, 0, -1, 0, 0, 0],
       'm9': [X, 0, -2, 0, 0, 0], 'maj9': [X, 0, -1, 1, 0, X], 'add9': [X, 0, -1, -3, 0, X], 'madd9': [X, 0, -2, -3, 0, X],
       '7b9': [X, 0, -1, 0, -1, X], '7#9': [X, 0, -1, 0, 1, X], 'mmaj7': [X, 0, 2, 1, 1, 0], '69': [X, 0, -1, -1, 0, 0],
       'm69': [X, 0, -2, -1, 0, 0], '9sus4': [X, 0, 0, 0, 0, 0], '11': [X, 0, 0, 0, 0, X]}
DSH = {'': [X, X, 0, 2, 3, 2], 'm': [X, X, 0, 2, 3, 1], '7': [X, X, 0, 2, 1, 2], 'm7': [X, X, 0, 2, 1, 1],
       'maj7': [X, X, 0, 2, 2, 2], 'sus4': [X, X, 0, 2, 3, 3], 'sus2': [X, X, 0, 2, 3, 0], '6': [X, X, 0, 2, 0, 2],
       'm6': [X, X, 0, 2, 0, 1], '7sus4': [X, X, 0, 2, 1, 3], 'dim': [X, X, 0, 1, 3, 1], 'dim7': [X, X, 0, 1, 0, 1],
       'm7b5': [X, X, 0, 1, 1, 1], 'aug': [X, X, 0, 3, 3, 2], '5': [X, X, 0, 2, 3, X]}
SHAPES = [(ESH, 4), (ASH, 9), (DSH, 2)]  # forma, nota de la cuerda donde está la raíz


def shape(tpl, r):
    fr = tuple(-1 if o is None else r + o for o in tpl)
    return fr if all(f >= -1 for f in fr) and not any(o is not None and r + o < 0 for o in tpl) else None


def cost(fr):
    """Cuanto más bajo, más cómoda. Se usa para ordenar las posiciones generadas."""
    fz = [f for f in fr if f > 0]
    snd = sum(1 for f in fr if f >= 0)
    first = next(i for i, f in enumerate(fr) if f >= 0)
    last = max(i for i, f in enumerate(fr) if f >= 0)
    inner_mute = sum(1 for i in range(first, last + 1) if fr[i] < 0)
    open_mix = bool(any(f == 0 for f in fr) and fz and max(fz) >= 4)
    pressed = [i for i, f in enumerate(fr) if f > 0]
    inner_open = sum(1 for i, f in enumerate(fr) if f == 0 and pressed and min(pressed) < i < max(pressed))
    return (2 * fingers(fr) + 1.5 * span(fr) + (1.5 if span(fr) >= 3 else 0) + 1.0 * (min(fz) if fz else 0)
            + (3 if fz and min(fz) >= 10 else 0)
            + 4 * open_mix + 1.2 * (6 - snd) + 2.5 * inner_mute + 2 * inner_open + (0.5 if barre(fr) else 0))


def natural(fr):
    """Filtro para lo que propone el buscador (las posiciones conocidas y las formas no pasan por acá)."""
    fz = [f for f in fr if f > 0]
    if not fz:
        return True
    # Cuerdas al aire solo cerca de la cejuela: 0 2 5 0 x x no.
    if any(f == 0 for f in fr) and max(fz) > 3:
        return False
    # Abrir cuatro trastes con cejilla (5 3 2 2 5 x, 7 6 4 4 4 5) no se toca.
    if span(fr) == 3 and barre(fr):
        return False
    # Dos o más cuerdas al aire metidas entre cuerdas pisadas (x x 2 0 0 3) no.
    pressed = [i for i, f in enumerate(fr) if f > 0]
    if sum(1 for i, f in enumerate(fr) if f == 0 and min(pressed) < i < max(pressed)) >= 2:
        return False
    # Bajo en la 6ª con el meñique, en el traste más alto, y cuatro dedos (7 5 5 7 x x): no.
    if fr[0] > 0 and fr[0] == max(fz) and fingers(fr) >= 4 and span(fr) >= 2:
        return False
    return True


def solve(rp, q, bp, limit=8):
    allowed, _ = tones(rp, q)
    allowed |= {bp}
    found = []
    for base in range(1, 12):
        opts = []
        for s in range(6):
            o = [-1] + [f for f in [0] + list(range(base, base + 4)) if (OPEN[s] + f) % 12 in allowed]
            opts.append(sorted(set(o)))
        for fr in itertools.product(*opts):
            if not valid(fr, rp, q, bp) or not playable(fr):
                continue
            snd = sum(1 for f in fr if f >= 0)
            if snd < 4 and len(QUAL[q]['iv']) > 2:
                continue
            if not natural(fr):
                continue
            first = next(i for i, f in enumerate(fr) if f >= 0)
            last = max(i for i, f in enumerate(fr) if f >= 0)
            if any(fr[i] < 0 for i in range(first, last + 1)):
                continue  # nada de cuerdas apagadas en el medio
            found.append(fr)
    found = sorted(set(found), key=cost)
    return found[:limit * 4]


def similar(a, b):
    return sum(1 for x, y in zip(a, b) if x != y) <= 2


MAXV = 4


def variants(key, rp, q, bp, own=()):
    out = []  # (frets, dedos)

    def fixed(fr, dedos=None):
        if fr not in [o[0] for o in out]:
            out.append((fr, dedos))

    for fr, dedos in own:  # posiciones propias: van siempre, aunque el programa no las entienda
        fixed(fr, dedos)
    if key in CUR and valid(CUR[key], rp, q, bp):
        fixed(CUR[key])
    cand = []
    if rp == bp:
        for tbl, open_note in SHAPES:
            if q in tbl:
                for r in ((rp - open_note) % 12, (rp - open_note) % 12 + 12):
                    fr = shape(tbl[q], r)
                    if fr and max(fr) <= 14 and valid(fr, rp, q, bp) and playable(fr):
                        cand.append(fr)
    forms = set(cand)  # las formas de cejilla de siempre tienen prioridad sobre lo que encuentre el buscador
    cand += solve(rp, q, bp)
    cand = sorted(set(cand), key=lambda fr: (cost(fr) - (2.5 if fr in forms else 0), fr))
    for fr in cand:
        if len(out) >= MAXV:
            break
        if any(similar(fr, o[0]) for o in out):
            continue
        out.append((fr, None))
    return [pack(fr, d) for fr, d in out[:max(MAXV, len(own))]]


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, 'herramientas', 'acordes_cache.json')
PROPIOS = os.path.join(ROOT, 'datos', 'acordes.json')
VERSION = '3'


def cargar_propios():
    """datos/acordes.json -> {clave: [(frets, dedos), ...]}"""
    try:
        with open(PROPIOS, encoding='utf-8') as f:
            raw = json.load(f)
    except FileNotFoundError:
        return {}, ''
    out = {}
    for nombre, val in raw.items():
        if nombre.startswith('_'):
            continue
        c = canon(nombre)
        if not c:
            raise ValueError('datos/acordes.json: no entiendo el acorde %r' % nombre)
        lst = []
        for p in val.get('posiciones', []):
            if isinstance(p, dict):
                fr = parse_frets(p['trastes'])
                dedos = [0 if d in ('-', 'x', 'X') else int(d) for d in p['dedos'].replace(' ', '')] if p.get('dedos') else None
            else:
                fr, dedos = parse_frets(p), None
            lst.append((fr, dedos))
        out[c[0]] = lst
    firma = hashlib.sha1(json.dumps(raw, sort_keys=True).encode()).hexdigest()[:10]
    return out, firma


def build_dict(used):
    propios, firma = cargar_propios()
    ver = VERSION + ':' + firma
    try:
        cache = json.load(open(CACHE, encoding='utf-8'))
    except Exception:
        cache = {}
    if cache.get('_v') != ver:
        cache = {'_v': ver}
    dirty = False

    def get(k, rp, q, bp):
        nonlocal dirty
        if k not in cache:
            cache[k] = {'v': variants(k, rp, q, bp, propios.get(k, ()))}
            dirty = True
        return cache[k]

    D = {}
    for rp in range(12):
        for q in QUAL:
            k = NAMES[rp] + q
            D[k] = get(k, rp, q, rp)
    for k in list(used) + list(propios):
        c = canon(k)
        for t in range(12):
            rp = (c[1] + t) % 12
            bp = (c[3] + t) % 12
            kk = NAMES[rp] + c[2] + ('/' + NAMES[bp] if bp != rp else '')
            if kk not in D:
                D[kk] = get(kk, rp, c[2], bp)
    if dirty:
        with open(CACHE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    return D


def para_pagina():
    """Lo que la página necesita para escribir notas y transponer: intervalos, alias y etiquetas."""
    return {
        'Q': {q: [[s, g] for s, g in d['iv']] for q, d in QUAL.items()},
        'X': {q: [[s, g] for s, g in d['extra']] for q, d in QUAL.items() if d['extra']},
        'A': ALIAS,
        'L': [[q, d['label']] for q, d in QUAL.items()],
        'S': SUF,
    }
