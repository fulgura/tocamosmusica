"""Cifras guardadas como archivos de texto en datos/cifras/<id>.txt.

Cada archivo es la cifra tal cual se pega desde La Cuerda, Cifra Club, etc. Al construir la página
se limpia el encabezado y el pie de La Cuerda (los recuadros con ====) y los espacios de más.

Si hay un archivo sin entrada en datos/canciones.json, la canción aparece igual, fuera de las
rondas, con el título y el artista del encabezado de La Cuerda (o el nombre del archivo).
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(RAIZ, 'datos', 'cifras')

_RECUADRO = re.compile(r'^\s*[=+|]')  # líneas del recuadro de La Cuerda
_PIE = re.compile(r'^=+ *lacuerda\.net *=+\s*$', re.I)


def ruta(id_):
    return os.path.join(DIR, id_ + '.txt')


def normalizar(texto):
    t = texto.replace('\r\n', '\n').replace('\r', '\n').replace('\xa0', ' ').replace('﻿', '').expandtabs(4)
    ls = [l.rstrip() for l in t.split('\n')]
    while ls and not ls[0]:
        ls.pop(0)
    while ls and not ls[-1]:
        ls.pop()
    return ls


def limpiar(texto):
    """Saca el encabezado y el pie de La Cuerda; deja el resto tal cual."""
    ls = normalizar(texto)
    # Encabezado: el recuadro del principio (líneas que empiezan con =, + o |).
    if ls and ls[0].lstrip().startswith('='):
        i = 0
        while i < len(ls) and (not ls[i].strip() or _RECUADRO.match(ls[i])):
            i += 1
        ls = ls[i:]
    # Pie: desde la primera línea "==== lacuerda.net ====" hasta el final.
    for i, l in enumerate(ls):
        if _PIE.match(l.strip()):
            ls = ls[:i]
            break
    while ls and not ls[-1]:
        ls.pop()
    return '\n'.join(ls)


def encabezado(texto):
    """Título y artista del recuadro de La Cuerda, si está."""
    datos = {}
    for l in normalizar(texto)[:15]:
        m = re.match(r'^\|\s*(ARTISTA|CANCION|CANCIÓN):\s*(.*?)\s*\|?\s*$', l, re.I)
        if m and m.group(2):
            datos['artist' if m.group(1).upper() == 'ARTISTA' else 'title'] = _titulo(m.group(2))
    return datos


def _titulo(s):
    chicas = {'a', 'de', 'del', 'el', 'en', 'la', 'las', 'lo', 'los', 'y', 'o', 'por', 'con', 'que', 'mi', 'tu', 'se'}
    ps = s.strip().lower().split()
    return ' '.join(p if (i and p in chicas) else p[:1].upper() + p[1:] for i, p in enumerate(ps))


def leer(id_):
    """Cifra limpia de datos/cifras/<id>.txt, o None si no hay archivo (o está vacío)."""
    try:
        with open(ruta(id_), encoding='utf-8') as f:
            t = limpiar(f.read())
    except FileNotFoundError:
        return None
    return t or None


def guardar(id_, texto):
    os.makedirs(DIR, exist_ok=True)
    with open(ruta(id_), 'w', encoding='utf-8') as f:
        f.write(texto.rstrip('\n') + '\n')


def sueltas(ids_conocidos):
    """Canciones que solo tienen archivo de cifra: [{'id', 'title', 'artist'}]."""
    if not os.path.isdir(DIR):
        return []
    out = []
    for nombre in sorted(os.listdir(DIR)):
        if not nombre.endswith('.txt'):
            continue
        id_ = nombre[:-4]
        if id_ in ids_conocidos:
            continue
        with open(ruta(id_), encoding='utf-8') as f:
            enc = encabezado(f.read())
        out.append({'id': id_, 'title': enc.get('title') or _titulo(id_.replace('-', ' ')),
                    'artist': enc.get('artist', '')})
    return out
