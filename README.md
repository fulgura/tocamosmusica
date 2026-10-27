# Tocamos Música — Cancionero

Repertorio de la banda: quién toca cada tema en las 3 rondas y los acordes para ensayar.

Página: https://fulgura.github.io/tocamosmusica/

## Cómo está armado

- `datos/canciones.json`: todas las canciones (ronda, quiénes tocan, cifra).
- `datos/acordes.json`: posiciones de acordes propias de la banda (van primero en el diccionario).
- `herramientas/chords.py`: el diccionario de acordes (reconoce los acordes y arma las posiciones).
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

## Diccionario de acordes

El diccionario reconoce mayores, menores, 7, m7, maj7, 6, m6, sus2, sus4, 7sus4, add9, m(add9), 9, m9, maj9,
5, ° (dim), °7, m7(b5) y aum, escritos de las formas habituales (`D7(9)`, `Am7(b5)`, `E°7`, `C+`, `D7M`, `A4`…).
Para cada acorde muestra hasta 4 posiciones con el dedo de cada cuerda: primero las abiertas conocidas,
después las de cejilla y por último las que encuentra el programa ordenadas por comodidad.
Los nombres se muestran como están escritos en la cifra (Bb, Ab), y al transponer se usan sostenidos o
bemoles según el tono al que se llega.

Para usar una posición que no sale, o cambiar el orden, agregala en `datos/acordes.json`. Se puede copiar
tal cual de Cifra Club (sexta cuerda primero, X = no se toca); los dedos son opcionales:

```json
"G#°": {
  "posiciones": [{"trastes": "4 X 3 4 3 X", "dedos": "3 - 1 4 2 -"}],
  "fuente": "https://www.cifraclub.com/no-te-va-gustar/chau/"
}
```

Después se corre `python3 herramientas/construir.py`. Las posiciones calculadas se guardan en
`herramientas/acordes_cache.json`, que se rehace solo cuando cambia `datos/acordes.json` o el programa.

## Pruebas

```
cd herramientas && python3 test_agente.py && python3 test_acordes.py
```

Las pruebas no usan la API ni ningún sitio: trabajan con una página inventada.

## Aviso

Las letras y cifras de Cifra Club y La Cuerda tienen derechos de autor y los sitios pueden tener
condiciones de uso que limitan copiarlas de forma automática. Esta herramienta es para armar el
cancionero de la banda: usala con una canción por vez y dejá siempre el link a la fuente (el agente lo guarda).
Este repositorio y su página son públicos.
