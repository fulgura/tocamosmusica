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

    def test_cejilla_de_siempre_primero(self):
        self.assertEqual(CD.variants('C#m', 1, 'm', 1)[0]['f'], [-1, 4, 6, 6, 5, 4])
        self.assertEqual(CD.variants('G#', 8, '', 8)[0]['f'], [4, 6, 6, 5, 4, 4])


if __name__ == '__main__':
    unittest.main()
