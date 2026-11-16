"""Menú de escritorio para importar ventas y consultar reportes."""
import os
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import psycopg
from main import ejecutar_flujo
from src.config import ARCHIVO_VENTAS, CARPETA_REPORTES, NOMBRE_REPORTE
from src.database import conectar, inicializar_esquema
from src.generador_pdf import exportar_pdf
from src.grafico_categorias import mostrar_grafico


class Aplicacion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Reportes de ventas | Panel de control")
        self.geometry("1000x780")
        self.minsize(820, 650)
        self.configure(bg="#eef2f7")
        self.resultados = queue.Queue()
        self.botones = []
        self.ocupado = False
        self.ruta_actual = None
        self.resumen_actual = None
        self.campos = {}
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure("TFrame", background="#eef2f7")
        estilo.configure("TLabel", background="#eef2f7", foreground="#172b4d", font=("Segoe UI", 10))
        estilo.configure("Title.TLabel", font=("Segoe UI", 24, "bold"))
        estilo.configure("TButton", font=("Segoe UI", 10), padding=9)
        estilo.configure("TLabelframe", background="#eef2f7")
        estilo.configure("TLabelframe.Label", font=("Segoe UI", 11, "bold"))
        marco = ttk.Frame(self, padding=22)
        marco.pack(fill="both", expand=True)
        ttk.Label(marco, text="Reportes de ventas", style="Title.TLabel").pack(anchor="w")
        ttk.Label(marco, text="Importa tu CSV, consulta PostgreSQL y comparte el resumen mediante QR.").pack(anchor="w", pady=(4, 16))
        conexion = ttk.LabelFrame(marco, text="1. Conexión a PostgreSQL", padding=12)
        conexion.pack(fill="x")
        valores = [("Servidor", "PGHOST", "localhost"), ("Puerto", "PGPORT", "5432"),
                   ("Base de datos", "PGDATABASE", "reportes_presentacion"),
                   ("Usuario", "PGUSER", "reportes_app"), ("Contraseña", "PGPASSWORD", "")]
        self.entradas = []
        for i, (titulo, clave, defecto) in enumerate(valores):
            ttk.Label(conexion, text=titulo).grid(row=0, column=i, sticky="w", padx=4)
            variable = tk.StringVar(value=os.environ.get(clave, defecto))
            self.campos[clave] = variable
            entrada = ttk.Entry(conexion, textvariable=variable, width=17, show="*" if clave == "PGPASSWORD" else "")
            entrada.grid(row=1, column=i, sticky="ew", padx=4, pady=5)
            conexion.columnconfigure(i, weight=1)
            self.entradas.append(entrada)
        ttk.Label(conexion, text="La contraseña se utiliza en esta sesión y no se guarda en archivos.").grid(row=2, column=0, columnspan=5, sticky="w", pady=(4, 0))
        acciones = ttk.Frame(marco)
        acciones.pack(fill="x", pady=10)
        self.boton(acciones, "Probar conexión", lambda: self.ejecutar("conexion"))
        self.boton(acciones, "Crear tablas", lambda: self.ejecutar("tablas"))
        archivos = ttk.LabelFrame(marco, text="2. Archivos del reporte", padding=12)
        archivos.pack(fill="x")
        self.csv = tk.StringVar(value=str(ARCHIVO_VENTAS))
        self.salida = tk.StringVar(value=str(CARPETA_REPORTES / NOMBRE_REPORTE))
        for fila, (texto, variable, elegir) in enumerate([
            ("CSV de entrada", self.csv, self.elegir_csv),
            ("Guardar TXT en", self.salida, self.elegir_salida),
        ]):
            ttk.Label(archivos, text=texto).grid(row=fila, column=0, sticky="w", padx=4)
            entrada = ttk.Entry(archivos, textvariable=variable)
            entrada.grid(row=fila, column=1, sticky="ew", padx=8, pady=5)
            self.entradas.append(entrada)
            boton = ttk.Button(archivos, text="Elegir…", command=elegir)
            boton.grid(row=fila, column=2)
            self.botones.append(boton)
        archivos.columnconfigure(1, weight=1)
        ttk.Label(archivos, text="El QR se guarda junto al TXT. Si el nombre ya existe, ambos se reemplazan.").grid(row=2, column=0, columnspan=3, sticky="w", pady=5)
        acciones = ttk.Frame(marco)
        acciones.pack(fill="x", pady=12)
        self.boton(acciones, "Importar CSV + TXT y QR", lambda: self.ejecutar("importar"))
        self.boton(acciones, "Solo reporte + QR", lambda: self.ejecutar("reporte"))
        self.boton(acciones, "Abrir TXT", lambda: self.abrir(False))
        self.boton(acciones, "Abrir QR", lambda: self.abrir(True))
        exportacion = ttk.Frame(marco)
        exportacion.pack(fill="x", pady=(0, 10))
        self.boton(exportacion, "Exportar a PDF", self.exportar)
        self.boton(exportacion, "Gráfico por categoría", self.graficar)
        self.estado = tk.StringVar(value="Listo. Prueba la conexión para comenzar.")
        ttk.Label(marco, textvariable=self.estado).pack(anchor="w", pady=(0, 8))
        self.texto = tk.Text(marco, wrap="word", font=("Consolas", 10), bg="white", fg="#172b4d", relief="flat", padx=12, pady=12, state="disabled")
        self.texto.pack(fill="both", expand=True)
        self.mostrar("Aquí aparecerán el resultado de la operación y el contenido del reporte.\nEl QR contiene un resumen de ventas en texto; no es un enlace web.")
        self.after(100, self.recibir)
        self.protocol("WM_DELETE_WINDOW", self.cerrar)

    def boton(self, padre, texto, accion):
        boton = ttk.Button(padre, text=texto, command=accion)
        boton.pack(side="left", padx=(0, 8))
        self.botones.append(boton)

    def elegir_csv(self):
        ruta = filedialog.askopenfilename(filetypes=[("Archivo CSV", "*.csv")])
        if ruta:
            self.csv.set(ruta)

    def elegir_salida(self):
        ruta = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Reporte de texto", "*.txt")])
        if ruta:
            self.salida.set(ruta)

    def mostrar(self, contenido):
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.insert("1.0", contenido)
        self.texto.configure(state="disabled")

    def ejecutar(self, accion):
        if self.ocupado:
            return
        for clave, valor in self.campos.items():
            os.environ[clave] = valor.get() if clave == "PGPASSWORD" else valor.get().strip()
        archivo = Path(self.csv.get()) if accion == "importar" else None
        salida = Path(self.salida.get())
        if accion in ("importar", "reporte"):
            if salida.suffix.lower() != ".txt":
                messagebox.showerror("Destino inválido", "Elige un archivo de salida con extensión .txt.")
                return
            if archivo is not None and not archivo.is_file():
                messagebox.showerror("CSV no encontrado", "Selecciona un archivo CSV existente.")
                return
            if archivo is not None and archivo.resolve() in (salida.resolve(), salida.with_suffix(".png").resolve()):
                messagebox.showerror("Destino inválido", "El reporte debe tener una ruta diferente al CSV.")
                return
            if (salida.exists() or salida.with_suffix(".png").exists()) and not messagebox.askyesno("Reemplazar reporte", "Ya existe el TXT o su imagen QR. ¿Deseas reemplazarlos?"):
                return
        self.ocupado = True
        self.estado.set("Procesando…")
        for control in self.botones + self.entradas:
            control.configure(state="disabled")
        threading.Thread(target=self.trabajar, args=(accion, archivo, salida), daemon=True).start()

    def trabajar(self, accion, archivo, salida):
        try:
            resumen = None
            with conectar() as conexion:
                if accion == "conexion":
                    info = conexion.execute("SELECT current_database() AS base, current_user AS usuario").fetchone()
                    mensaje = f"Conexión correcta: {info['base']} / {info['usuario']}"
                    ruta = None
                elif accion == "tablas":
                    inicializar_esquema(conexion)
                    mensaje, ruta = "Tablas preparadas: categorias, productos y ventas.", None
                else:
                    resultado = ejecutar_flujo(conexion, archivo, salida.parent, salida.name)
                    ruta = resultado["ruta_reporte"]
                    resumen = resultado["resumen"]
                    importacion = resultado["importacion"]
                    if importacion is None:
                        mensaje = "Reporte desde PostgreSQL sin importar CSV.\n"
                    else:
                        mensaje = (f"Ventas válidas: {importacion['ventas_validas']} | "
                                   f"Nuevas: {importacion['ventas_insertadas']} | "
                                   f"Ya existentes: {importacion['ventas_ya_existentes']}\n")
                    mensaje += f"TXT: {ruta}\nQR: {ruta.with_suffix('.png')}\n\n" + ruta.read_text(encoding="utf-8")
            self.resultados.put((True, mensaje, ruta, resumen))
        except Exception as error:
            if isinstance(error, psycopg.OperationalError):
                mensaje = "No se pudo conectar. Revisa servidor, puerto, base, usuario y contraseña."
            elif isinstance(error, psycopg.errors.UndefinedTable):
                mensaje = "Faltan tablas. Pulsa Crear tablas antes de generar el reporte."
            else:
                mensaje = f"No se completó la operación: {error}"
            mensaje += "\nSi la importación ya se confirmó, las ventas permanecen guardadas. Puedes repetir el CSV sin duplicarlo."
            self.resultados.put((False, mensaje, None, None))

    def recibir(self):
        try:
            correcto, mensaje, ruta, resumen = self.resultados.get_nowait()
        except queue.Empty:
            pass
        else:
            self.ocupado = False
            for control in self.botones + self.entradas:
                control.configure(state="normal")
            self.estado.set("Operación completada." if correcto else "Revisa el mensaje de error.")
            self.mostrar(mensaje)
            if ruta is not None:
                self.ruta_actual = ruta
                self.resumen_actual = resumen
        self.after(100, self.recibir)

    def abrir(self, qr):
        if self.ruta_actual is None:
            messagebox.showinfo("Generar primero", "Genera un reporte desde este menú para abrir sus archivos.")
            return
        ruta = self.ruta_actual.with_suffix(".png") if qr else self.ruta_actual
        try:
            os.startfile(str(ruta.resolve()))
        except OSError as error:
            messagebox.showerror("No se pudo abrir", str(error))

    def graficar(self):
        if self.resumen_actual is None:
            messagebox.showinfo("Generar primero", "Genera un reporte desde este menú para mostrar sus categorías.")
            return
        mostrar_grafico(self, self.resumen_actual)

    def exportar(self):
        if self.ruta_actual is None:
            messagebox.showinfo("Generar primero", "Genera un reporte desde este menú antes de exportarlo.")
            return
        destino = filedialog.asksaveasfilename(
            title="Exportar reporte a PDF", defaultextension=".pdf",
            initialdir=str(self.ruta_actual.parent),
            initialfile=self.ruta_actual.with_suffix(".pdf").name,
            filetypes=[("Documento PDF", "*.pdf")],
        )
        if not destino:
            return
        try:
            ruta = exportar_pdf(self.ruta_actual, Path(destino))
        except ImportError:
            messagebox.showerror("Falta ReportLab", "Instala las dependencias: python -m pip install -r requirements.txt")
        except Exception as error:
            messagebox.showerror("No se pudo exportar", str(error))
        else:
            self.estado.set(f"PDF exportado: {ruta}")
            if messagebox.askyesno("PDF generado", "El PDF se guardó correctamente. ¿Deseas abrirlo?"):
                try:
                    os.startfile(str(ruta.resolve()))
                except OSError as error:
                    messagebox.showerror("No se pudo abrir el PDF", str(error))

    def cerrar(self):
        if self.ocupado:
            messagebox.showinfo("Operación en curso", "Espera a que termine antes de cerrar la ventana.")
            return
        os.environ.pop("PGPASSWORD", None)
        self.destroy()


if __name__ == "__main__":
    Aplicacion().mainloop()
