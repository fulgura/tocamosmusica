# Tocamos Música — Cancionero

Repertorio de la banda: quién toca cada tema en las 3 rondas y los acordes para ensayar.

Página: https://fulgura.github.io/tocamosmusica/

## Cómo está armado

- `datos/canciones.json`: todas las canciones (ronda, quiénes tocan, cifra).
- `herramientas/construir.py`: genera `index.html` a partir de esos datos.
- `herramientas/agregar_cancion.py`: el agente que agrega una canción desde una página de cifras.

`index.html` es un archivo generado. Los cambios van en `datos/` y se regenera.

## Agregar una canción con el agente

Necesita Python 3.9 o más nuevo (no instala nada más) y una clave de la API de Anthropic:

```
export ANTHROPIC_API_KEY="tu-clave"
python3 herramientas/agregar_cancion.py "https://acordes.lacuerda.net/patricio_rey/masacre_en_el_puticlub" --ronda 2 --tocan d,s,g
```

Integrantes para `--tocan`: `d` Diego, `s` Seba, `g` Sergio, `a` Agustín, `j` Juan, `c` Cyn.
Si ponés `--ronda` sin `--tocan`, el tema queda con el tridente marcado como "a definir".

El agente usa Haiku (`claude-haiku-5-5`, se puede cambiar con `--modelo` o la variable `MODELO_AGENTE`).
Haiku no reescribe la cifra: solo indica en qué bloque y entre qué líneas está, y cuáles sobran. El programa
copia esas líneas tal cual, así que no puede cambiar un acorde ni la alineación con la letra.

Otras opciones:

| Opción | Qué hace |
| --- | --- |
| `--versiones` | Lista las otras versiones enlazadas en la página (La Cuerda suele tener varias) y termina |
| `--version N` | Usa la versión N de esa lista |
| `--probar` | Muestra el resultado sin guardar nada |
| `--reemplazar` | Si el tema ya existe, cambia su cifra y conserva ronda y quiénes tocan |
| `--titulo`, `--artista`, `--nota` | Corrige o agrega datos a mano |
| `--publicar` | Hace commit y push al terminar |

Si el sitio no deja descargar la página (por ejemplo, Cifra Club responde con un error):

1. Abrila en el navegador y guardala con Cmd+S como "Página web, solo HTML", y usá `--html archivo.html`; o
2. Copiá la cifra y usá `pbpaste | python3 herramientas/agregar_cancion.py --pegar --titulo "..." --artista "..."`.

Después de agregar, revisá la canción en `index.html`, y si está bien: `git add -A && git commit -m "Agrega ..." && git push`.

## Pruebas

```
cd herramientas && python3 test_agente.py
```

Las pruebas no usan la API ni ningún sitio: trabajan con una página inventada.

## Aviso

Las letras y cifras de Cifra Club y La Cuerda tienen derechos de autor y los sitios pueden tener
condiciones de uso que limitan copiarlas de forma automática. Esta herramienta es para armar el
cancionero de la banda: usala con una canción por vez y dejá siempre el link a la fuente (el agente lo guarda).
Este repositorio y su página son públicos.
