"""Pruebas del diccionario de acordes.  Correr con:  python3 herramientas/test_acordes.py"""
import unittest

import chords as CD


class Acordes(unittest.TestCase):
    def test_reconoce_cifras(self):
        casos = {'Bbm': 'A#m', 'G#°': 'G#dim', 'D7(9)': 'D9', 'Am7(b5)': 'Am7b5', 'E°7': 'Edim7',
                 'Cadd9': 'Cadd9', 'A7sus4': 'A7sus4', 'C+': 'Caug', 'F#/A#': 'F#/A#', 'Em/d': 'Em/D', 'D7M': 'Dmaj7'}
        for escrito, clave in casos.items():
            self.assertEqual(CD.canon(escrito)[0], clave, escrito)
        for no in ('Final', 'Corazón', 'x2', 'Dmej4'):
            self.assertIsNone(CD.canon(no), no)

    def test_conserva_como_se_escribe(self):
        self.assertEqual(CD.canon('Bbm/F')[4:], ('Bb', 'F'))

    def test_separa_tokens(self):
        self.assertEqual(CD.TOKRE.findall('Bm G#° (Am) D7(9) C-G | x2'), ['Bm', 'G#°', 'Am', 'D7(9)', 'C', 'G', 'x2'])

    def test_posiciones_conocidas_son_correctas(self):
        for k, fr in CD.CUR.items():
            c = CD.canon(k)
            self.assertTrue(CD.valid(fr, *c[1:4]), k)

    def test_posicion_propia_va_primero(self):
        propios, _ = CD.cargar_propios()
        v = CD.variants('G#dim', 8, 'dim', 8, propios['G#dim'])
        self.assertEqual(v[0]['f'], [4, -1, 3, 4, 3, -1])
        self.assertEqual(v[0]['d'], [3, 0, 1, 4, 2, 0])

    def test_todas_tienen_posiciones_tocables(self):
        for rp in range(12):
            for q in CD.QUAL:
                v = CD.variants(CD.NAMES[rp] + q, rp, q, rp)
                self.assertGreaterEqual(len(v), 2, CD.NAMES[rp] + q)
                for p in v:
                    self.assertTrue(CD.valid(tuple(p['f']), rp, q, rp), (CD.NAMES[rp] + q, p['f']))

    def test_tipos_nuevos(self):
        casos = {'E7(#9)': 'E7#9', 'A7(b9)': 'A7b9', 'C6/9': 'C69', 'C6(9)': 'C69', 'Am(maj7)': 'Ammaj7', 'Am7M': 'Ammaj7',
                 'G13': 'G13', 'G7(13)': 'G13', 'A9sus4': 'A9sus4', 'D11': 'D11', 'Am7(11)': 'Am11', 'Cadd11': 'Cadd11',
                 'F#7(b5)': 'F#7b5', 'G7(#5)': 'G7#5', 'Dm6/9': 'Dm69', 'Bb7M(9)': 'A#maj9'}
        for escrito, clave in casos.items():
            self.assertEqual(CD.canon(escrito)[0], clave, escrito)

    def test_parentesis_sin_septima_es_add(self):
        # Como en Cifra Club: C(9) = Cadd9, Am(9) = Am(add9); con séptima sí es novena: D7(9) = D9.
        self.assertEqual(CD.canon('C(9)')[0], 'Cadd9')
        self.assertEqual(CD.canon('Am(9)')[0], 'Amadd9')
        self.assertEqual(CD.canon('D7(9)')[0], 'D9')
        self.assertEqual(CD.canon('G(11)')[0], 'Gadd11')

    def test_sin_posiciones_raras(self):
        raras = {'Am': [5, 3, 2, 2, 5, -1], 'Bm': [7, 5, 4, 4, 7, -1], 'Em': [-1, -1, 2, 0, 0, 3],
                 'B7': [7, 6, 4, 4, 4, 5], 'E5': [0, 2, 2, 4, 0, 0]}
        for k, fr in raras.items():
            c = CD.canon(k)
            self.assertNotIn(fr, [p['f'] for p in CD.variants(c[0], *c[1:4])], k)

    def test_alternativas_en_zona_media_antes_que_en_el_12(self):
        self.assertEqual(CD.variants('A', 9, '', 9)[2]['f'], [-1, -1, 7, 9, 10, 9])

    def test_cejilla_de_siempre_primero(self):
        self.assertEqual(CD.variants('C#m', 1, 'm', 1)[0]['f'], [-1, 4, 6, 6, 5, 4])
        self.assertEqual(CD.variants('G#', 8, '', 8)[0]['f'], [4, 6, 6, 5, 4, 4])


if __name__ == '__main__':
    unittest.main()
