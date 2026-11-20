"""Escalas legibles para saldos grandes y variaciones pequeñas."""
import math


def formato_eje(valor):
    absoluto = abs(valor)
    if absoluto >= 1000000:
        return f'{valor / 1000000:,.2f}'.rstrip('0').rstrip('.') + ' M'
    if absoluto >= 1000:
        return f'{valor / 1000:,.2f}'.rstrip('0').rstrip('.') + ' mil'
    return f'{valor:,.2f}'.rstrip('0').rstrip('.') if valor else '0'


def escala_saldos(valores):
    valores = [float(v) for v in valores]
    minimo, maximo = min(valores), max(valores)
    rango = maximo - minimo
    if rango == 0:
        rango = max(abs(minimo) * .1, 1)
        minimo -= rango / 2
        maximo += rango / 2
    # Incluir cero solo cuando no aplasta una variación distante de la recuperación.
    if minimo > 0 and minimo <= rango * 2:
        minimo = 0
    if maximo < 0 and -maximo <= rango * 2:
        maximo = 0
    rango = maximo - minimo
    bruto = rango / 5
    magnitud = 10 ** math.floor(math.log10(bruto))
    paso = next(m * magnitud for m in (1, 2, 2.5, 5, 10) if m * magnitud >= bruto)
    inferior = math.floor((minimo - rango * .06) / paso) * paso
    superior = math.ceil((maximo + rango * .06) / paso) * paso
    cantidad = round((superior - inferior) / paso)
    return inferior, superior, [inferior + i * paso for i in range(cantidad + 1)]
