"""Proyección editable de inversión, caja mensual y sensibilidades."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.proyeccion import proyectar_inversion, texto_recuperacion, exportar_proyeccion, explicar_resultado
from src.grafico_inversion import escala_saldos, formato_eje


def mostrar_proyeccion(padre):
    ventana = tk.Toplevel(padre)
    ventana.title('Inversión | ¿Cuándo recupero mi dinero?')
    ventana.geometry('1120x850')
    ventana.minsize(920, 760)
    principal = ttk.Frame(ventana, padding=18)
    principal.pack(fill='both', expand=True)
    ttk.Label(principal, text='Recuperación de la inversión', font=('Segoe UI', 21, 'bold')).pack(anchor='w')
    ttk.Label(principal, text='Escenario hipotético editable. Usa importes de una misma moneda; no es una promesa de ganancias.', wraplength=950).pack(anchor='w', pady=(5,8))
    alcance = tk.StringVar(value='Inversión en software')
    selector = ttk.Combobox(principal, textvariable=alcance, state='readonly', values=['Inversión en software', 'Inversión en negocio'])
    selector.pack(anchor='w')
    ayuda = ttk.Label(principal, wraplength=980)
    ayuda.pack(anchor='w', pady=6)
    campos = ttk.LabelFrame(principal, text='Supuestos mensuales de caja (100k = 100000; 1.5k = 1500)', padding=10)
    campos.pack(fill='x')
    variables = {}
    etiquetas = [('inversion', 'Inversión inicial'), ('cobros', 'Cobros esperados / mes'),
                 ('costo_productos', 'Pagos de productos / mes'), ('gastos', 'Otros pagos / mes'),
                 ('ahorros', 'Ahorros atribuibles / mes'), ('meses', 'Horizonte (1-120 meses)')]
    for i, (clave, etiqueta) in enumerate(etiquetas):
        fila, col = divmod(i, 3)
        contenedor = ttk.Frame(campos)
        contenedor.grid(row=fila, column=col, sticky='ew', padx=8, pady=4)
        campos.columnconfigure(col, weight=1)
        ttk.Label(contenedor, text=etiqueta).pack(anchor='w')
        variables[clave] = tk.StringVar()
        ttk.Entry(contenedor, textvariable=variables[clave]).pack(fill='x')
    acciones = ttk.Frame(principal)
    acciones.pack(fill='x', pady=8)
    estado = tk.StringVar()
    resultados = tk.StringVar()
    ttk.Label(principal, textvariable=estado, foreground='#92400e').pack(anchor='w')
    ttk.Label(principal, textvariable=resultados, wraplength=1000, font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=6)
    tabs = ttk.Notebook(principal)
    tabs.pack(fill='both', expand=True)
    grafico = tk.Canvas(tabs, bg='white', highlightthickness=0)
    barras = tk.Canvas(tabs, bg='white', highlightthickness=0)
    detalle = ttk.Frame(tabs)
    explicacion = ttk.Frame(tabs)
    tabs.add(explicacion, text='¿Cuánto dinero me queda?')
    texto_empresario = tk.Text(explicacion, wrap='word', font=('Segoe UI', 12), padx=20, pady=15,
                               bg='white', fg='#17345c', relief='flat', state='disabled')
    barra_explicacion = ttk.Scrollbar(explicacion, orient='vertical', command=texto_empresario.yview)
    texto_empresario.configure(yscrollcommand=barra_explicacion.set)
    barra_explicacion.pack(side='right', fill='y')
    texto_empresario.pack(fill='both', expand=True)
    tabs.add(grafico, text='Recuperación acumulada')
    tabs.add(barras, text='Entradas y pagos mensuales')
    tabs.add(detalle, text='Detalle por mes')
    tabla = ttk.Treeview(detalle, columns=('mes', 'conservador', 'base', 'optimista'), show='headings')
    for clave, titulo in [('mes', 'Mes'), ('conservador', 'Conservador'), ('base', 'Base'), ('optimista', 'Optimista')]:
        tabla.heading(clave, text=titulo)
        tabla.column(clave, width=90 if clave == 'mes' else 220, anchor='e')
    scroll = ttk.Scrollbar(detalle, orient='vertical', command=tabla.yview)
    tabla.configure(yscrollcommand=scroll.set)
    scroll.pack(side='right', fill='y')
    tabla.pack(fill='both', expand=True)
    ttk.Label(principal, text='Mes 0: salida de la inversión. Saldo cero: capital recuperado. Saldo positivo: excedente acumulado de caja.\n'
              'Escenarios: cobros y ahorros -20% / base / +20%, con pagos constantes. Sin inflación, financiación ni descuento financiero.',
              wraplength=1000).pack(anchor='w', pady=(8,0))
    actual = {'datos': None, 'alcance': None}
    colores = ['#b45309', '#2563eb', '#15803d']

    def dibujar(event=None):
        datos = actual['datos']
        if datos is None:
            return
        grafico.delete('all')
        ancho, alto = max(grafico.winfo_width(), 800), max(grafico.winfo_height(), 220)
        izquierda, derecha, arriba, abajo = 100, ancho-35, 96, alto-55
        valores = [float(v) for e in datos['escenarios'] for v in e['saldos']]
        minimo, maximo, marcas = escala_saldos(valores)
        rango = maximo-minimo
        def x(mes): return izquierda+(derecha-izquierda)*mes/datos['meses']
        def y(valor): return abajo-(float(valor)-minimo)/rango*(abajo-arriba)
        grafico.create_text(20,18,text='Dinero acumulado después de descontar la inversión',anchor='w',fill='#17345c',font=('Segoe UI',11,'bold'))
        cero_visible = minimo <= 0 <= maximo
        if cero_visible:
            grafico.create_rectangle(izquierda,arriba,derecha,y(0),fill='#f0fdf4',outline='')
            grafico.create_rectangle(izquierda,y(0),derecha,abajo,fill='#fff7f7',outline='')
        else:
            grafico.create_rectangle(izquierda,arriba,derecha,abajo,fill='#f8fafc',outline='')
        for valor in marcas:
            grafico.create_line(izquierda,y(valor),derecha,y(valor),fill='#e2e8f0')
            grafico.create_text(izquierda-10,y(valor),text=formato_eje(valor),anchor='e',fill='#475569',font=('Segoe UI',9))
        if cero_visible:
            grafico.create_line(izquierda,y(0),derecha,y(0),fill='#64748b',width=2,dash=(5,3))
            grafico.create_text(derecha-5,y(0)-10,text='0 = inversión recuperada',anchor='e',fill='#475569',font=('Segoe UI',9))
        nota = ('Zona roja: falta recuperar | Zona verde: excedente acumulado' if cero_visible else
                'Escala ampliada de la variación: el saldo 0 está fuera de vista; aún no se recupera la inversión.' if maximo < 0 else
                'Escala ampliada: todos los saldos mostrados son positivos.')
        grafico.create_text(20,40,text=nota,anchor='w',fill='#64748b',font=('Segoe UI',9),width=ancho-40)
        paso = max(1,(datos['meses']+7)//8)
        for mes in sorted(set(range(0,datos['meses']+1,paso)) | {datos['meses']}):
            grafico.create_text(x(mes),abajo+18,text=f'Mes {mes}',font=('Segoe UI',9))
        for i,e in enumerate(datos['escenarios']):
            puntos = [c for n,v in enumerate(e['saldos']) for c in (x(n), y(v))]
            grafico.create_line(*puntos,fill=colores[i],width=3 if i==1 else 2,dash=() if i==1 else (6,3))
            grafico.create_text(izquierda+i*(derecha-izquierda)/3,70,
                                text=f"{e['nombre']} · final {e['saldos'][-1]:,.2f}",
                                fill=colores[i],anchor='w',font=('Segoe UI',9,'bold'))
        base = datos['escenarios'][1]
        mes = base['recuperacion']
        if mes is not None and mes <= datos['meses']:
            grafico.create_line(x(mes),arriba,x(mes),abajo,fill='#93c5fd',dash=(3,4))
            grafico.create_oval(x(mes)-4,y(base['saldos'][mes])-4,x(mes)+4,y(base['saldos'][mes])+4,fill='#2563eb',outline='white')
            grafico.create_text(x(mes),abajo+36,text=f'Recuperación base: mes {mes}',fill='#1d4ed8',font=('Segoe UI',9,'bold'),anchor='e' if mes > datos['meses']*.7 else 'w')
        def detalle_mes(event):
            grafico.delete('detalle_mes')
            if not izquierda <= event.x <= derecha or not arriba <= event.y <= abajo:
                return
            n = round((event.x-izquierda)/(derecha-izquierda)*datos['meses'])
            grafico.create_line(x(n),arriba,x(n),abajo,fill='#94a3b8',tags='detalle_mes')
            etiqueta = f'Mes {n} | ' + ' | '.join(f"{e['nombre']}: {e['saldos'][n]:,.2f}" for e in datos['escenarios'])
            grafico.create_rectangle(izquierda,arriba-4,derecha,arriba+22,fill='#17345c',outline='',tags='detalle_mes')
            grafico.create_text(izquierda+8,arriba+9,text=etiqueta,anchor='w',fill='white',font=('Segoe UI',9),tags='detalle_mes')
        grafico.bind('<Motion>',detalle_mes)
        grafico.bind('<Leave>',lambda e:grafico.delete('detalle_mes'))
        barras.delete('all')
        w,h = max(barras.winfo_width(),800),max(barras.winfo_height(),220)
        montos = [('Cobros', datos['cobros'], '#2563eb'), ('Ahorros', datos['ahorros'], '#0891b2'),
                  ('Pagos productos', datos['costo_productos'], '#b45309'), ('Otros pagos', datos['gastos'], '#b91c1c')]
        maximo = max(float(v) for _,v,_ in montos) or 1
        for i,(nombre,valor,color) in enumerate(montos):
            centro = 90+(w-160)*(i+.5)/4
            y_top = h-55-float(valor)/maximo*(h-110)
            barras.create_rectangle(centro-45,y_top,centro+45,h-55,fill=color,outline='')
            barras.create_text(centro,y_top-15,text=f'{valor:,.2f}',font=('Segoe UI',10,'bold'))
            barras.create_text(centro,h-32,text=nombre,font=('Segoe UI',10))
        barras.create_text(20,16,anchor='w',text='Supuestos del escenario base por mes (misma moneda)',font=('Segoe UI',10,'bold'))

    def modificado(*args):
        estado.set('Supuestos modificados: pulsa Calcular para actualizar gráficos y resultados.')
        exportar_boton.configure(state='disabled')

    def calcular():
        try:
            datos = proyectar_inversion(**{k:v.get() for k,v in variables.items()})
        except ValueError as error:
            messagebox.showerror('Revisar supuestos',str(error),parent=ventana)
            return
        actual.update(datos=datos, alcance=alcance.get())
        texto_empresario.configure(state='normal')
        texto_empresario.delete('1.0', 'end')
        texto_empresario.insert('1.0', '\n\n'.join(explicar_resultado(datos)))
        texto_empresario.configure(state='disabled')
        base = datos['escenarios'][1]
        excedente = (f"mes {base['excedente']}" if base['excedente'] is not None else 'no previsto con este flujo')
        resultados.set(f"Flujo neto mensual base: {base['flujo']:,.2f} | Recuperación: {texto_recuperacion(base,datos['meses'])}\n"
                       f"Primer excedente acumulado positivo: {excedente} | Saldo al mes {datos['meses']}: {base['saldos'][-1]:,.2f}")
        estado.set('Proyección calculada con los supuestos ingresados; no es una predicción garantizada.')
        tabla.delete(*tabla.get_children())
        for n in range(datos['meses']+1):
            tabla.insert('', 'end', values=[n]+[f"{e['saldos'][n]:,.2f}" for e in datos['escenarios']])
        exportar_boton.configure(state='normal')
        dibujar()

    def exportar():
        ruta = filedialog.asksaveasfilename(parent=ventana,defaultextension='.pdf',initialfile='proyeccion_inversion.pdf',filetypes=[('PDF','*.pdf')])
        if ruta:
            try:
                exportar_proyeccion(actual['datos'],ruta,actual['alcance'])
            except Exception as error:
                messagebox.showerror('No se pudo exportar',str(error),parent=ventana)
            else:
                messagebox.showinfo('PDF generado','Se guardaron los supuestos, el gráfico y la tabla mensual.',parent=ventana)

    def cargar_ejemplo():
        software = alcance.get() == 'Inversión en software'
        valores = ['3000','0','0','50','550','12'] if software else ['10000','6000','3500','1000','0','12']
        for (clave,_), valor in zip(etiquetas,valores):
            variables[clave].set(valor)
        calcular()
        estado.set('EJEMPLO FICTICIO cargado para demostración. Sustituye estos supuestos por datos de la empresa.')

    def cambiar_alcance(event=None):
        ayuda.configure(text=('Software: usa solo cobros adicionales, ahorros y pagos atribuibles a la herramienta; no el total de ventas del negocio.'
                              if alcance.get() == 'Inversión en software' else
                              'Negocio: ingresa cobros y pagos mensuales del proyecto. No sumes un ahorro ya descontado de los pagos.'))
        modificado()

    def cargar_100k():
        alcance.set('Inversión en negocio')
        cambiar_alcance()
        for (clave,_), valor in zip(etiquetas, ['100k','30k','15k','5k','0','12']):
            variables[clave].set(valor)
        calcular()
        estado.set('EJEMPLO FICTICIO de inversión 100,000: sustituye los cobros y pagos por los de tu empresa.')

    ttk.Button(acciones,text='Calcular proyección',command=calcular).pack(side='left',padx=(0,8))
    ttk.Button(acciones,text='Cargar ejemplo ficticio',command=cargar_ejemplo).pack(side='left')
    ttk.Button(acciones,text='Ejemplo de 100k',command=cargar_100k).pack(side='left',padx=8)
    exportar_boton = ttk.Button(acciones,text='Exportar proyección PDF',command=exportar,state='disabled')
    exportar_boton.pack(side='right')
    for variable in variables.values():
        variable.trace_add('write',modificado)
    selector.bind('<<ComboboxSelected>>',cambiar_alcance)
    grafico.bind('<Configure>',dibujar)
    barras.bind('<Configure>',dibujar)
    cambiar_alcance()
    cargar_ejemplo()
    ventana.after_idle(dibujar)
    return ventana
