"""Comparación de facturación por categoría en una vista organizada."""
import tkinter as tk
from tkinter import ttk
from decimal import Decimal


def mostrar_grafico(padre, resumen):
    grupos = sorted([(nombre, Decimal(str(total))) for nombre, total in resumen['por_categoria']], key=lambda par: par[1], reverse=True)
    total = sum((importe for _, importe in grupos), Decimal('0'))
    ventana = tk.Toplevel(padre)
    ventana.title('Análisis de ventas | Categorías')
    ventana.geometry('1060x700')
    ventana.minsize(820, 560)
    ventana.configure(bg='#eef2f7')
    principal = ttk.Frame(ventana, padding=20)
    principal.pack(fill='both', expand=True)
    ttk.Label(principal, text='¿Qué categorías generan más ventas?', font=('Segoe UI', 20, 'bold')).pack(anchor='w')
    ttk.Label(principal, text='Comparación de la facturación del último reporte generado.', font=('Segoe UI', 10)).pack(anchor='w', pady=(4, 15))
    tarjetas = ttk.Frame(principal)
    tarjetas.pack(fill='x', pady=(0, 15))
    lider = grupos[0][0] if grupos else 'Sin datos'
    participacion = grupos[0][1] / total * 100 if grupos and total > 0 else Decimal('0')
    datos = [('TOTAL FACTURADO', f'${total:,.2f}'), ('CATEGORÍAS', str(len(grupos))),
             ('MAYOR FACTURACIÓN', lider), ('PARTICIPACIÓN DEL LÍDER', f'{participacion:.2f}%')]
    for indice, (titulo, valor) in enumerate(datos):
        tarjeta = tk.Frame(tarjetas, bg='white', padx=12, pady=12)
        tarjeta.grid(row=0, column=indice, sticky='nsew', padx=(0, 8))
        tarjetas.columnconfigure(indice, weight=1, uniform='tarjeta')
        tk.Label(tarjeta, text=titulo, bg='white', fg='#64748b', font=('Segoe UI', 9)).pack(anchor='w')
        etiqueta = tk.Label(tarjeta, text=valor, bg='white', fg='#172b4d', font=('Segoe UI', 14, 'bold'), wraplength=205, justify='left')
        etiqueta.pack(anchor='w', pady=(6, 0))
        tarjeta.bind('<Configure>', lambda e, label=etiqueta: label.configure(wraplength=max(100,e.width-24)))
    ttk.Label(principal, text='Ranking de categorías · de mayor a menor facturación', font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0, 8))
    marco = ttk.Frame(principal)
    marco.pack(fill='both', expand=True)
    canvas = tk.Canvas(marco, background='white', highlightthickness=0)
    barra = ttk.Scrollbar(marco, orient='vertical', command=canvas.yview)
    canvas.configure(yscrollcommand=barra.set)
    barra.pack(side='right', fill='y')
    canvas.pack(side='left', fill='both', expand=True)
    ttk.Label(principal, text='Azul: facturación por categoría. Verde: categoría líder. % del total = importe de la categoría ÷ total × 100.', wraplength=970).pack(anchor='w', pady=(10, 3))
    ttk.Label(principal, text='Las barras comparten una escala desde cero hasta el importe mayor. $ indica el formato monetario del proyecto.', wraplength=970).pack(anchor='w')

    def dibujar(event=None):
        canvas.delete('all')
        ancho = max(canvas.winfo_width(), 730)
        alto = max(160, 65 + 46 * len(grupos))
        canvas.configure(scrollregion=(0, 0, ancho, alto))
        inicio, fin = 225, ancho - 245
        importe_x, porcentaje_x = ancho - 105, ancho - 18
        canvas.create_rectangle(0, 0, ancho, 43, fill='#172b4d', outline='')
        for x, titulo, ancla in [(15,'Categoría','w'), (inicio,'Facturación comparada','w'), (importe_x,'Importe','e'), (porcentaje_x,'% del total','e')]:
            canvas.create_text(x, 21, text=titulo, anchor=ancla, fill='white', font=('Segoe UI',10,'bold'))
        if not grupos:
            canvas.create_text(ancho/2, 95, text='No hay ventas para graficar.', font=('Segoe UI',13), fill='#64748b')
            return
        maximo = max(importe for _, importe in grupos)
        for indice, (nombre, importe) in enumerate(grupos):
            arriba = 45 + indice * 46
            y = arriba + 23
            canvas.create_rectangle(0,arriba,ancho,arriba+46,fill='white' if indice%2==0 else '#f8fafc',outline='')
            canvas.create_text(15,y,text=f'{indice+1}. {nombre}',width=200,anchor='w',font=('Segoe UI',10,'bold' if indice==0 else 'normal'),fill='#172b4d')
            canvas.create_rectangle(inicio,y-9,fin,y+9,fill='#e2e8f0',outline='')
            longitud = float(importe/maximo)*(fin-inicio) if maximo>0 else 0
            if longitud>0:
                canvas.create_rectangle(inicio,y-9,inicio+longitud,y+9,fill='#0f766e' if indice==0 else '#2563eb',outline='')
            porcentaje = importe/total*100 if total>0 else Decimal('0')
            canvas.create_text(importe_x,y,text=f'${importe:,.2f}',anchor='e',font=('Segoe UI',10),fill='#172b4d')
            canvas.create_text(porcentaje_x,y,text=f'{porcentaje:.2f}%',anchor='e',font=('Segoe UI',10),fill='#172b4d')
    canvas.bind('<Configure>',dibujar)
    canvas.bind('<MouseWheel>',lambda e: canvas.yview_scroll(-int(e.delta/120),'units'))
    ventana.after_idle(dibujar)
    return ventana
