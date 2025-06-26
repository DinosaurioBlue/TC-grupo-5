import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class TC1ScopeApp:
    def __init__(self, root):
        self.cursor_x1 = None
        self.cursor_x2 = None
        self.cursor_y1 = None
        self.cursor_y2 = None
        self.ymin_global = None
        self.ymax_global = None
        self._actualizando_slider = False
        self.offset_divisiones = 0.0
        self.df = None
        self.primera_grafica = True
        self.root = root
        self.canal_offset = tk.IntVar(value=1)
        self.offset_tension_ch1 = 0.0
        self.offset_tension_ch2 = 0.0




        ###pantalla
        self.frame_control = ttk.Frame(root)
        self.frame_control.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)


        ancho_cm = 32
        alto_cm = 12
        ancho_in = ancho_cm / 2.54
        alto_in = alto_cm / 2.54
        self.fig, self.ax = plt.subplots(figsize=(ancho_in, alto_in))
        self.fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.config(width=int(ancho_cm*37.8), height=int(alto_cm*37.8))
        canvas_widget.pack(fill=tk.BOTH, expand=True)


        ###slider_T
        self.frame_control = ttk.Frame(root)
        self.frame_control.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        self.var_offset_tiempo = tk.DoubleVar(value=0.0)
        self.scl_toffset = ttk.Scale(
            master=self.frame_control,
            from_=-10,
            to=15,
            orient='horizontal',
            command=self.on_slider_offset,
            variable=self.var_offset_tiempo
        )
        self.scl_toffset.set(0)
        self.scl_toffset.pack()

        ###slider_V
        self.frame_control = ttk.Frame(root)
        self.frame_control.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        self.offset_tension = 0 
        self.scl_tension_offset = ttk.Scale(
            master=self.frame_control,
            from_=-20,
            to=20,
            orient='horizontal',
            command=self.on_slider_offset_volt,
        )


        self.scl_tension_offset.set(0)
        self.scl_tension_offset.pack()


        self.scl_toffset.pack()

        self.root.title("GUI XD")

        screen_width = self.root.winfo_screenwidth()            ##
        screen_height = self.root.winfo_screenheight()          ##
        width = int(screen_width * 0.9)                         ##
        height = int(screen_height * 0.9)                       ##AJUSTE DE RESOLUCION
        x = (screen_width - width) // 2                         ##
        y = (screen_height - height) // 2                       ##
        self.root.geometry(f"{width}x{height}+{x}+{y}")         ##



        self.frame_control = ttk.Frame(root)
        self.frame_control.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)


        ###ABRIR CSV 
        self.btn_abrir = ttk.Button(self.frame_control, text="Abrir CSV", command=self.abrir_csv)
        self.btn_abrir.pack(side=tk.LEFT)


        ###CURSORES
        self.canal_cursores = tk.IntVar(value=1)
        self.var_cursores = tk.BooleanVar(value=False)
        self.chk_cursores = ttk.Checkbutton(self.frame_control, text="Usar cursores", variable=self.var_cursores, command=self.actualizar_grafica)
        self.chk_cursores.pack(side=tk.LEFT, padx=10)
        self.canal_cursores = tk.IntVar(value=1)
        frame_deltas = tk.Frame(self.frame_control)
        frame_deltas.pack(side=tk.LEFT, padx=10)

        ###selector de canal
        tk.Label(frame_deltas, text="Canal ΔY:").pack(side="left")
        tk.Radiobutton(frame_deltas, text="Canal 1", variable=self.canal_cursores, value=1).pack(side="left")
        tk.Radiobutton(frame_deltas, text="Canal 2", variable=self.canal_cursores, value=2).pack(side="left")

        ###separador
        tk.Label(frame_deltas, text="   ").pack(side="left")  # Espacio entre secciones

        # Selección de canal para offset
        self.canal_offset = tk.IntVar(value=1)
        tk.Label(frame_deltas, text="Canal Offset:").pack(side="left")
        tk.Label(frame_deltas, text="Canal Offset:").pack(side="left")
        tk.Radiobutton(frame_deltas, text="Canal 1", variable=self.canal_offset, value=1,
                    command=self.actualizar_slider_offset).pack(side="left")

        tk.Radiobutton(frame_deltas, text="Canal 2", variable=self.canal_offset, value=2,
                    command=self.actualizar_slider_offset).pack(side="left")


        




        self.label_deltas = ttk.Label(self.frame_control, text="ΔS = 0, ΔV = 0")
        self.label_deltas.pack(side=tk.RIGHT)


        self.frame_timediv = ttk.Frame(root)
        self.frame_timediv.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ttk.Label(self.frame_timediv, text="Tiempo por división: ").pack(side=tk.LEFT) 

        ### ELIJAN EL TIEMPO
        self.tiempos_por_div = [
            ("1 ns/div", 1e-9), ("10 ns/div", 10e-9), ("25 ns/div", 25e-9), ("100 ns/div", 100e-9),
            ("1 μs/div", 1e-6), ("10 μs/div", 10e-6), ("25 μs/div", 25e-6), ("50 μs/div", 50e-6), ("100 μs/div", 100e-6),
            ("1 ms/div", 1e-3), ("10 ms/div", 10e-3), ("25 ms/div", 25e-3), ("50 ms/div", 50e-3), ("100 ms/div", 100e-3),
            ("1 s/div", 1)
        ]

        self.var_tiempo_div = tk.StringVar()
        self.combo_tiempo_div = ttk.Combobox(
            self.frame_timediv, values=[v[0] for v in self.tiempos_por_div],
            state="readonly", width=10, textvariable=self.var_tiempo_div
        )
        self.combo_tiempo_div.current(6)  
        self.combo_tiempo_div.pack(side=tk.LEFT)
        self.combo_tiempo_div.bind("<<ComboboxSelected>>", self.actualizar_grafica)
        self.frm_offset = ttk.Frame(root)
        self.frm_offset.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ###botones 
        self.frm_time = ttk.Frame(self.frm_offset)
        self.frm_time.pack(side=tk.LEFT)
        self.btn_offsetzero_time = tk.Button(
            master=self.frm_time,
            text="Reset offset Time/div",
            command=self.reset_offset
        )
        self.btn_offsetzero_time.pack(side=tk.LEFT, padx=5)

        self.btn_offsetzero_volt = tk.Button(
            master=self.frm_time,
            text="Reset offset Volt/div",
            command=self.reset_offset_volt
        )
        self.btn_offsetzero_volt.pack(side=tk.LEFT, padx=5)


        ###VOLTS/DIVS
        self.frame_voltdiv = ttk.LabelFrame(self.frm_offset, text="Volt por división por canal")
        self.frame_voltdiv.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        ### ELIJAN EL VOLTS/DIVS
        self.voltajes_por_div = [
            ("1 mV/div", 1e-3), ("10 mV/div", 10e-3), ("25 mV/div", 25e-3), ("50 mV/div", 50e-3),
            ("100 mV/div", 100e-3), ("1 V/div", 1), ("2 V/div", 2), ("5 V/div", 5), ("10 V/div", 10)
        ]




        ###listado de VOLT/DIVS
        self.volt_div_vars = []
        self.volt_div_combos = []
        for i, (label, valor) in enumerate(self.voltajes_por_div):
            var = tk.StringVar(value=label)
            combo = ttk.Combobox(self.frame_voltdiv, values=[v[0] for v in self.voltajes_por_div], textvariable=var, state='readonly')
            combo.pack(side=tk.LEFT, padx=5, pady=5)
            self.volt_div_vars.append(var)
            self.volt_div_combos.append(combo)













   
        self.unidad_tiempo = "s"
        self.unidad_valor = "V"
        self.lineas = []
        self.selected_cursor = None

       
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

        self.ymin, self.ymax = self.ax.get_ylim()
        self.ax.set_ylim(self.ymin, self.ymax)
        self.ax.legend()
        self.ax.grid(True)
        self.canvas.draw()






    def inicializar_volt_div(self):
        for combo in self.volt_div_combos:
            combo.destroy()
        self.volt_div_vars, self.volt_div_combos = [], []

        if self.df is None:
            return

        opciones = [v[0] for v in self.voltajes_por_div]
        for _ in range(len(self.df.columns) - 1):
            var = tk.StringVar(value="1 V/div")
            combo = ttk.Combobox(self.frame_voltdiv, values=opciones, state="readonly", width=10, textvariable=var)
            combo.pack(side=tk.LEFT, padx=5, pady=5)
            combo.bind("<<ComboboxSelected>>", self.actualizar_grafica)
            self.volt_div_vars.append(var)
            self.volt_div_combos.append(combo)

    def dibujar_divisiones(self):
        ancho_cm = 32
        alto_cm = 12
        espaciado_cm_x = 3.33
        espaciado_cm_y = 1.5625

        self.canvas.draw()
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()

        rango_x = x_max - x_min
        rango_y = y_max - y_min

        espaciado_x = rango_x * (espaciado_cm_x / ancho_cm)
        espaciado_y = rango_y * (espaciado_cm_y / alto_cm)

        x_centro = (x_max + x_min) / 2
        y_centro = (y_max + y_min) / 2

        x = x_centro
        while x <= x_max:
            self.ax.axvline(x=x, color='gray', linestyle='--', linewidth=0.5, zorder=0)
            x += espaciado_x
        x = x_centro - espaciado_x
        while x >= x_min:
            self.ax.axvline(x=x, color='gray', linestyle='--', linewidth=0.5, zorder=0)
            x -= espaciado_x

        y = y_centro
        while y <= y_max:
            self.ax.axhline(y=y, color='gray', linestyle='--', linewidth=0.5, zorder=0)
            y += espaciado_y
        y = y_centro - espaciado_y
        while y >= y_min:
            self.ax.axhline(y=y, color='gray', linestyle='--', linewidth=0.5, zorder=0)
            y -= espaciado_y

        self.canvas.draw()

    def abrir_csv(self):
        ruta = filedialog.askopenfilename(filetypes=[("Archivos CSV", "*.csv")])
        if not ruta:
            return
        try:
            with open(ruta, 'r', encoding='cp1252') as f:
                primera_linea = f.readline()
            sep = '\t' if '\t' in primera_linea else ','

            df = pd.read_csv(ruta, sep=sep)
            df.columns = [col.strip().replace('"', '') for col in df.columns]

            for c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce')

            df.dropna(inplace=True)

            if df.empty:
                messagebox.showerror("Error", "El archivo CSV está vacío o no tiene datos válidos.")
                return

            self.df = df

            self.inicializar_volt_div()  

            self.actualizar_rango_y_global()

            self.t_min = df.iloc[:, 0].min()
            self.t_max = df.iloc[:, 0].max()

            if df.shape[1] > 1:
                self.ymin = df.iloc[:, 1:].min().min()
                self.ymax = df.iloc[:, 1:].max().max()
            else:
                self.ymin = 0
                self.ymax = 1

            self.ajustar_escala_tiempo() 
            self.actualizar_grafica()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo CSV:\n{e}")


    def actualizar_rango_y_global(self):
        if self.df is None:
            return
        
        ymin_global = float('inf')
        ymax_global = float('-inf')
        
        columnas_datos = self.df.columns[1:] 
        
        for i, col in enumerate(columnas_datos):
            datos = self.df[col].values
            
            factor = 1
            if i < len(self.volt_div_vars):
                volt_div_str = self.volt_div_vars[i].get()
                factor = dict(self.voltajes_por_div).get(volt_div_str, 1)
            
            datos_escalados = datos / factor
            
            ymin_col = np.min(datos_escalados)
            ymax_col = np.max(datos_escalados)
            
            if ymin_col < ymin_global:
                ymin_global = ymin_col
            if ymax_col > ymax_global:
                ymax_global = ymax_col
        
        self.ymin_global = ymin_global
        self.ymax_global = ymax_global

    def update_offset(self, val=None):

        self.actualizar_grafica()

    def reset_offset(self):
        self.scl_toffset.set(0)
        self.actualizar_grafica()

    def on_slider_offset(self, valor_offset):
        if self.df is None:
            return
        try:
            tiempo_div_segs = dict(self.tiempos_por_div)[self.var_tiempo_div.get()]
            t_min = self.df.iloc[:, 0].min()
            t_max = self.df.iloc[:, 0].max()
            duracion_total = t_max - t_min

            rango_visible = tiempo_div_segs * 10

            offset_div = float(valor_offset)

            max_offset = max((duracion_total / tiempo_div_segs) - 5, 0)

            min_offset = 0

            offset_div_limited = min(max(offset_div, min_offset), max_offset)

            self.offset_divisiones = offset_div_limited

            if abs(offset_div - offset_div_limited) > 1e-6:
                self.scl_toffset.set(offset_div_limited)

            self.actualizar_grafica()

        except Exception as e:
            print("Error en on_slider_offset:", e)

    def on_slider_offset_volt(self, valor_offset_entero):
        if self._actualizando_slider:
            print("Retornando porque _actualizando_slider está True")
            return
        self._actualizando_slider = True
        try:
            canal_seleccionado = self.canal_offset.get()
            if self.df is None:
                print("No hay datos cargados (df is None), retorno.")
                return

            y_min = self.ymin_global if self.ymin_global is not None else self.ymin
            y_max = self.ymax_global if self.ymax_global is not None else self.ymax
            rango_tension = y_max - y_min
            if rango_tension == 0:
                rango_tension = 1

            alto_cm = 12
            paso_offset = rango_tension * (0.135564  / alto_cm)
            print(f"paso_offset calculado: {paso_offset}")
            print(f"Rango Y: {rango_tension}, Offset previo canal 1: {self.offset_tension_ch1}, canal 2: {self.offset_tension_ch2}")

            valor_entero = int(round(float(valor_offset_entero)))
            offset_real = valor_entero * paso_offset
            print(f"valor_entero: {valor_entero}, offset_real aplicado: {offset_real}")

            max_offset = rango_tension + 5
            min_offset = -max_offset

            offset_limitado = min(max(offset_real, min_offset), max_offset)

            if canal_seleccionado == 1:
                self.offset_tension_ch1 = offset_limitado
            elif canal_seleccionado == 2:
                self.offset_tension_ch2 = offset_limitado

            self.actualizar_grafica()
        except Exception as e:
            print("Error en on_slider_offset_tension:", e)
        finally:
            self._actualizando_slider = False
            print("Se liberó _actualizando_slider")

    def actualizar_slider_offset(self):
        canal = self.canal_offset.get()
        if canal == 1:
            self.scl_tension_offset.set(self.offset_tension_ch1)
        else:
            self.scl_tension_offset.set(self.offset_tension_ch2)

    def reset_offset_volt(self):
        self.scl_tension_offset.set(0)
        self.offset_tension = 0
        self.actualizar_grafica()

    def ajustar_escala_tiempo(self):
        if self.df is None:
            return

        t_min = self.df.iloc[:, 0].min()
        t_max = self.df.iloc[:, 0].max()
        duracion_total = t_max - t_min

        divisiones_horizontales = 10
        tiempo_por_div_necesario = duracion_total / divisiones_horizontales
        opciones_validas = [(label, val) for (label, val) in self.tiempos_por_div if val <= tiempo_por_div_necesario]

        if opciones_validas:
            escala_seleccionada = max(opciones_validas, key=lambda x: x[1])[0]
        else:
            escala_seleccionada = min(self.tiempos_por_div, key=lambda x: x[1])[0]
        valores_todos = [label for (label, val) in self.tiempos_por_div]
        self.combo_tiempo_div['values'] = valores_todos
        self.var_tiempo_div.set(escala_seleccionada)
        self.combo_tiempo_div.config(state='readonly')

    def ajustar_unidades_tiempo(self, tiempo_s):
        max_abs = np.max(np.abs(tiempo_s))
        if max_abs == 0:
            return tiempo_s, "s"
        if max_abs < 1e-6:
            return tiempo_s * 1e9, "ns"
        elif max_abs < 1e-3:
            return tiempo_s * 1e6, "μs"
        elif max_abs < 1:
            return tiempo_s * 1e3, "ms"
        else:
            return tiempo_s, "s"

    def ajustar_unidades_valor(self, valores):
        max_abs = np.max(np.abs(valores))
        if max_abs == 0:
            return valores, "V"
        if max_abs < 1e-3:
            return valores * 1e6, "μV"
        elif max_abs < 1:
            return valores * 1e3, "mV"
        else:
            return valores, "V"

    def actualizar_grafica(self, event=None):
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        posiciones_relativas = self.obtener_posiciones_relativas()
        if posiciones_relativas is None:
            posiciones_relativas = {}

        if self.cursor_x1:
            x1 = self.cursor_x1.get_xdata()[0]
            posiciones_relativas['x1'] = (x1 - xlim[0]) / (xlim[1] - xlim[0])
        if self.cursor_x2:
            x2 = self.cursor_x2.get_xdata()[0]
            posiciones_relativas['x2'] = (x2 - xlim[0]) / (xlim[1] - xlim[0])
        if self.cursor_y1:
            y1 = self.cursor_y1.get_ydata()[0]
            posiciones_relativas['y1'] = (y1 - ylim[0]) / (ylim[1] - ylim[0])
        if self.cursor_y2:
            y2 = self.cursor_y2.get_ydata()[0]
            posiciones_relativas['y2'] = (y2 - ylim[0]) / (ylim[1] - ylim[0])
    
        self.ax.clear()
        self.lineas.clear()



        if self.df is None:
            self.ax.set_title("Abre un archivo CSV para graficar")
            self.canvas.draw()
            return

        tiempo_col = self.df.columns[0]
        tiempo_original = self.df[tiempo_col].values

        tiempo_div_segs = dict(self.tiempos_por_div).get(self.var_tiempo_div.get(), 1)
        divisiones_totales = 10

        offset_actual = self.offset_divisiones * tiempo_div_segs
        tmin = -5 * tiempo_div_segs + offset_actual
        tmax = 5 * tiempo_div_segs + offset_actual

        idx_visible = np.where((tiempo_original >= tmin) & (tiempo_original <= tmax))[0]

        tiempo_total = tiempo_original[-1] - tiempo_original[0]
        tiempo_por_div_sugerido = tiempo_total / divisiones_totales

        mejor_indice = min(
            range(len(self.tiempos_por_div)),
            key=lambda i: abs(self.tiempos_por_div[i][1] - tiempo_por_div_sugerido)
        )
        if mejor_indice + 1 < len(self.tiempos_por_div):
            etiqueta_escala, mejor_escala = self.tiempos_por_div[mejor_indice + 1]
        else:
            etiqueta_escala, mejor_escala = self.tiempos_por_div[mejor_indice]

        self.ax.set_xlim(tmin, tmax)

        if self.ymin_global is not None and self.ymax_global is not None:
            padding = (self.ymax_global - self.ymin_global) * 0.1
            ymin_ax = self.ymin_global - padding
            ymax_ax = self.ymax_global + padding
        else:
            ymin_ax, ymax_ax = self.ax.get_ylim()
            if abs(ymax_ax - ymin_ax) < 1e-9:
                ymin_ax -= 1
                ymax_ax += 1
            padding = (ymax_ax - ymin_ax) * 0.1
            ymin_ax = ymin_ax - padding
            ymax_ax = ymax_ax + padding


        self.ax.set_ylim(ymin_ax, ymax_ax)

        self.ax.grid(axis='y', visible=False)


        if mejor_escala < tiempo_div_segs:
            self.ax.text(0.95, 0.05, f"Sugerencia: {etiqueta_escala}",
                        transform=self.ax.transAxes, ha='right', va='bottom',
                        fontsize=10, color='red',
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='red'))

        if len(idx_visible) < 2:
            self.ax.text(0.95, 0.05, f"Sugerencia: {etiqueta_escala}",
                        transform=self.ax.transAxes, ha='right', va='bottom',
                        fontsize=10, color='red',
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='red'))
            self.canvas.draw()
            return

        tiempo_ventana = tiempo_original[idx_visible]
        tiempo_ajustado, self.unidad_tiempo = self.ajustar_unidades_tiempo(tiempo_ventana)

        num_canales = len(self.df.columns) - 1
        colores = ['blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'gray']

        for i in range(num_canales):
            datos_originales = self.df[self.df.columns[i + 1]].values[idx_visible]

            volt_div_str = (self.volt_div_vars[i].get() if i < len(self.volt_div_vars) else None)
            factor_volt_div = dict(self.voltajes_por_div).get(volt_div_str, 1)

            datos_ajustados = datos_originales / factor_volt_div

            if i == 0:
                datos_ajustados += self.offset_tension_ch1
            elif i == 1:
                datos_ajustados += self.offset_tension_ch2

            self.unidad_valor = "V"

            linea, = self.ax.plot(
                tiempo_ajustado, datos_ajustados,
                color=colores[i % len(colores)],
                label=f"{self.df.columns[i + 1]} ({volt_div_str if volt_div_str else 'N/A'})"
            )
            self.lineas.append(linea)






        self.ax.set_xlim(tiempo_ajustado[0], tiempo_ajustado[-1])

        if self.lineas:
            self.ax.legend()
        ticks_x = np.linspace(tiempo_ajustado[0], tiempo_ajustado[-1], 11)
        self.ax.set_xticks(ticks_x)
        self.ax.set_xticklabels([])








        try:
            valor_div = dict(self.tiempos_por_div)[self.var_tiempo_div.get()]
            self.offset_max = valor_div * 5
            self.offset_step = valor_div * 0.5
        except KeyError:
            self.offset_max = None
            self.offset_step = None

        if self.var_cursores.get():
            if posiciones_relativas and self.ax.get_xlim() and self.ax.get_ylim():
                x_min, x_max = self.ax.get_xlim()
                y_min, y_max = self.ax.get_ylim()
                dx = x_max - x_min
                dy = y_max - y_min
                
                posiciones_abs = {}
                for key in ['x1', 'x2', 'y1', 'y2']:
                    if key in posiciones_relativas:
                        pos_rel = max(0, min(1, posiciones_relativas[key])) 
                        if key.startswith('x'):
                            posiciones_abs[key] = x_min + pos_rel * dx
                        else:
                            posiciones_abs[key] = y_min + pos_rel * dy

                self.crear_cursores(posiciones=posiciones_abs)

            else:
                self.crear_cursores()
            self.actualizar_deltas_cursores()
        else:
            x_min, x_max = self.ax.get_xlim()
            y_min, y_max = self.ax.get_ylim()
            x_centro = (x_min + x_max) / 2
            y_centro = (y_min + y_max) / 2

            separacion_x = (x_max - x_min) * 0.1
            separacion_y = (y_max - y_min) * 0.1

            if self.cursor_x1:
                self.cursor_x1.set_xdata([x_centro - separacion_x]*2)
                self.cursor_x1.set_ydata([y_min, y_max])
            if self.cursor_x2:
                self.cursor_x2.set_xdata([x_centro + separacion_x]*2)
                self.cursor_x2.set_ydata([y_min, y_max])
            if self.cursor_y1:
                self.cursor_y1.set_ydata([y_centro - separacion_y]*2)
                self.cursor_y1.set_xdata([x_min, x_max])
            if self.cursor_y2:
                self.cursor_y2.set_ydata([y_centro + separacion_y]*2)
                self.cursor_y2.set_xdata([x_min, x_max])

            self.actualizar_label_deltas(0, 0)

        self.ax.plot([0.5, 0.5], [0, 1], color='black', linewidth=1.0, transform=self.ax.transAxes)
        self.ax.plot([0, 1], [0.5, 0.5], color='black', linewidth=1.0, transform=self.ax.transAxes)
        self.dibujar_divisiones()
        self.canvas.draw()

    def obtener_posiciones_relativas(self):
        posiciones = {}
        if not all([self.cursor_x1, self.cursor_x2, self.cursor_y1, self.cursor_y2]):
            return None

        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()

        try:
            posiciones['x1'] = (self.cursor_x1.get_xdata()[0] - x_min) / (x_max - x_min)
            posiciones['x2'] = (self.cursor_x2.get_xdata()[0] - x_min) / (x_max - x_min)
            posiciones['y1'] = (self.cursor_y1.get_ydata()[0] - y_min) / (y_max - y_min)
            posiciones['y2'] = (self.cursor_y2.get_ydata()[0] - y_min) / (y_max - y_min)
            return posiciones
        except Exception:
            return None

    def crear_cursores(self, rango_x=None, posiciones=None):
        if rango_x is None:
            x_min, x_max = self.ax.get_xlim()
        else:
            x_min, x_max = rango_x

        y_min, y_max = self.ax.get_ylim()

        escala_actual = (x_min, x_max, y_min, y_max)
        self.ultima_escala_cursores = escala_actual  

        for cursor in ['cursor_x1', 'cursor_x2', 'cursor_y1', 'cursor_y2']:
            linea = getattr(self, cursor, None)
            if linea:
                try:
                    linea.remove()
                except Exception:
                    pass
                setattr(self, cursor, None)

        pos_x1 = posiciones.get('x1', x_min + (x_max - x_min) * 0.25) if posiciones else x_min + (x_max - x_min) * 0.25
        pos_x2 = posiciones.get('x2', x_min + (x_max - x_min) * 0.75) if posiciones else x_min + (x_max - x_min) * 0.75
        pos_y1 = posiciones.get('y1', y_min + (y_max - y_min) * 0.25) if posiciones else y_min + (y_max - y_min) * 0.25
        pos_y2 = posiciones.get('y2', y_min + (y_max - y_min) * 0.75) if posiciones else y_min + (y_max - y_min) * 0.75

        self.cursor_x1 = self.ax.axvline(pos_x1, color='red', linestyle='--', picker=5)
        self.cursor_x2 = self.ax.axvline(pos_x2, color='red', linestyle='--', picker=5)
        self.cursor_y1 = self.ax.axhline(pos_y1, color='blue', linestyle='--', picker=5)
        self.cursor_y2 = self.ax.axhline(pos_y2, color='blue', linestyle='--', picker=5)

        self.canvas.draw_idle()

    def on_press(self, event):
        if not self.var_cursores.get():
            return
        if event.inaxes != self.ax:
            return

        for cursor in [self.cursor_x1, self.cursor_x2, self.cursor_y1, self.cursor_y2]:
            if cursor is not None:
                contains, _ = cursor.contains(event)
                if contains:
                    self.selected_cursor = cursor
                    print("Se tocó el cursor")  # Debug aquí
                    break

    def on_release(self, event):
        if not self.var_cursores.get():
            return
        self.selected_cursor = None

    def on_motion(self, event):
        if not self.var_cursores.get() or self.selected_cursor is None:
            return
        if event.inaxes != self.ax:
            return

        if self.selected_cursor in [self.cursor_x1, self.cursor_x2]:
            self.selected_cursor.set_xdata([event.xdata, event.xdata])
        elif self.selected_cursor in [self.cursor_y1, self.cursor_y2]:
            self.selected_cursor.set_ydata([event.ydata, event.ydata])
        
        self.canvas.draw()
        self.actualizar_deltas_cursores()

    def calcular_deltas(self):
        if None in (self.cursor_x1, self.cursor_x2, self.cursor_y1, self.cursor_y2):
            return

        dx = abs(self.cursor_x2.get_xdata()[0] - self.cursor_x1.get_xdata()[0])
        dy = abs(self.cursor_y2.get_ydata()[0] - self.cursor_y1.get_ydata()[0])

        self.actualizar_label_deltas(dx, dy)

    def actualizar_deltas_cursores(self):
        if None in (self.cursor_x1, self.cursor_x2, self.cursor_y1, self.cursor_y2):
            return

        try:
            x1 = self.cursor_x1.get_xdata()[0]
            x2 = self.cursor_x2.get_xdata()[0]
            y1 = self.cursor_y1.get_ydata()[0]
            y2 = self.cursor_y2.get_ydata()[0]

            delta_x = abs(x2 - x1)
            delta_y = abs(y2 - y1)

            self.actualizar_label_deltas(delta_x, delta_y)
        except Exception as e:
            print("Error al actualizar deltas:", e)

    def formatear_voltaje(self, valor):
        if abs(valor) < 1:
            return f"{valor * 1000:.3g} mV"
        else:
            return f"{valor:.3g} V"

    def actualizar_label_deltas(self, dx, dy):
        canal_idx = self.canal_cursores.get() - 1

        if canal_idx < len(self.volt_div_vars):
            volt_div_str = self.volt_div_vars[canal_idx].get()
            factor_volt_div = dict(self.voltajes_por_div).get(volt_div_str, 1)
            dy_escalado = dy * factor_volt_div
        else:
            dy_escalado = dy
            factor_volt_div = 1

        texto_volt = self.formatear_voltaje(dy_escalado)

        self.label_deltas.config(
            text=f"ΔX = {dx:.4g} {self.unidad_tiempo}, ΔY = {texto_volt} (Canal {canal_idx + 1})"
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = TC1ScopeApp(root)
    root.mainloop()
