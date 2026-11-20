"""38 casos adicionales: límites CSV, gráficos, PDF y PostgreSQL real.

Los casos de datos se registran individualmente con nombres descriptivos para
que unittest y GitHub Actions muestren el resultado de cada escenario.
"""

import csv
import os
from datetime import date
from decimal import Decimal
from io import StringIO
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest

import psycopg

from src.extractor import cargar_lote
from src.generador import generar_reporte
from src.generador_pdf import exportar_pdf
from src.grafico_categorias import preparar_datos_grafico
from src.procesador import calcular_resumen, consultar_resumen
from src.repositorio import guardar_ventas, consultar_ventas
from src.rentabilidad import calcular_rentabilidad, simular_descuento, lineas_rentabilidad
from src.proyeccion import proyectar_inversion, texto_recuperacion, exportar_proyeccion, explicar_resultado
from src.grafico_inversion import escala_saldos, formato_eje
import test_postgresql as pruebas_bd


class LimitesCSVTest(unittest.TestCase):
    def leer_fila(self, columna, valor):
        fila = ['2026-01-15', 'Producto', 'Categoría', '2', '3.50']
        fila[columna] = valor
        contenido = StringIO(newline='')
        escritor = csv.writer(contenido)
        escritor.writerow(['fecha', 'producto', 'categoria', 'cantidad', 'precio_unitario'])
        escritor.writerow(fila)
        with TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'ventas.csv'
            ruta.write_text(contenido.getvalue(), encoding='utf-8', newline='')
            return cargar_lote(ruta)


# Cada entrada representa una regla o frontera diferente del contrato CSV.
INVALIDOS = [
    ('fecha_no_bisiesta', 0, '2025-02-29', 'fecha inexistente'),
    ('fecha_mes_cero', 0, '2026-00-15', 'fecha inexistente'),
    ('fecha_mes_sin_dos_digitos', 0, '2026-1-15', 'YYYY-MM-DD'),
    ('fecha_con_hora', 0, '2026-01-15T12:00:00', 'YYYY-MM-DD'),
    ('cantidad_con_signo_mas', 3, '+2', 'entero positivo'),
    ('cantidad_notacion_cientifica', 3, '2e3', 'entero positivo'),
    ('cantidad_digitos_unicode', 3, '٢', 'entero positivo'),
    ('cantidad_con_separador', 3, '1,000', 'entero positivo'),
    ('precio_notacion_cientifica', 4, '1e2', 'punto y como máximo'),
    ('precio_sin_entero', 4, '.50', 'punto y como máximo'),
    ('precio_con_punto_final', 4, '1.', 'punto y como máximo'),
    ('categoria_con_caracter_nulo', 2, 'Hogar\x00Oficina', 'carácter nulo'),
]


def caso_invalido(columna, valor, mensaje):
    def test(self):
        ventas, errores, _ = self.leer_fila(columna, valor)
        self.assertEqual(ventas, [])
        self.assertEqual(len(errores), 1)
        self.assertIn('Fila 2:', errores[0])
        self.assertIn(mensaje, errores[0])
    return test


for nombre, columna, valor, mensaje in INVALIDOS:
    setattr(LimitesCSVTest, 'test_rechaza_' + nombre, caso_invalido(columna, valor, mensaje))


VALIDOS = [
    ('fecha_bisiesta', 0, '2024-02-29', 'fecha', date(2024, 2, 29)),
    ('cantidad_limite_postgresql', 3, '2147483647', 'cantidad', 2147483647),
    ('precio_maximo_admitido', 4, '9999999999.99', 'precio_unitario', Decimal('9999999999.99')),
    ('precio_un_centavo', 4, '0.01', 'precio_unitario', Decimal('0.01')),
    ('producto_longitud_limite', 1, 'P' * 150, 'producto', 'P' * 150),
    ('categoria_longitud_limite', 2, 'C' * 100, 'categoria', 'C' * 100),
    ('producto_comillas_y_coma', 1, 'Monitor, edición "Pro"', 'producto', 'Monitor, edición "Pro"'),
    ('precio_con_ceros_iniciales', 4, '0003.50', 'precio_unitario', Decimal('3.50')),
]


def caso_valido(columna, valor, campo, esperado):
    def test(self):
        ventas, errores, _ = self.leer_fila(columna, valor)
        self.assertEqual(errores, [])
        self.assertEqual(len(ventas), 1)
        self.assertEqual(ventas[0][campo], esperado)
        self.assertEqual(ventas[0]['total'], ventas[0]['cantidad'] * ventas[0]['precio_unitario'])
        if campo == 'precio_unitario' and esperado == Decimal('9999999999.99'):
            # Contrato extendido: costo opcional y validación sin romper CSV antiguos.
            for costo, valido in [('0.00', True), ('12.50', True), ('', True),
                                   ('-1', False), ('NaN', False), ('1e2', False),
                                   ('1.001', False), ('10000000000', False)]:
                with self.subTest(costo_unitario=costo), TemporaryDirectory() as d:
                    ruta = Path(d) / 'costos.csv'
                    ruta.write_text('fecha,producto,categoria,cantidad,precio_unitario,costo_unitario\n'
                                    f'2026-01-15,A,B,2,20.00,{costo}\n', encoding='utf-8')
                    filas, errores_costo, _ = cargar_lote(ruta)
                    self.assertEqual(len(filas), int(valido))
                    if valido:
                        self.assertEqual(filas[0]['costo_unitario'], Decimal(costo) if costo else None)
                    else:
                        self.assertEqual(len(errores_costo), 1)
    return test


for nombre, columna, valor, campo, esperado in VALIDOS:
    setattr(LimitesCSVTest, 'test_acepta_' + nombre, caso_valido(columna, valor, campo, esperado))


class GraficoAdicionalTest(unittest.TestCase):
    def test_resumen_sin_clave_categorias(self):
        datos = preparar_datos_grafico({})
        self.assertEqual(datos['items'], [])
        self.assertEqual(datos['lider'], 'Sin datos')

    def test_no_modifica_lista_del_resumen(self):
        grupos = [('B', Decimal('1')), ('A', Decimal('5'))]
        original = list(grupos)
        datos = preparar_datos_grafico({'por_categoria': grupos})
        self.assertEqual(grupos, original)
        self.assertEqual(datos['lider'], 'A')

    def test_precision_de_centavos(self):
        datos = preparar_datos_grafico({'por_categoria': [('A', '0.10'), ('B', '0.20')]})
        self.assertEqual(datos['total'], Decimal('0.30'))
        self.assertEqual(datos['maximo'], Decimal('0.20'))
        for descuento, utilidad, margen in [('0', '350', '35'), ('10', '250', None),
                                            ('35', '0', '0'), ('50', '-150', '-30'), ('100', '-650', None)]:
            with self.subTest(descuento=descuento):
                resultado = simular_descuento('1000', '650', descuento)
                self.assertEqual(resultado['utilidad'], Decimal(utilidad))
                if margen is not None:
                    self.assertEqual(resultado['margen'], Decimal(margen))
                if descuento == '100':
                    self.assertIsNone(resultado['margen'])
        for invalido in ['-1', '101', 'NaN', 'Infinity', 'texto']:
            with self.subTest(invalido=invalido), self.assertRaises(ValueError):
                simular_descuento(1000, 650, invalido)

    def test_categoria_unica_representa_cien_por_ciento(self):
        datos = preparar_datos_grafico({'por_categoria': [('Única', 25)]})
        self.assertEqual(datos['participacion_lider'], Decimal('100'))
        self.assertEqual(datos['cantidad'], 1)
        # Escenarios financieros asociados a decisiones comerciales.
        casos = [
            (('3000','0','0','50','550','12'), 6, 7, '3000'),
            (('10000','6000','3500','1000','0','12'), 7, 7, '8000'),
            (('1000','100','0','100','0','12'), None, None, '-1000'),
            (('1000','100','0','200','0','12'), None, None, '-2200'),
            (('0','100','0','0','0','12'), 0, 1, '1200'),
            (('10000','100','0','0','0','12'), 100, 101, '-8800'),
            (('0','0','0','0','0','12'), 0, None, '0'),
            (('0.03','0.01','0','0','0','3'), 3, 4, '0'),
        ]
        for args, recuperacion, excedente, saldo in casos:
            with self.subTest(proyeccion=args):
                proyeccion = proyectar_inversion(*args)
                base = proyeccion['escenarios'][1]
                self.assertEqual(base['recuperacion'], recuperacion)
                self.assertEqual(base['excedente'], excedente)
                self.assertEqual(base['saldos'][-1], Decimal(saldo))
                self.assertEqual(len(base['saldos']), int(args[-1])+1)
                self.assertEqual(base['saldos'][0], -Decimal(args[0]))
                if recuperacion is not None and recuperacion > int(args[-1]):
                    self.assertIn('Fuera del horizonte', texto_recuperacion(base, int(args[-1])))
                if recuperacion is None:
                    self.assertIn('No se recupera', texto_recuperacion(base, int(args[-1])))
        escenarios = proyectar_inversion('3000','0','0','50','550','12')['escenarios']
        self.assertEqual([e['flujo'] for e in escenarios], [Decimal('390'), Decimal('500'), Decimal('610')])
        self.assertEqual([e['recuperacion'] for e in escenarios], [8,6,5])
        mensaje = '\n'.join(explicar_resultado(proyectar_inversion('3000','0','0','50','550','12')))
        for esperado in ['500.00 de caja por mes', 'faltan 1,500.00', 'adicional acumulado es 0.00',
                         'le quedan 3,000.00 adicionales', 'cierre del mes 6', 'cierre del mes 7']:
            self.assertIn(esperado, mensaje)
        mensaje = '\n'.join(explicar_resultado(proyectar_inversion(1000, 0, 0, 100, 0, 3)))
        self.assertIn('faltan 1,300.00', mensaje)
        self.assertIn('no se recupera', mensaje)
        for importe in ['100k', '100K', ' 100 k ', '100000']:
            with self.subTest(inversion_100k=importe):
                proyeccion = proyectar_inversion(importe, '30k', '15k', '5k', 0, 12)
                base = proyeccion['escenarios'][1]
                self.assertEqual(proyeccion['inversion'], Decimal('100000'))
                self.assertEqual(base['flujo'], Decimal('10000'))
                self.assertEqual(base['recuperacion'], 10)
                self.assertEqual(base['saldos'][-1], Decimal('20000'))
                self.assertIn('20,000.00 adicionales', '\n'.join(explicar_resultado(proyeccion)))
        self.assertEqual(proyectar_inversion('1.5k', 500, 0, 0, 0, 3)['inversion'], Decimal('1500'))
        fuera = proyectar_inversion('100k', 0, 0, 50, 550, 12)
        self.assertIn('mes 200', texto_recuperacion(fuera['escenarios'][1], 12))
        self.assertEqual(formato_eje(100000), '100 mil')
        self.assertEqual(formato_eje(-1500000), '-1.5 M')
        self.assertEqual(formato_eje(0), '0')
        for valores in [[-100000, -94000], [-100000,20000], [0,0], [100000,100000], [-.03,.02]]:
            with self.subTest(escala=valores):
                inferior, superior, marcas = escala_saldos(valores)
                self.assertLessEqual(inferior, min(valores))
                self.assertGreaterEqual(superior, max(valores))
                self.assertGreater(superior, inferior)
                self.assertTrue(3 <= len(marcas) <= 10)
        self.assertLess(escala_saldos([-100000,-94000])[1], 0)

    def test_cero_junto_a_categoria_con_ventas(self):
        datos = preparar_datos_grafico({'por_categoria': [('Sin ventas', 0), ('Activa', 50)]})
        self.assertEqual([x['porcentaje'] for x in datos['items']], [Decimal('100'), Decimal('0')])

    def test_cien_categorias_conservan_total_y_orden(self):
        grupos = [(f'Categoría {n}', n) for n in range(1, 101)]
        datos = preparar_datos_grafico({'por_categoria': grupos})
        self.assertEqual(datos['cantidad'], 100)
        self.assertEqual(datos['total'], Decimal('5050'))
        self.assertEqual(datos['lider'], 'Categoría 100')
        self.assertEqual(datos['items'][-1]['importe'], Decimal('1'))
        for indice in range(5):
            for valor in ['-1', 'NaN', 'Infinity', 'texto', '0.001', '1000000000001']:
                with self.subTest(campo=indice, importe_invalido=valor):
                    args = ['1000','100','10','20','5','12']
                    args[indice] = valor
                    with self.assertRaises(ValueError):
                        proyectar_inversion(*args)
        for meses in ['0','121','1.5','NaN','Infinity','texto']:
            with self.subTest(meses=meses), self.assertRaises(ValueError):
                proyectar_inversion(1000,100,10,20,5,meses)


class PDFAdicionalTest(unittest.TestCase):
    def exportar(self, carpeta, ventas=None, incidencias=None, destino='salida.pdf'):
        resumen = calcular_resumen(ventas or [])
        txt = generar_reporte(resumen, incidencias, Path(carpeta), 'fuente.txt')
        original = txt.read_bytes()
        pdf = exportar_pdf(txt, Path(carpeta) / destino)
        contenido = pdf.read_bytes()
        self.assertTrue(contenido.startswith(b'%PDF-'))
        self.assertTrue(contenido.rstrip().endswith(b'%%EOF'))
        self.assertEqual(txt.read_bytes(), original)
        return contenido

    def test_exporta_resumen_de_base_vacia(self):
        with TemporaryDirectory() as d:
            self.exportar(d)

    def test_crea_carpetas_de_destino_anidadas(self):
        with TemporaryDirectory() as d:
            self.exportar(d, destino='nueva/subcarpeta/salida.pdf')
            self.assertTrue((Path(d) / 'nueva/subcarpeta/salida.pdf').is_file())
            datos = proyectar_inversion(3000, 0, 0, 50, 550, 12)
            original = list(datos['escenarios'][1]['saldos'])
            salida = exportar_proyeccion(datos, Path(d)/'inversion/proyeccion.pdf', 'Software <ejemplo> & ahorros')
            self.assertTrue(salida.read_bytes().startswith(b'%PDF-'))
            self.assertEqual(datos['escenarios'][1]['saldos'], original)
            with self.assertRaises(ValueError):
                exportar_proyeccion(datos, Path(d)/'invalido.txt', 'Software')

    def test_nombres_con_marcado_xml_no_rompen_pdf(self):
        ventas = [dict(total=Decimal('12.50'), cantidad=1, categoria='A & B <oficina>', producto='<b>Producto</b>')]
        with TemporaryDirectory() as d:
            self.exportar(d, ventas, ['Fila 3: <valor> & dato inválido'])

    def test_pdf_con_precio_cero(self):
        ventas = [dict(total=Decimal('0.00'), cantidad=2, categoria='Promoción', producto='Muestra')]
        with TemporaryDirectory() as d:
            self.exportar(d, ventas, [])
            rentabilidad = calcular_rentabilidad([
                dict(producto='Muestra', categoria='Promoción', cantidad=2,
                     precio_unitario=Decimal('0'), costo_unitario=Decimal('3'))])
            self.assertEqual(rentabilidad['utilidad'], Decimal('-6'))
            self.assertIsNone(rentabilidad['margen'])
            resumen = calcular_resumen(ventas)
            resumen['rentabilidad'] = rentabilidad
            fuente = generar_reporte(resumen, [], Path(d), 'rentabilidad.txt')
            self.assertIn('PÉRDIDA BRUTA', fuente.read_text(encoding='utf-8'))
            exportar_pdf(fuente, Path(d) / 'rentabilidad.pdf')
            self.assertTrue((Path(d) / 'rentabilidad.pdf').read_bytes().startswith(b'%PDF-'))

    def test_reporte_extenso_genera_mas_de_dos_paginas(self):
        ventas = [dict(total=Decimal('10'), cantidad=1, categoria=f'Grupo {n}', producto=f'Producto {n}') for n in range(100)]
        with TemporaryDirectory() as d:
            contenido = self.exportar(d, ventas, [])
            paginas = re.search(rb'/Count\s+(\d+)\b', contenido)
            self.assertIsNotNone(paginas)
            self.assertGreater(int(paginas.group(1)), 2)

    def test_fuente_inexistente_no_crea_pdf(self):
        with TemporaryDirectory() as d:
            destino = Path(d) / 'salida.pdf'
            with self.assertRaises(FileNotFoundError):
                exportar_pdf(Path(d) / 'inexistente.txt', destino)
            self.assertFalse(destino.exists())


@unittest.skipUnless(
    os.environ.get('POSTGRES_TEST_DATABASE')
    and os.environ.get('POSTGRES_TEST_DATABASE') == os.environ.get('PGDATABASE'),
    'Configura la base PostgreSQL aislada de pruebas',
)
class PostgreSQLAdicionalTest(unittest.TestCase):
    setUp = pruebas_bd.PostgreSQLTest.setUp

    def test_misma_fila_en_otro_lote_es_otra_venta(self):
        guardar_ventas(self.conexion, [self.ventas[0]], self.lote)
        self.assertEqual(guardar_ventas(self.conexion, [self.ventas[0]], 'a' * 64), 1)
        self.assertEqual(len(consultar_ventas(self.conexion)), 2)

    def test_precio_historico_de_producto_se_conserva(self):
        otras = [dict(self.ventas[0], costo_unitario=Decimal('50')),
                 dict(self.ventas[0], fila_origen=3, precio_unitario=Decimal('99.99'), costo_unitario=Decimal('70')),
                 dict(self.ventas[0], fila_origen=4)]
        guardar_ventas(self.conexion, otras, self.lote)
        filas = consultar_ventas(self.conexion)
        self.assertEqual([v['precio_unitario'] for v in filas], [Decimal('85.50'), Decimal('99.99'), Decimal('85.50')])
        self.assertEqual([v['costo_unitario'] for v in filas], [Decimal('50'), Decimal('70'), None])
        datos = calcular_rentabilidad(filas)
        self.assertEqual((datos['conocidas'], datos['desconocidas']), (2, 1))
        self.assertEqual(datos['ingresos'], Decimal('370.98'))
        self.assertEqual(datos['costos'], Decimal('240'))
        self.assertEqual(datos['utilidad'], Decimal('130.98'))
        self.assertEqual(guardar_ventas(self.conexion, otras, self.lote), 0)
        self.assertEqual(calcular_rentabilidad(consultar_ventas(self.conexion)), datos)
        self.assertIn('Rentabilidad no calculable', '\n'.join(lineas_rentabilidad(calcular_rentabilidad([self.ventas[0]]))))
        for costo in ['-1', 'NaN', 'Infinity', '1.001', '10000000000']:
            with self.subTest(costo=costo), self.assertRaises(ValueError):
                guardar_ventas(self.conexion, [dict(self.ventas[0], costo_unitario=costo)], 'c' * 64)
        with self.assertRaises(psycopg.errors.CheckViolation):
            self.conexion.execute('UPDATE ventas SET costo_unitario = -1')
        self.assertEqual(self.conexion.execute('SELECT count(*) AS n FROM productos').fetchone()['n'], 1)

    def test_lote_vacio_no_crea_catalogos(self):
        self.assertEqual(guardar_ventas(self.conexion, [], self.lote), 0)
        self.assertEqual(self.conexion.execute('SELECT count(*) AS n FROM categorias').fetchone()['n'], 0)

    def test_sql_rechaza_cantidad_cero(self):
        guardar_ventas(self.conexion, [self.ventas[0]], self.lote)
        with self.assertRaises(psycopg.errors.CheckViolation):
            self.conexion.execute('UPDATE ventas SET cantidad = 0')
        self.assertEqual(consultar_ventas(self.conexion)[0]['cantidad'], 2)

    def test_sql_rechaza_categoria_vacia(self):
        with self.assertRaises(psycopg.errors.CheckViolation):
            self.conexion.execute('INSERT INTO categorias (nombre) VALUES (%s)', ('   ',))
        self.assertEqual(self.conexion.execute('SELECT count(*) AS n FROM categorias').fetchone()['n'], 0)

    def test_resumen_suma_distintos_lotes(self):
        guardar_ventas(self.conexion, [self.ventas[0]], self.lote)
        guardar_ventas(self.conexion, [dict(self.ventas[0], cantidad=1, precio_unitario=Decimal('0.10'))], 'b' * 64)
        resumen = consultar_resumen(self.conexion)
        self.assertEqual(resumen['numero_ventas'], 2)
        self.assertEqual(resumen['total_facturado'], Decimal('171.10'))
        self.assertEqual(resumen['unidades_vendidas'], 3)


if __name__ == '__main__':
    unittest.main()
