"""Gráfico accesible de facturación agrupada por categoría."""

from decimal import Decimal
import tkinter as tk
from tkinter import ttk


COLOR = {
    "fondo": "#f3f6fb",
    "blanco": "#ffffff",
    "tinta": "#172b4d",
    "muted": "#64748b",
    "linea": "#e2e8f0",
    "azul": "#3973d6",
    "azul_suave": "#eaf1fd",
    "verde": "#0f766e",
    "verde_suave": "#e8f5f2",
}


def preparar_datos_grafico(resumen):
    """Normaliza el resumen para mostrar y probar el gráfico sin Tkinter."""
    grupos = [
        (str(nombre), Decimal(str(total)))
        for nombre, total in resumen.get("por_categoria", [])
    ]
    grupos.sort(key=lambda par: (-par[1], par[0].casefold()))
    total = sum((importe for _, importe in grupos), Decimal("0"))
    maximo = max((importe for _, importe in grupos), default=Decimal("0"))
    items = [
        {
            "nombre": nombre,
            "importe": importe,
            "porcentaje": (importe / total * Decimal("100")) if total else Decimal("0"),
        }
        for nombre, importe in grupos
    ]
    lider = items[0] if items else None
    return {
        "items": items,
        "total": total,
        "maximo": maximo,
        "cantidad": len(items),
        "lider": lider["nombre"] if lider else "Sin datos",
        "participacion_lider": lider["porcentaje"] if lider else Decimal("0"),
    }


def mostrar_grafico(padre, resumen):
    """Abre una vista de análisis con indicadores, escala y ranking legible."""
    datos = preparar_datos_grafico(resumen)
    ventana = tk.Toplevel(padre)
    ventana.title("Análisis de ventas | Facturación por categoría")
    ventana.geometry("1120x760")
    ventana.minsize(900, 620)
    ventana.configure(bg=COLOR["fondo"])
    ventana.transient(padre)

    estilos = ttk.Style(ventana)
    estilos.configure("Grafico.TFrame", background=COLOR["fondo"])
    estilos.configure("Grafico.TLabel", background=COLOR["fondo"], foreground=COLOR["tinta"], font=("Segoe UI", 10))

    principal = ttk.Frame(ventana, padding=(28, 24), style="Grafico.TFrame")
    principal.pack(fill="both", expand=True)
    ttk.Label(principal, text="Facturación por categoría", font=("Segoe UI", 22, "bold"), style="Grafico.TLabel").pack(anchor="w")
    ttk.Label(
        principal,
        text="Comparación del resumen generado más recientemente. Las categorías se ordenan por importe.",
        foreground=COLOR["muted"], style="Grafico.TLabel",
    ).pack(anchor="w", pady=(5, 18))

    tarjetas = ttk.Frame(principal, style="Grafico.TFrame")
    tarjetas.pack(fill="x", pady=(0, 18))
    lider = datos["lider"]
    if len(lider) > 24:
        lider = f"{lider[:22]}…"
    indicadores = [
        ("TOTAL FACTURADO", f"${datos['total']:,.2f}", COLOR["azul"]),
        ("CATEGORÍAS", str(datos["cantidad"]), COLOR["tinta"]),
        ("LÍDER DE VENTAS", lider, COLOR["verde"]),
        ("PARTICIPACIÓN DEL LÍDER", f"{datos['participacion_lider']:.2f}%", COLOR["tinta"]),
    ]
    for columna, (titulo, valor, acento) in enumerate(indicadores):
        tarjetas.columnconfigure(columna, weight=1, uniform="indicador")
        tarjeta = tk.Frame(tarjetas, bg=COLOR["blanco"], padx=18, pady=15, highlightthickness=1,
                           highlightbackground=COLOR["linea"])
        tarjeta.grid(row=0, column=columna, sticky="nsew", padx=(0 if columna == 0 else 8, 0))
        tk.Label(tarjeta, text=titulo, bg=COLOR["blanco"], fg=COLOR["muted"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(tarjeta, text=valor, bg=COLOR["blanco"], fg=acento,
                 font=("Segoe UI", 16, "bold"), wraplength=220, justify="left").pack(anchor="w", pady=(7, 0))

    encabezado = ttk.Frame(principal, style="Grafico.TFrame")
    encabezado.pack(fill="x", pady=(0, 8))
    ttk.Label(encabezado, text="Ranking", font=("Segoe UI", 12, "bold"), style="Grafico.TLabel").pack(side="left")
    ttk.Label(encabezado, text="Importe y participación del total", foreground=COLOR["muted"],
              style="Grafico.TLabel").pack(side="right")

    contenedor = tk.Frame(principal, bg=COLOR["blanco"], highlightthickness=1,
                          highlightbackground=COLOR["linea"])
    contenedor.pack(fill="both", expand=True)
    canvas = tk.Canvas(contenedor, bg=COLOR["blanco"], highlightthickness=0, borderwidth=0)
    barra = ttk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=barra.set)
    barra.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    def dibujar(event=None):
        canvas.delete("all")
        ancho = max(canvas.winfo_width(), 780)
        alto_fila = 58
        alto = max(150, 54 + alto_fila * len(datos["items"]) + 18)
        canvas.configure(scrollregion=(0, 0, ancho, alto))

        left = max(190, min(260, int(ancho * 0.26)))
        right = 190
        inicio = left + 12
        fin = max(inicio + 90, ancho - right)
        importe_x = ancho - 112
        porcentaje_x = ancho - 20

        canvas.create_rectangle(0, 0, ancho, 46, fill="#f8fafc", outline="")
        canvas.create_text(20, 23, text="CATEGORÍA", anchor="w", fill=COLOR["muted"],
                           font=("Segoe UI", 9, "bold"))
        canvas.create_text(inicio, 23, text="FACTURACIÓN", anchor="w", fill=COLOR["muted"],
                           font=("Segoe UI", 9, "bold"))
        canvas.create_text(importe_x, 23, text="IMPORTE", anchor="e", fill=COLOR["muted"],
                           font=("Segoe UI", 9, "bold"))
        canvas.create_text(porcentaje_x, 23, text="DEL TOTAL", anchor="e", fill=COLOR["muted"],
                           font=("Segoe UI", 9, "bold"))

        if not datos["items"]:
            canvas.create_text(ancho / 2, 110, text="Todavía no hay ventas para comparar.",
                               fill=COLOR["muted"], font=("Segoe UI", 12))
            return

        maximo = datos["maximo"]
        for marca in range(5):
            fraccion = marca / 4
            x = inicio + (fin - inicio) * fraccion
            canvas.create_line(x, 50, x, alto - 8, fill=COLOR["linea"], dash=(2, 4))
            canvas.create_text(x, 51, text=f"{fraccion * 100:.0f}%", anchor="n",
                               fill=COLOR["muted"], font=("Segoe UI", 8))

        for indice, item in enumerate(datos["items"]):
            arriba = 72 + indice * alto_fila
            centro = arriba + 24
            if indice % 2:
                canvas.create_rectangle(0, arriba - 10, ancho, arriba + 46, fill="#fbfcfe", outline="")
            canvas.create_text(20, centro, text=f"{indice + 1:02d}  {item['nombre']}", anchor="w",
                               width=left - 36, fill=COLOR["tinta"],
                               font=("Segoe UI", 10, "bold" if indice == 0 else "normal"))
            canvas.create_rectangle(inicio, centro - 8, fin, centro + 8,
                                    fill="#edf1f7", outline="")
            proporcion = float(item["importe"] / maximo) if maximo > 0 else 0
            if proporcion > 0:
                canvas.create_rectangle(inicio, centro - 8, inicio + (fin - inicio) * proporcion,
                                        centro + 8, fill=COLOR["verde"] if indice == 0 else COLOR["azul"],
                                        outline="")
            canvas.create_text(importe_x, centro, text=f"${item['importe']:,.2f}", anchor="e",
                               fill=COLOR["tinta"], font=("Segoe UI", 10, "bold"))
            canvas.create_text(porcentaje_x, centro, text=f"{item['porcentaje']:.2f}%", anchor="e",
                               fill=COLOR["muted"], font=("Segoe UI", 9))

    canvas.bind("<Configure>", dibujar)
    canvas.bind("<MouseWheel>", lambda evento: canvas.yview_scroll(-int(evento.delta / 120), "units"))
    ventana.after_idle(dibujar)
    return ventana
