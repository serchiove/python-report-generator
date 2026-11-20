"""Panel comercial de utilidad bruta y simulación con volumen constante."""
import tkinter as tk
from tkinter import ttk, messagebox

from src.rentabilidad import simular_descuento


def mostrar_rentabilidad(padre, datos, exportar):
    ventana = tk.Toplevel(padre)
    ventana.title('Rentabilidad | Decisiones comerciales')
    ventana.geometry('1060x740')
    ventana.minsize(850, 650)
    marco = ttk.Frame(ventana, padding=20)
    marco.pack(fill='both', expand=True)
    ttk.Label(marco, text='¿Qué ventas generan más utilidad?', font=('Segoe UI', 20, 'bold')).pack(anchor='w')
    ttk.Label(marco, text='Utilidad bruta: ingresos menos costo de productos. No incluye alquiler, sueldos ni otros gastos.', wraplength=900).pack(anchor='w', pady=(6, 8))
    ttk.Label(marco, text=f"Cobertura: {datos['conocidas']} registros con costo / {datos['desconocidas']} sin costo (excluidos).", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
    tarjetas = ttk.Frame(marco)
    tarjetas.pack(fill='x', pady=12)
    margen = f"{datos['margen']:.2f}%" if datos['margen'] is not None else 'No calculable'
    for i, (titulo, valor) in enumerate([
        ('Ingresos analizados', f"${datos['ingresos']:,.2f}"), ('Costo vendido', f"${datos['costos']:,.2f}"),
        ('Utilidad bruta', f"${datos['utilidad']:,.2f}" if datos['conocidas'] else 'Sin costos'), ('Margen bruto', margen),
    ]):
        tarjeta = ttk.LabelFrame(tarjetas, text=titulo, padding=12)
        tarjeta.grid(row=0, column=i, sticky='nsew', padx=4)
        tarjetas.columnconfigure(i, weight=1)
        ttk.Label(tarjeta, text=valor, font=('Segoe UI', 16, 'bold')).pack(anchor='w')
    notas = ('Importa un CSV con costo_unitario para calcular rentabilidad.' if not datos['conocidas']
             else 'Revisa productos en pérdida o con margen bajo. El umbral orientativo es 20%; depende del negocio.')
    ttk.Label(marco, text=notas, wraplength=950).pack(anchor='w', pady=(0, 8))
    tabs = ttk.Notebook(marco)
    tabs.pack(fill='both', expand=True)
    for titulo, clave in [('Productos', 'productos'), ('Categorías', 'categorias')]:
        frame = ttk.Frame(tabs)
        tabs.add(frame, text=titulo)
        tabla = ttk.Treeview(frame, columns=('nombre', 'ingresos', 'costos', 'utilidad', 'margen', 'alerta'), show='headings')
        for col, label, ancho in [('nombre', titulo, 235), ('ingresos', 'Ingresos', 115), ('costos', 'Costo vendido', 115),
                                  ('utilidad', 'Utilidad bruta', 115), ('margen', 'Margen', 90), ('alerta', 'Revisión sugerida', 160)]:
            tabla.heading(col, text=label)
            tabla.column(col, width=ancho, minwidth=60, anchor='w' if col in ('nombre', 'alerta') else 'e')
        barra = ttk.Scrollbar(frame, orient='vertical', command=tabla.yview)
        tabla.configure(yscrollcommand=barra.set)
        barra.pack(side='right', fill='y')
        tabla.pack(fill='both', expand=True)
        tabla.tag_configure('perdida', foreground='#b91c1c')
        tabla.tag_configure('bajo', foreground='#92400e')
        for item in datos[clave]:
            tag = 'perdida' if item['utilidad'] < 0 else ('bajo' if item['margen'] is not None and item['margen'] < 20 else '')
            texto = 'Pérdida bruta' if tag == 'perdida' else ('Margen bajo (<20%)' if tag else '')
            tabla.insert('', 'end', values=(item['nombre'], f"${item['ingresos']:,.2f}", f"${item['costos']:,.2f}",
                         f"${item['utilidad']:,.2f}", f"{item['margen']:.2f}%" if item['margen'] is not None else 'No calculable', texto), tags=(tag,))
    simulador = ttk.LabelFrame(marco, text='Simular descuento sobre todas las ventas con costo conocido', padding=12)
    simulador.pack(fill='x', pady=(12, 0))
    controles = ttk.Frame(simulador)
    controles.pack(fill='x')
    ttk.Label(controles, text='Descuento (%)').pack(side='left')
    entrada = ttk.Entry(controles, width=10)
    entrada.insert(0, '10')
    entrada.pack(side='left', padx=8)
    resultado = tk.StringVar(value='Se mantiene el volumen vendido y el costo. Esta simulación no modifica ventas ni predice demanda.')
    def simular():
        if not datos['conocidas']:
            messagebox.showinfo('Sin costos', 'Primero importa ventas con costo_unitario.', parent=ventana)
            return
        try:
            r = simular_descuento(datos['ingresos'], datos['costos'], entrada.get())
        except ValueError as error:
            messagebox.showerror('Descuento inválido', str(error), parent=ventana)
            return
        m = f"{r['margen']:.2f}%" if r['margen'] is not None else 'No calculable'
        aviso = ' | PÉRDIDA BRUTA' if r['utilidad'] < 0 else ''
        resultado.set(f"Ingresos: ${r['ingresos']:,.2f} | Utilidad bruta: ${r['utilidad']:,.2f} | Margen: {m}{aviso}\nVolumen y costo constantes; no modifica ventas ni predice demanda.")
    ttk.Button(controles, text='Calcular escenario', command=simular).pack(side='left')
    ttk.Button(controles, text='Exportar reporte completo a PDF', command=exportar).pack(side='right')
    ttk.Label(simulador, textvariable=resultado, wraplength=900).pack(anchor='w', pady=(8, 0))
    return ventana
