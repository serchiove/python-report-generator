"""Escenarios de caja constantes; cobros al cierre de cada mes."""
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import re


def proyectar_inversion(inversion, cobros, costo_productos, gastos, ahorros, meses):
    valores = []
    for nombre, valor in zip(('Inversión', 'Cobros', 'Costo de productos', 'Otros pagos', 'Ahorros'),
                             (inversion, cobros, costo_productos, gastos, ahorros)):
        try:
            texto = str(valor).strip()
            if re.fullmatch(r'[+-]?[0-9]+(?:\.[0-9]+)?\s*[kK]', texto):
                numero = Decimal(texto[:-1].strip()) * 1000
            else:
                numero = Decimal(texto)
        except (InvalidOperation, ValueError) as error:
            raise ValueError(f'{nombre}: usa un importe con punto decimal, por ejemplo 100000 o 100k') from error
        if not numero.is_finite() or not 0 <= numero <= Decimal('1000000000000'):
            raise ValueError(f'{nombre}: debe estar entre 0 y 1000000000000')
        if numero != numero.quantize(Decimal('0.01')):
            raise ValueError(f'{nombre}: usa como máximo dos decimales')
        valores.append(numero)
    try:
        horizonte = Decimal(str(meses))
    except InvalidOperation as error:
        raise ValueError('El horizonte debe ser un entero entre 1 y 120 meses') from error
    if not horizonte.is_finite() or not 1 <= horizonte <= 120 or horizonte != horizonte.to_integral_value():
        raise ValueError('El horizonte debe ser un entero entre 1 y 120 meses')
    meses = int(horizonte)
    inversion, cobros, costo_productos, gastos, ahorros = valores
    escenarios = []
    for nombre, factor in [('Conservador', Decimal('0.8')), ('Base', Decimal('1')), ('Optimista', Decimal('1.2'))]:
        entradas = ((cobros + ahorros) * factor).quantize(Decimal('0.01'))
        pagos = costo_productos + gastos
        flujo = entradas - pagos
        plazo = inversion / flujo if flujo > 0 else None
        mes_recuperacion = (0 if inversion == 0 else
                            int(plazo.to_integral_value(rounding=ROUND_CEILING)) if plazo is not None else None)
        # El saldo cero recupera la inversión; el excedente requiere saldo > 0.
        mes_excedente = (int(inversion // flujo) + 1) if flujo > 0 else None
        saldos = [-inversion + flujo * n for n in range(meses + 1)]
        escenarios.append(dict(nombre=nombre, entradas=entradas, pagos=pagos, flujo=flujo,
                               plazo=plazo, recuperacion=mes_recuperacion, excedente=mes_excedente,
                               saldos=saldos))
    return dict(inversion=inversion, cobros=cobros, costo_productos=costo_productos,
                gastos=gastos, ahorros=ahorros, meses=meses, escenarios=escenarios)


def texto_recuperacion(escenario, meses):
    mes = escenario['recuperacion']
    if mes == 0:
        return 'Sin inversión inicial por recuperar'
    if mes is None:
        return 'No se recupera con este flujo mensual'
    if mes > meses:
        return f'Fuera del horizonte: mes {mes}'
    return f'Mes {mes} (cobros al cierre de mes)'


def explicar_resultado(datos):
    """Explica el saldo neto de la inversión en términos comerciales."""
    base = datos['escenarios'][1]
    inversion, flujo = datos['inversion'], base['flujo']
    lineas = [f"Usted invierte {inversion:,.2f} al comenzar.",
              f"Cada mes obtiene {base['entradas']:,.2f} entre cobros y ahorros, y paga {base['pagos']:,.2f}."]
    if flujo > 0:
        lineas.append(f"Le quedan {flujo:,.2f} de caja por mes después de esos pagos, antes de recuperar la inversión inicial.")
    elif flujo < 0:
        lineas.append(f"Cada mes le faltan {-flujo:,.2f} para cubrir los pagos. Con estos supuestos el saldo empeora.")
    else:
        lineas.append('Los cobros y ahorros solo cubren los pagos mensuales: no queda dinero para recuperar la inversión.')
    hitos = sorted({n for n in (1, 3, 6, 12, datos['meses']) if n <= datos['meses']})
    for mes in hitos:
        saldo = base['saldos'][mes]
        periodo = 'Al terminar el mes 1' if mes == 1 else f'Al terminar {mes} meses'
        if saldo < 0:
            lineas.append(f'{periodo}: todavía le faltan {-saldo:,.2f} para recuperar lo invertido.')
        elif saldo == 0:
            lineas.append(f'{periodo}: recuperó exactamente la inversión. El dinero adicional acumulado es 0.00.')
        else:
            lineas.append(f'{periodo}: recuperó toda la inversión y le quedan {saldo:,.2f} adicionales acumulados.')
    mes = base['recuperacion']
    if inversion == 0:
        lineas.append('No existe un desembolso inicial que recuperar en este escenario.')
    elif mes is None:
        lineas.append('La inversión no se recupera mientras se mantenga este flujo mensual.')
    elif mes > datos['meses']:
        lineas.append(f"No recupera la inversión en los {datos['meses']} meses mostrados. Si todo se mantiene igual, la recuperaría al cierre del mes {mes}.")
    else:
        excedente = base['excedente']
        lineas.append(f'Recupera la inversión al cierre del mes {mes}; empieza a tener dinero adicional acumulado al cierre del mes {excedente}.')
    lineas.append('“Adicional acumulado” ya descuenta la inversión inicial: no vuelva a restarla. Es caja estimada, no ganancia neta contable; depende de que los supuestos se cumplan y de incluir todos los pagos relevantes.')
    return lineas


def exportar_proyeccion(datos, ruta, alcance):
    from pathlib import Path
    from xml.sax.saxutils import escape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.graphics.shapes import Drawing, Line, String, PolyLine, Rect
    from src.grafico_inversion import escala_saldos, formato_eje
    ruta = Path(ruta)
    if ruta.suffix.lower() != '.pdf':
        raise ValueError('El destino debe tener extensión .pdf')
    ruta.parent.mkdir(parents=True, exist_ok=True)
    estilos = getSampleStyleSheet()
    elementos = [Paragraph('Recuperación de la inversión', estilos['Title']),
                 Paragraph('Escenario hipotético: ' + escape(alcance), estilos['Heading2']),
                 Paragraph('Importes en una misma moneda. No se utilizan totales históricos como ingresos mensuales. '
                           'Se supone volumen constante, cobros y pagos al cierre de mes y ausencia de financiación. '
                           'Incluye todos los pagos relevantes en los supuestos. No calcula beneficio contable ni valor presente.', estilos['BodyText']), Spacer(1, 14)]
    filas = [['Supuesto', 'Importe / plazo']]
    for etiqueta, clave in [('Inversión inicial', 'inversion'), ('Cobros mensuales', 'cobros'), ('Pagos mensuales de productos', 'costo_productos'), ('Otros pagos mensuales', 'gastos'), ('Ahorros mensuales', 'ahorros')]:
        filas.append([etiqueta, f"{datos[clave]:,.2f}"])
    filas.append(['Horizonte', f"{datos['meses']} meses"])
    def tabla(filas, anchos):
        t = Table(filas, colWidths=anchos, repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8eff9')),
                               ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                               ('FONTSIZE', (0,0), (-1,-1), 9), ('BOTTOMPADDING', (0,0), (-1,-1), 7),
                               ('TOPPADDING', (0,0), (-1,-1), 7), ('LINEBELOW', (0,0), (-1,-1), .3, colors.lightgrey)]))
        return t
    elementos.append(tabla(filas, [310, 180]))
    elementos += [Spacer(1, 14), Paragraph('Saldo acumulado después de la inversión', estilos['Heading2'])]
    dibujo = Drawing(490, 230)
    valores = [float(x) for e in datos['escenarios'] for x in e['saldos']]
    minimo, maximo, marcas = escala_saldos(valores)
    rango = maximo-minimo
    def y(v): return 35 + (float(v)-minimo)/rango*155
    if minimo <= 0 <= maximo:
        dibujo.add(Rect(58,35,417,y(0)-35,fillColor=colors.HexColor('#fff7f7'),strokeColor=None))
        dibujo.add(Rect(58,y(0),417,190-y(0),fillColor=colors.HexColor('#f0fdf4'),strokeColor=None))
        dibujo.add(Line(58, y(0), 475, y(0), strokeColor=colors.grey))
    else:
        dibujo.add(String(58,200,'Escala ampliada: el saldo cero está fuera de vista.',fontSize=8))
    for v in marcas:
        dibujo.add(Line(58,y(v),475,y(v),strokeColor=colors.HexColor('#e2e8f0'),strokeWidth=.3))
        dibujo.add(String(52, y(v)-3, formato_eje(v), textAnchor='end', fontSize=7))
    for i, e in enumerate(datos['escenarios']):
        color = colors.HexColor(('#b45309', '#2563eb', '#15803d')[i])
        puntos = [c for n,v in enumerate(e['saldos']) for c in (58+417*n/datos['meses'], y(v))]
        dibujo.add(PolyLine(puntos, strokeColor=color, strokeWidth=1.8))
        dibujo.add(String(58+i*140, 215, e['nombre'], fillColor=color, fontSize=9))
    dibujo.add(String(58, 16, 'Mes 0', fontSize=8))
    dibujo.add(String(475, 16, f"Mes {datos['meses']}", textAnchor='end', fontSize=8))
    elementos.append(dibujo)
    elementos += [Paragraph('Escenarios: los cobros y ahorros cambian -20% y +20%; los pagos permanecen constantes. '
                            'Son sensibilidades ilustrativas, no probabilidades. La línea cero indica capital recuperado.', estilos['BodyText']), PageBreak(),
                 Paragraph('¿Cuánto dinero le queda?', estilos['Title'])]
    for linea in explicar_resultado(datos):
        elementos.append(Paragraph(escape(linea), estilos['BodyText']))
        elementos.append(Spacer(1,6))
    elementos += [Spacer(1, 10), Paragraph('Comparación de escenarios', estilos['Heading2'])]
    for e in datos['escenarios']:
        elementos.append(Paragraph(escape(f"{e['nombre']}: flujo mensual {e['flujo']:,.2f}; "
                                          f"{texto_recuperacion(e, datos['meses'])}; saldo final {e['saldos'][-1]:,.2f}."), estilos['BodyText']))
        elementos.append(Spacer(1,6))
    elementos += [PageBreak(), Paragraph('Detalle del saldo acumulado por mes', estilos['Title']),
                  Paragraph('Cada importe ya descuenta la inversión inicial. Un saldo negativo indica dinero pendiente de recuperar; un saldo positivo es el excedente acumulado.', estilos['BodyText']), Spacer(1,12)]
    filas = [['Mes', 'Conservador', 'Base', 'Optimista']]
    filas += [[str(n)] + [f"{e['saldos'][n]:,.2f}" for e in datos['escenarios']] for n in range(datos['meses']+1)]
    elementos.append(tabla(filas, [55, 145, 145, 145]))
    elementos += [Spacer(1, 12), Paragraph('Los resultados dependen de los supuestos y no garantizan ganancias. '
                    'Para medir la inversión en software, utiliza únicamente cobros adicionales y ahorros atribuibles a la herramienta, '
                    'así como los pagos adicionales que genera.', estilos['BodyText'])]
    def pie(c, doc):
        c.setFont('Helvetica', 8)
        c.drawString(50, 28, 'Proyección comercial | Escenario hipotético')
        c.drawRightString(545, 28, str(doc.page))
    SimpleDocTemplate(str(ruta), title='Proyección de recuperación de inversión',
                      leftMargin=50, rightMargin=50, topMargin=40, bottomMargin=50).build(elementos, onFirstPage=pie, onLaterPages=pie)
    return ruta
