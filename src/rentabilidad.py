"""Utilidad bruta sobre ventas con costo conocido; no estima ganancia neta."""
from decimal import Decimal, InvalidOperation


def simular_descuento(ingresos, costos, descuento):
    try:
        ingresos, costos, descuento = map(lambda x: Decimal(str(x)), (ingresos, costos, descuento))
    except InvalidOperation as error:
        raise ValueError('Introduce valores numéricos') from error
    if (not all(x.is_finite() for x in (ingresos, costos, descuento))
            or ingresos < 0 or costos < 0 or not 0 <= descuento <= 100):
        raise ValueError('El descuento debe estar entre 0 y 100 y los importes deben ser no negativos')
    ingresos_nuevos = (ingresos * (1 - descuento / 100)).quantize(Decimal('0.01'))
    utilidad = ingresos_nuevos - costos
    return {'ingresos': ingresos_nuevos, 'costos': costos, 'utilidad': utilidad,
            'margen': utilidad / ingresos_nuevos * 100 if ingresos_nuevos else None}


def calcular_rentabilidad(ventas):
    ingresos = costos = Decimal('0')
    conocidas = desconocidas = 0
    productos, categorias = {}, {}
    for venta in ventas:
        if venta.get('costo_unitario') is None:
            desconocidas += 1
            continue
        conocidas += 1
        ingreso = venta['cantidad'] * Decimal(str(venta['precio_unitario']))
        costo = venta['cantidad'] * Decimal(str(venta['costo_unitario']))
        ingresos += ingreso
        costos += costo
        for grupos, clave in ((productos, (venta['producto'], venta['categoria'])),
                             (categorias, venta['categoria'])):
            grupo = grupos.setdefault(clave, {'ingresos': Decimal('0'), 'costos': Decimal('0')})
            grupo['ingresos'] += ingreso
            grupo['costos'] += costo
    def ordenar(grupos):
        items = []
        for nombre, datos in grupos.items():
            ingreso, costo = datos['ingresos'], datos['costos']
            items.append(dict(nombre=' / '.join(nombre) if isinstance(nombre, tuple) else nombre,
                              **datos, utilidad=ingreso-costo,
                              margen=(ingreso-costo)/ingreso*100 if ingreso else None))
        return sorted(items, key=lambda x: (-x['utilidad'], x['nombre'].casefold()))
    return dict(ingresos=ingresos, costos=costos, utilidad=ingresos-costos,
                margen=(ingresos-costos)/ingresos*100 if ingresos else None,
                conocidas=conocidas, desconocidas=desconocidas,
                productos=ordenar(productos), categorias=ordenar(categorias))


def lineas_rentabilidad(datos):
    margen = f"{datos['margen']:.2f}%" if datos['margen'] is not None else 'No calculable'
    lineas = [
        'Utilidad bruta: ingresos menos costo de los productos vendidos; no incluye gastos operativos.',
        f"Registros con costo: {datos['conocidas']} | Sin costo: {datos['desconocidas']}",
        'Las ventas sin costo se excluyen del cálculo. No se asume costo cero.',
    ]
    if not datos['conocidas']:
        return lineas + ['Rentabilidad no calculable: importa ventas con costo_unitario.']
    lineas += [f"Ingresos con costo conocido: ${datos['ingresos']:,.2f}",
               f"Costo de productos vendidos: ${datos['costos']:,.2f}",
               f"Utilidad bruta: ${datos['utilidad']:,.2f}", f'Margen bruto: {margen}']
    for titulo, clave in [('PRODUCTOS POR UTILIDAD BRUTA', 'productos'), ('CATEGORÍAS POR UTILIDAD BRUTA', 'categorias')]:
        lineas.append(titulo)
        for item in datos[clave]:
            m = f"{item['margen']:.2f}%" if item['margen'] is not None else 'No calculable'
            alerta = 'PÉRDIDA BRUTA' if item['utilidad'] < 0 else ('MARGEN BAJO (<20%)' if item['margen'] is not None and item['margen'] < 20 else '')
            lineas.append(f"{item['nombre']}: utilidad ${item['utilidad']:,.2f} | margen {m} {alerta}".rstrip())
    lineas.append('El umbral de margen bajo (20%) es orientativo; debe ajustarse al negocio.')
    return lineas
