"""Pruebas de las cifras en archivos de texto.  Correr con:  python3 herramientas/test_cifras.py

Usa una cifra inventada, con el mismo encabezado y pie que pone La Cuerda.
"""
import os
import shutil
import tempfile
import unittest

import cifras as CF

PEGADA = """=====================================================================
|             TABLATURAS Y ACORDES DE MÚSICA EN ESPAÑOL             |
+-------------------------- lacuerda.net ---------------------------+
| ARTISTA: Banda Ficticia                                           |
| CANCION: LA CANCION DE PRUEBA                                     |
+------------------------------------------------------ACO-ficti001-+
| TRANS:   alguien                                                  |
=====================================================================

\tAm           G
Una letra inventada para probar\xa0\r
C                 D
que nada se rompe al pegar

=========================== lacuerda.net ============================
Este fichero es trabajo propio de su transcriptor...
=========================== lacuerda.net ============================
"""


class Cifras(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.orig = CF.DIR
        CF.DIR = self.tmp

    def tearDown(self):
        CF.DIR = self.orig
        shutil.rmtree(self.tmp)

    def test_saca_encabezado_y_pie_de_la_cuerda(self):
        t = CF.limpiar(PEGADA)
        self.assertTrue(t.startswith('    Am           G'))
        self.assertTrue(t.endswith('que nada se rompe al pegar'))
        self.assertNotIn('lacuerda', t)
        self.assertNotIn('\r', t)
        self.assertNotIn('\xa0', t)

    def test_texto_sin_encabezado_queda_igual(self):
        t = 'Am  G\nalgo\n\n[Solo] C G'
        self.assertEqual(CF.limpiar('\n\n' + t + '\n\n'), t)

    def test_titulo_y_artista_del_encabezado(self):
        self.assertEqual(CF.encabezado(PEGADA), {'artist': 'Banda Ficticia', 'title': 'La Cancion de Prueba'})

    def test_archivo_suelto_aparece(self):
        CF.guardar('nueva', PEGADA)
        CF.guardar('ya-esta', 'Am')
        self.assertEqual(CF.sueltas({'ya-esta'}),
                         [{'id': 'nueva', 'title': 'La Cancion de Prueba', 'artist': 'Banda Ficticia'}])

    def test_sin_archivo_o_vacio(self):
        self.assertIsNone(CF.leer('no-existe'))
        CF.guardar('vacia', '\n\n')
        self.assertIsNone(CF.leer('vacia'))


if __name__ == '__main__':
    unittest.main()
