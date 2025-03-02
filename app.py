import tkinter as tk
from tkinter import ttk, messagebox
import json
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import date

class SistemaPesadas(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Control de Producción")
        self.geometry("1200x800")
        
        # Datos iniciales
        self.targets = self.cargar_objetivos()
        self.registros = []
        self.figura = Figure(figsize=(6, 4), dpi=100)
        self.configurar_ui()
        
    def cargar_objetivos(self):
        try:
            with open('pesadas.json') as f:
                data = json.load(f)
                return {str(item['SKU']): item['TARGET_HORA'] for item in data}
        except:
            return {
                '801327': 85, '801605': 120, '36147': 60,
                '801345': 55, '800890': 20, '34567': 12
            }
    
    def configurar_ui(self):
        # Contenedor principal
        contenedor = ttk.Frame(self)
        contenedor.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Cabecera
        header = ttk.Label(contenedor, text="🏭 Sistema de Control de Producción", 
                          font=('Helvetica', 16, 'bold'))
        header.pack(pady=10)
        
        # Formulario inicial
        form_frame = ttk.Frame(contenedor)
        form_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(form_frame, text="Operario:").grid(row=0, column=0, padx=5)
        self.operario = ttk.Entry(form_frame, width=20)
        self.operario.grid(row=0, column=1, padx=5)
        
        ttk.Label(form_frame, text="Fecha:").grid(row=0, column=2, padx=5)
        self.fecha = ttk.Entry(form_frame, width=15)
        self.fecha.insert(0, date.today().isoformat())
        self.fecha.grid(row=0, column=3, padx=5)
        
        ttk.Label(form_frame, text="Turno:").grid(row=0, column=4, padx=5)
        self.turno = ttk.Combobox(form_frame, values=["Mañana", "Tarde", "Noche"], width=10)
        self.turno.current(0)
        self.turno.grid(row=0, column=5, padx=5)
        
        # Cabecera de registros
        registros_header = ttk.Frame(contenedor)
        registros_header.pack(fill=tk.X, pady=10)
        headers = ["SKU", "Pesadas", "Tiempo (min)", "Target/h", "Rendimiento", "Acciones"]
        for i, h in enumerate(headers):
            ttk.Label(registros_header, text=h, width=15).grid(row=0, column=i, padx=2)
        
        # Area de registros
        self.registros_frame = ttk.Frame(contenedor)
        self.registros_frame.pack(fill=tk.X)
        
        # Botones
        btn_frame = ttk.Frame(contenedor)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="➕ Nuevo Registro", 
                  command=self.agregar_registro).pack(side=tk.LEFT)
        
        # Resumen
        self.resumen = ttk.Label(contenedor, text="Rendimiento Promedio: 0.0%",
                                font=('Helvetica', 12, 'bold'))
        self.resumen.pack(pady=10)
        
        # Gráfico
        self.configurar_grafico(contenedor)
        self.agregar_registro()
        
    def configurar_grafico(self, parent):
        self.ax = self.figura.add_subplot(111)
        self.ax.pie([0, 100], labels=['Alcanzado', 'Restante'], 
                   colors=['#27ae60', '#e0e0e0'], autopct='%1.1f%%')
        self.canvas = FigureCanvasTkAgg(self.figura, master=parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def agregar_registro(self):
        frame = ttk.Frame(self.registros_frame)
        frame.pack(fill=tk.X, pady=2)
        
        sku = ttk.Combobox(frame, values=list(self.targets.keys()), width=15)
        sku.grid(row=0, column=0, padx=2)
        
        pesadas = ttk.Entry(frame, width=10)
        pesadas.grid(row=0, column=1, padx=2)
        pesadas.bind('<KeyRelease>', self.actualizar_calculos)
        
        tiempo = ttk.Entry(frame, width=10)
        tiempo.insert(0, "15")
        tiempo.grid(row=0, column=2, padx=2)
        tiempo.bind('<KeyRelease>', self.actualizar_calculos)
        
        target = ttk.Label(frame, text="0", width=10)
        target.grid(row=0, column=3, padx=2)
        
        rendimiento = ttk.Label(frame, text="0%", width=10)
        rendimiento.grid(row=0, column=4, padx=2)
        
        btn_eliminar = ttk.Button(frame, text="🗑", width=3,
                                 command=lambda: frame.destroy())
        btn_eliminar.grid(row=0, column=5, padx=2)
        
        sku.bind('<<ComboboxSelected>>', lambda e: self.actualizar_target(e, target))
        self.registros.append((sku, pesadas, tiempo, target, rendimiento))
        
    def actualizar_target(self, event, target_label):
        sku = event.widget.get()
        target_label.config(text=str(self.targets.get(sku, 0)))
        self.actualizar_calculos()
        
    def calcular_rendimiento(self, pesadas, tiempo, target):
        try:
            pesadas = float(pesadas)
            tiempo = float(tiempo)
            target = float(target)
            if tiempo <= 0 or target <= 0:
                return 0
            horas = tiempo / 60
            rendimiento = (pesadas / (target * horas)) * 100
            return min(rendimiento, 100)
        except:
            return 0
        
    def actualizar_calculos(self, event=None):
        total = 0
        contador = 0
        
        for registro in self.registros:
            sku, pesadas, tiempo, target, rendimiento = registro
            target_val = target.cget("text")
            
            if sku.get() and target_val.isdigit():
                calc = self.calcular_rendimiento(
                    pesadas.get(), tiempo.get(), target_val
                )
                rendimiento.config(text=f"{calc:.1f}%")
                total += calc
                contador += 1
                
        promedio = total / contador if contador > 0 else 0
        self.resumen.config(text=f"Rendimiento Promedio: {promedio:.1f}%")
        self.actualizar_grafico(promedio)
        
    def actualizar_grafico(self, promedio):
        self.ax.clear()
        self.ax.pie([promedio, 100 - promedio], 
                   labels=['Alcanzado', 'Restante'],
                   colors=['#27ae60', '#e0e0e0'], 
                   autopct='%1.1f%%')
        self.canvas.draw()

if __name__ == "__main__":
    app = SistemaPesadas()
    app.mainloop()