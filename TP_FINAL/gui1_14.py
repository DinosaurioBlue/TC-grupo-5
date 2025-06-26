import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import re
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


# --- CONSTANTES DE CONFIGURACIÓN ---
# Constantes para los tipos de archivo CSV
CSV_FILE_TYPES_DESCRIPTION = "Archivos CSV"
CSV_FILE_EXTENSION_PATTERN = "*.csv"
DEFAULT_FILE_TYPES = [(CSV_FILE_TYPES_DESCRIPTION, CSV_FILE_EXTENSION_PATTERN)]

# Dimensiones de la pantalla del osciloscopio (en cm)
OSCILLOSCOPE_SCREEN_WIDTH_CM = 32
OSCILLOSCOPE_SCREEN_HEIGHT_CM = 12
SCREEN_DIVISIONS_X = 10
SCREEN_DIVISIONS_Y = 8

# Colores para el modo oscuro/claro
LIGHT_MODE_COLORS = {
    "bg": "lightgray",
    "fg": "black",
    "plot_bg": "#F0F0F0",
    "grid": "gray",
    "line_colors": ['blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'gray'],
    "cursor_x": "darkgreen",
    "cursor_y": "darkmagenta",
    "frame_bg": "lightgray",
    "label_fg": "black",
    "button_bg": "SystemButtonFace",
    "button_fg": "black"
}

DARK_MODE_COLORS = {
    "bg": "#2e2e2e",
    "fg": "white",
    "plot_bg": "#1e1e1e",
    "grid": "#444444",
    "line_colors": ['cyan', 'lime', 'magenta', 'yellow', 'orange', 'white', 'purple', 'lightgray'],
    "cursor_x": "lightblue",
    "cursor_y": "lightcoral",
    "frame_bg": "#3c3c3c",
    "label_fg": "white",
    "button_bg": "#4a4a4a",
    "button_fg": "white"
}


class TC1ScopeApp:
    def __init__(self, root):
        self.is_bode = False     
        self.root = root
        self.df = None
        self.primera_grafica = True
        self.df = None
        self.primera_grafica = True
        self.unidad_tiempo = "s"
        self.unidad_valor = "V"
        self.lineas = []
        self.selected_cursor = None
        self.cursor_x1 = None
        self.cursor_x2 = None
        self.cursor_y1 = None
        self.cursor_y2 = None
        self.ymin_global = None
        self.ymax_global = None
        self._actualizando_slider = False # Flag para evitar recursión en sliders
        self.offset_divisiones = 0.0 # Offset de tiempo en número de divisiones
        self.offset_tension_ch1 = 0.0
        self.offset_tension_ch2 = 0.0
        self.canal_offset = tk.IntVar(value=1) 
        self.canal_cursores = tk.IntVar(value=1) 
        self.var_cursores = tk.BooleanVar(value=False) 
        self.var_offset_tiempo = tk.DoubleVar(value=0.0) 
        self.var_modo_oscuro = tk.BooleanVar(value=False) 
        self.current_colors = LIGHT_MODE_COLORS # Colores actuales
        # Variables de control de visibilidad
        self.mostrar_ch1 = tk.BooleanVar(value=True)
        self.mostrar_ch2 = tk.BooleanVar(value=True)

        # Checkboxes para mostrar/ocultar canales
        self.chk_ch1 = tk.Checkbutton(self.root, text="View Channel 1", variable=self.mostrar_ch1,
                              command=self.actualizar_grafica)
        self.chk_ch2 = tk.Checkbutton(self.root, text="View Channel 2", variable=self.mostrar_ch2,
                                    command=self.actualizar_grafica)
        self.chk_ch1.pack()
        self.chk_ch2.pack()



        self.root.title("Oscilloscope GUI")

        # Ajuste de resolución de la ventana
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = int(screen_width * 0.9)
        height = int(screen_height * 0.9)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # Configuración de los estilos para ttk (para modo oscuro)
        self.style = ttk.Style()
        self.apply_theme()

        self.create_widgets()
        self.setup_plot()

        # Conectar eventos de Matplotlib para los cursores
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.canvas.mpl_connect('resize_event', self.on_resize) # Capturar evento de redimensionado de figura

    def apply_theme(self):
        """Aplica el tema (claro/oscuro) a la interfaz y el gráfico."""
        self.current_colors = DARK_MODE_COLORS if self.var_modo_oscuro.get() else LIGHT_MODE_COLORS

        # Configurar estilo de ttk
        self.style.theme_use("clam") # Un tema base que se puede personalizar

        # Configurar colores de fondo de Tkinter y ttk frames/widgets
        self.root.configure(bg=self.current_colors["bg"])
        self.style.configure("TFrame", background=self.current_colors["frame_bg"])
        self.style.configure("TLabelframe", background=self.current_colors["frame_bg"],
                             foreground=self.current_colors["label_fg"])
        self.style.configure("TLabelframe.Label", background=self.current_colors["frame_bg"],
                     foreground=self.current_colors["label_fg"])

        self.style.configure("TLabel", background=self.current_colors["frame_bg"],
                             foreground=self.current_colors["label_fg"])
        self.style.configure("TButton", background=self.current_colors["button_bg"],
                             foreground=self.current_colors["button_fg"])
        self.style.map("TButton",
                       background=[('active', self.current_colors["button_bg"])]
                       )
        self.style.configure("TCheckbutton", background=self.current_colors["frame_bg"],
                             foreground=self.current_colors["label_fg"])
        self.style.configure("TRadiobutton", background=self.current_colors["frame_bg"],
                             foreground=self.current_colors["label_fg"])
        texto_color_combo = "white" if self.var_modo_oscuro.get() else "black"
        fondo_combo = self.current_colors["plot_bg"]

        combo_text_color = "white" if self.var_modo_oscuro.get() else "black"
        combo_bg_color = "#2e2e2e" if self.var_modo_oscuro.get() else "white"
        combo_field_bg = "#3c3c3c" if self.var_modo_oscuro.get() else "white"

        self.style.configure("TCombobox",
            background=combo_bg_color,
            fieldbackground=combo_field_bg,
            foreground=combo_text_color,
            arrowcolor=combo_text_color
        )

        self.style.map("TCombobox",
            fieldbackground=[("readonly", combo_field_bg)],
            foreground=[("readonly", combo_text_color)],
            background=[("readonly", combo_bg_color)],
            arrowcolor=[("readonly", combo_text_color)]
        )


        



        # Configurar colores de Matplotlib
        if hasattr(self, 'ax') and hasattr(self, 'fig'):
            self.fig.set_facecolor(self.current_colors["plot_bg"])
            self.ax.set_facecolor(self.current_colors["plot_bg"])
            self.ax.spines['bottom'].set_color(self.current_colors["fg"])
            self.ax.spines['top'].set_color(self.current_colors["fg"])
            self.ax.spines['right'].set_color(self.current_colors["fg"])
            self.ax.spines['left'].set_color(self.current_colors["fg"])
            self.ax.tick_params(axis='x', colors=self.current_colors["fg"])
            self.ax.tick_params(axis='y', colors=self.current_colors["fg"])
            self.ax.xaxis.label.set_color(self.current_colors["fg"])
            self.ax.yaxis.label.set_color(self.current_colors["fg"])
            self.ax.title.set_color(self.current_colors["fg"])

            # Actualiza el grid si ya existe
            for line in self.ax.get_xgridlines() + self.ax.get_ygridlines():
                line.set_color(self.current_colors["grid"])
            
            # Re-dibuja líneas de datos y cursores con los nuevos colores si ya existen
            self.actualizar_grafica() 

        # Actualiza el estilo de los checkboxes personalizados según el modo
        if hasattr(self, 'chk_ch1') and hasattr(self, 'chk_ch2'):
            texto_color = "white" if self.var_modo_oscuro.get() else "black"
            self.chk_ch1.config(
                bg=self.current_colors["bg"],
                fg=texto_color,
                selectcolor=self.current_colors["bg"],
                activebackground=self.current_colors["bg"],
                activeforeground=texto_color
            )
            self.chk_ch2.config(
                bg=self.current_colors["bg"],
                fg=texto_color,
                selectcolor=self.current_colors["bg"],
                activebackground=self.current_colors["bg"],
                activeforeground=texto_color
            )



    def toggle_dark_mode(self):
        """Cambia entre modo claro y oscuro."""
        self.var_modo_oscuro.set(not self.var_modo_oscuro.get())
        self.apply_theme()

    def create_widgets(self):
        """Crea y organiza todos los widgets de la interfaz."""
        # Frame superior para botones principales y cursores
        top_frame = ttk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Botón Abrir CSV
        self.btn_abrir = ttk.Button(top_frame, text="Open CSV", command=self.abrir_csv)
        self.btn_abrir.pack(side=tk.LEFT, padx=5)

        # Checkbox Usar Cursores
        self.chk_cursores = ttk.Checkbutton(top_frame, text="Use cursors", variable=self.var_cursores, command=self.actualizar_grafica)
        self.chk_cursores.pack(side=tk.LEFT, padx=10)

        # Controles de Cursores y Deltas
        frame_deltas = ttk.Frame(top_frame)
        frame_deltas.pack(side=tk.LEFT, padx=10)
        ttk.Label(frame_deltas, text="ΔY Channel:").pack(side="left")
        ttk.Radiobutton(frame_deltas, text="Ch1", variable=self.canal_cursores, value=1, command=self.actualizar_deltas_cursores).pack(side="left")
        ttk.Radiobutton(frame_deltas, text="Ch2", variable=self.canal_cursores, value=2, command=self.actualizar_deltas_cursores).pack(side="left")
        
        # Etiqueta de Deltas
        self.label_deltas = ttk.Label(top_frame, text="ΔX = 0, ΔY = 0")
        self.label_deltas.pack(side=tk.RIGHT, padx=5)

        # Botón Default Setup y Modo Oscuro
        self.btn_default_setup = ttk.Button(top_frame, text="Default Setup", command=self.default_setup)
        self.btn_default_setup.pack(side=tk.RIGHT, padx=5)
        
        self.btn_toggle_mode = ttk.Button(top_frame, text="Dark Mode", command=self.toggle_dark_mode)
        self.btn_toggle_mode.pack(side=tk.RIGHT, padx=5)


        # Frame para controles de tiempo (Time/div y Offset de tiempo)
        time_control_frame = ttk.Frame(self.root)
        time_control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ttk.Label(time_control_frame, text="Time/div:").pack(side=tk.LEFT)
        self.tiempos_por_div = [
            ("1 ns/div", 1e-9), ("10 ns/div", 10e-9), ("25 ns/div", 25e-9), ("100 ns/div", 100e-9),
            ("1 μs/div", 1e-6), ("10 μs/div", 10e-6), ("25 μs/div", 25e-6), ("50 μs/div", 50e-6), ("100 μs/div", 100e-6),
            ("1 ms/div", 1e-3), ("10 ms/div", 10e-3), ("25 ms/div", 25e-3), ("50 ms/div", 50e-3), ("100 ms/div", 100e-3),
            ("1 s/div", 1)
        ]
        self.var_tiempo_div = tk.StringVar()
        self.combo_tiempo_div = ttk.Combobox(
            time_control_frame, values=[v[0] for v in self.tiempos_por_div],
            state="readonly", width=12, textvariable=self.var_tiempo_div
        )
        self.combo_tiempo_div.current(9) # Default a 1ms/div
        self.combo_tiempo_div.pack(side=tk.LEFT, padx=5)
        self.combo_tiempo_div.bind("<<ComboboxSelected>>", self.actualizar_grafica)

        # Slider de Offset de Tiempo
        self.scl_toffset = ttk.Scale(
            master=time_control_frame,
            from_=-5 * SCREEN_DIVISIONS_X, # Permitir offset de 5 divisiones a la izq
            to=5 * SCREEN_DIVISIONS_X,    # Permitir offset de 5 divisiones a la der
            orient='horizontal',
            command=self.on_slider_offset,
            variable=self.var_offset_tiempo
        )
        self.scl_toffset.set(0)
        self.scl_toffset.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Label(time_control_frame, text="Time Offset").pack(side=tk.LEFT)

        self.btn_reset_toffset = ttk.Button(time_control_frame, text="Reset", command=self.reset_offset)
        self.btn_reset_toffset.pack(side=tk.LEFT, padx=5)


        # Frame para controles de voltaje (Volt/div y Offset de tensión)
        volt_control_frame = ttk.Frame(self.root)
        volt_control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Selector de canal para offset
        ttk.Label(volt_control_frame, text="Voltage Offset Ch:").pack(side="left")
        ttk.Radiobutton(volt_control_frame, text="Ch1", variable=self.canal_offset, value=1, command=self.actualizar_slider_offset).pack(side="left")
        ttk.Radiobutton(volt_control_frame, text="Ch2", variable=self.canal_offset, value=2, command=self.actualizar_slider_offset).pack(side="left")

        # Slider de Offset de Tensión
        self.scl_tension_offset = ttk.Scale(
            master=volt_control_frame,
            from_=-5 * SCREEN_DIVISIONS_Y, # Offset de 5 divisiones hacia abajo
            to=5 * SCREEN_DIVISIONS_Y,     # Offset de 5 divisiones hacia arriba
            orient='horizontal',
            command=self.on_slider_offset_volt
        )
        self.scl_tension_offset.set(0)
        self.scl_tension_offset.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Label(volt_control_frame, text="Voltage Offset").pack(side=tk.LEFT)

        self.btn_reset_voffset = ttk.Button(volt_control_frame, text="Reset", command=self.reset_offset_volt)
        self.btn_reset_voffset.pack(side=tk.LEFT, padx=5)


        # Frame para Volt/div por canal
        self.frame_voltdiv = ttk.LabelFrame(self.root, text="Volts/div per channel")
        self.frame_voltdiv.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.voltajes_por_div = [
            ("1 mV/div", 1e-3), ("10 mV/div", 10e-3), ("25 mV/div", 25e-3), ("50 mV/div", 50e-3),
            ("100 mV/div", 100e-3), ("1 V/div", 1), ("2 V/div", 2), ("5 V/div", 5), ("10 V/div", 10)
        ]

        self.volt_div_vars = []
        self.volt_div_combos = []
        # Inicialmente, crea 2 combobox para los 2 canales más comunes.
        # Se recrearán dinámicamente en inicializar_volt_div si se carga un CSV con más/menos canales.
        for i in range(2): # Crea 2 combos por defecto
             var = tk.StringVar(value="1 V/div")
             combo = ttk.Combobox(self.frame_voltdiv, values=[v[0] for v in self.voltajes_por_div], textvariable=var, state='readonly', width=12)
             combo.pack(side=tk.LEFT, padx=5, pady=5)
             combo.bind("<<ComboboxSelected>>", self.actualizar_grafica)
             self.volt_div_vars.append(var)
             self.volt_div_combos.append(combo)

    def setup_plot(self):
        """Configura el área de trazado de Matplotlib."""
        ancho_in = OSCILLOSCOPE_SCREEN_WIDTH_CM / 2.54
        alto_in = OSCILLOSCOPE_SCREEN_HEIGHT_CM / 2.54
        self.fig, self.ax = plt.subplots(figsize=(ancho_in, alto_in))
        self.fig.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1) # Ajustar para título y labels
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)

        # Agrega la barra de herramientas de navegación de Matplotlib (zoom, pan, save)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.root)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.ax.set_title("Load a CSV file", color=self.current_colors["fg"])
        self.ax.set_xlabel("Time", color=self.current_colors["fg"])
        self.ax.set_ylabel("Voltage", color=self.current_colors["fg"])
        self.ax.legend()
        self.ax.grid(True)
        self.apply_theme() # Aplicar el tema inicial
        self.canvas.draw()

    def default_setup(self):
        """Restablece la configuración de visualización a valores por defecto."""
        # Restablecer sliders de offset
        self.scl_toffset.set(0.0)
        self.offset_divisiones = 0.0
        self.scl_tension_offset.set(0.0)
        self.offset_tension_ch1 = 0.0
        self.offset_tension_ch2 = 0.0
        self.canal_offset.set(1) # Canal de offset por defecto

        # Restablecer combobox de tiempo/div
        self.combo_tiempo_div.current(9) # Default a 1ms/div

        # Restablecer comboboxes de volt/div
        for var in self.volt_div_vars:
            var.set("1 V/div") 

        # Desactiva cursores
        self.var_cursores.set(False)

        # Actualiza la gráfica con la nueva configuración
        self.actualizar_grafica()


    def inicializar_volt_div(self):
        """
        Destruye y recrea los comboboxes de Volt/div
        según el número de columnas de datos en el CSV cargado.
        """
        # Elimina comboboxes existentes
        for combo in self.volt_div_combos:
            combo.destroy()
        self.volt_div_vars, self.volt_div_combos = [], []

        if self.df is None or self.df.shape[1] < 2:
            return # No hay datos o solo columna de tiempo

        opciones = [v[0] for v in self.voltajes_por_div]
        # Crea un combobox por cada columna de datos (excluyendo la primera de tiempo)
        for i in range(self.df.shape[1] - 1):
            var = tk.StringVar(value="1 V/div") # Valor por defecto
            combo = ttk.Combobox(self.frame_voltdiv, values=opciones, state="readonly", width=12, textvariable=var)
            combo.pack(side=tk.LEFT, padx=5, pady=5)
            combo.bind("<<ComboboxSelected>>", self.actualizar_grafica)
            self.volt_div_vars.append(var)
            self.volt_div_combos.append(combo)
        
        self.apply_theme() # Reaplica el tema a los nuevos comboboxes

    def dibujar_divisiones(self):
        """Dibuja la cuadrícula principal y subdivisión simulando un osciloscopio."""
        self.ax.grid(False) # Desactiva la cuadrícula automática de Matplotlib

        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()

        # Calcula el espaciado real de las divisiones basado en el rango visible
        # y el número de divisiones deseadas
        x_div_spacing = (x_max - x_min) / SCREEN_DIVISIONS_X
        y_div_spacing = (y_max - y_min) / SCREEN_DIVISIONS_Y

        # Líneas de la cuadrícula principal
        for x_val in np.arange(x_min, x_max + x_div_spacing, x_div_spacing):
            self.ax.axvline(x=x_val, color=self.current_colors["grid"], linestyle='-', linewidth=0.8, zorder=0)
        for x_val in np.arange(x_min, x_max - x_div_spacing, -x_div_spacing):
            self.ax.axvline(x=x_val, color=self.current_colors["grid"], linestyle='-', linewidth=0.8, zorder=0)

        for y_val in np.arange(y_min, y_max + y_div_spacing, y_div_spacing):
            self.ax.axhline(y=y_val, color=self.current_colors["grid"], linestyle='-', linewidth=0.8, zorder=0)
        for y_val in np.arange(y_min, y_max - y_div_spacing, -y_div_spacing):
            self.ax.axhline(y=y_val, color=self.current_colors["grid"], linestyle='-', linewidth=0.8, zorder=0)

        # Líneas de la cuadrícula de subdivisión
        # Cada división principal se divide en 5
        x_sub_spacing = x_div_spacing / 5
        y_sub_spacing = y_div_spacing / 5

        for x_val in np.arange(x_min, x_max + x_sub_spacing, x_sub_spacing):
            self.ax.axvline(x=x_val, color=self.current_colors["grid"], linestyle=':', linewidth=0.4, zorder=0)
        for x_val in np.arange(x_min, x_max - x_sub_spacing, -x_sub_spacing):
            self.ax.axvline(x=x_val, color=self.current_colors["grid"], linestyle=':', linewidth=0.4, zorder=0)

        for y_val in np.arange(y_min, y_max + y_sub_spacing, y_sub_spacing):
            self.ax.axhline(y=y_val, color=self.current_colors["grid"], linestyle=':', linewidth=0.4, zorder=0)
        for y_val in np.arange(y_min, y_max - y_sub_spacing, -y_sub_spacing):
            self.ax.axhline(y=y_val, color=self.current_colors["grid"], linestyle=':', linewidth=0.4, zorder=0)

        # Ejes centrales (cero)
        self.ax.axvline(x=0, color=self.current_colors["fg"], linewidth=1.0, zorder=1) # Eje Y en x=0
        self.ax.axhline(y=0, color=self.current_colors["fg"], linewidth=1.0, zorder=1) # Eje X en y=0
        
        # Elimina los ticks por defecto de Matplotlib y usa los queridos
        self.ax.set_xticks([])
        self.ax.set_yticks([])


    def abrir_csv(self):
        """
        Abre un CSV, limpia nombres de columna de símbolos no ASCII (°, θ, etc.),
        convierte todo a numérico descartando columnas vacías, detecta Bode
        por regex y renombra sus columnas, o inicializa osciloscopio en caso contrario.
        """
        ruta = filedialog.askopenfilename(filetypes=DEFAULT_FILE_TYPES)
        if not ruta:
            return

        try:
            # 1) detecta separador
            with open(ruta, 'r', encoding='latin1', errors='ignore') as f:
                primera = f.readline()
            sep = '\t' if '\t' in primera else ','

            # 2) lee CSV (saltando líneas malformadas)
            df = pd.read_csv(ruta,
                             sep=sep,
                             encoding='latin1',
                             engine='python',
                             on_bad_lines='skip')

            # 3) limpia caracteres: quitar todo lo que no sea ASCII
            df.columns = [
                re.sub(r'[^\x20-\x7E]+', '', col).strip()
                for col in df.columns
            ]

            # 4) convertie todo a numérico (coerce), luego descarta columnas totalmente
            df = df.apply(pd.to_numeric, errors='coerce')
            df = df.loc[:, df.notna().any(axis=0)]
            if df.shape[1] < 2:
                messagebox.showwarning(
                    "Formato Inválido",
                    "No quedan al menos dos columnas numéricas tras la limpieza."
                )
                return

            # 5) elimina filas con cualquier
            df = df.dropna()
            if df.empty:
                messagebox.showwarning(
                    "Archivo Vacío",
                    "No quedan filas con datos completos tras la limpieza."
                )
                return

            
            self.df = df

            # Detectar si es Bode por regex sobre nombres
            freq = next((c for c in df.columns
                         if re.search(r'frequency', c, re.I) and re.search(r'hz', c, re.I)), None)
            gain = next((c for c in df.columns
                         if re.search(r'gain', c, re.I) and re.search(r'db', c, re.I)), None)
            phase = next((c for c in df.columns
                          if re.search(r'phase', c, re.I)), None)

            if freq and gain and phase:
                self.is_bode = True
                # renombra para plot_bode
                self.df = df.rename(columns={
                    freq: 'Frequency (Hz)',
                    gain: 'Gain (dB)',
                    phase: 'Phase ()'
                })
            else:
                self.is_bode = False
                # Prepara la vista como un osciloscopio.
                self.inicializar_volt_div()
                self.actualizar_rango_y_global()
                self.update_voltage_offset_range()
                self.t_min = self.df.iloc[:, 0].min()
                self.t_max = self.df.iloc[:, 0].max()
                self.ajustar_escala_tiempo()

            # 7) refresca la gráfica
            self.actualizar_grafica()

        except pd.errors.EmptyDataError:
            messagebox.showwarning("Error de Lectura", "El archivo CSV está vacío.")
        except Exception as e:
            messagebox.showerror(
                "Error Inesperado",
                f"Ocurrió un error al procesar el CSV:\n{e}"
            )

    def actualizar_rango_y_global(self):
        """
        Calcula el rango global Y (min y max) de todos los datos
        sin considerar offset ni escala por división, para el auto-escalado inicial.
        """
        if self.df is None:
            self.ymin_global = None
            self.ymax_global = None
            return
        
        columnas_datos = self.df.columns[1:] 
        if not columnas_datos.empty:
            self.ymin_global = self.df[columnas_datos].min().min()
            self.ymax_global = self.df[columnas_datos].max().max()
        else:
            self.ymin_global = None
            self.ymax_global = None


    def on_slider_offset(self, valor_offset):
        """Maneja el evento del slider de offset de tiempo."""
        if self.df is None:
            return
        # El valor del slider es el número de divisiones que se quiere mover.
        self.offset_divisiones = float(valor_offset)
        self.actualizar_grafica()
        

    def reset_offset(self):
        self.var_offset_tiempo.set(0.0)
        self.offset_divisiones = 0.0
        self.actualizar_grafica()

    def on_slider_offset_volt(self, valor_offset_entero):
        """Maneja el evento del slider de offset de tensión para el canal seleccionado."""
        # No hacemos nada si todavía estamos actualizando o no hay datos
        if self._actualizando_slider or self.df is None:
            return
        # Ignorar el slider si el canal está oculto
        canal = self.canal_offset.get()
        if (canal == 1 and not self.mostrar_ch1.get()) or (canal == 2 and not self.mostrar_ch2.get()):
            return
        self._actualizando_slider = True
        try:
            # Obteniene factor de volt/div del canal
            volt_div_str = self.volt_div_vars[canal-1].get() if canal-1 < len(self.volt_div_vars) else "1 V/div"
            volt_div_value = dict(self.voltajes_por_div).get(volt_div_str, 1)
            # Convertierte divisiones a volts
            offset_real = float(valor_offset_entero) * volt_div_value
            # Asigna al atributo correcto
            if canal == 1:
                self.offset_tension_ch1 = offset_real
            else:
                self.offset_tension_ch2 = offset_real
            self.actualizar_grafica()
        finally:
            self._actualizando_slider = False
    
    def actualizar_slider_offset(self):
        """
        Sincroniza la posición del slider con el valor real de offset de tensión
        solo si el canal está visible.
        """
        if self._actualizando_slider:  # Evita recursión
            return
        canal = self.canal_offset.get()
        # Si el canal está oculto, ponemos slider en cero y no hacemos nada
        if (canal == 1 and not self.mostrar_ch1.get()) or (canal == 2 and not self.mostrar_ch2.get()):
            self.scl_tension_offset.set(0)
            return
        self._actualizando_slider = True
        try:
            # Convertierte el offset real a divisiones
            if canal == 1:
                volt_div_str = self.volt_div_vars[0].get() if len(self.volt_div_vars) > 0 else "1 V/div"
                factor = dict(self.voltajes_por_div).get(volt_div_str, 1)
                self.scl_tension_offset.set(self.offset_tension_ch1 / factor if factor else 0)
            else:
                volt_div_str = self.volt_div_vars[1].get() if len(self.volt_div_vars) > 1 else "1 V/div"
                factor = dict(self.voltajes_por_div).get(volt_div_str, 1)
                self.scl_tension_offset.set(self.offset_tension_ch2 / factor if factor else 0)
        finally:
            self._actualizando_slider = False
            self.update_voltage_offset_range()

    def reset_offset_volt(self):
        """Restablece los offsets de tensión de ambos canales a cero."""
        self.scl_tension_offset.set(0) # Reinicia el slider visualmente
        self.offset_tension_ch1 = 0.0
        self.offset_tension_ch2 = 0.0
        self.actualizar_grafica()

    def ajustar_escala_tiempo(self):
        """
        Ajusta el combobox de tiempo/div para que muestre una escala
        apropiada para la duración total de los datos.
        """
        if self.df is None:
            return

        t_min_data = self.df.iloc[:, 0].min()
        t_max_data = self.df.iloc[:, 0].max()
        duracion_total = t_max_data - t_min_data

        # Si el rango de tiempo es 0 (ej. un solo punto o datos inválidos)
        if duracion_total == 0:
            self.var_tiempo_div.set(self.tiempos_por_div[9][0]) # Default a 1ms/div
            return

        # Calcula el tiempo por división necesario para mostrar toda la duración en 10 divisiones
        # Usamos 8 divisiones para que la señal no ocupe todo el ancho
        tiempo_por_div_necesario = duracion_total / (SCREEN_DIVISIONS_X * 0.8) # Deja un poco de margen

        # Encuentra la mejor escala de tiempo por división
        best_match_idx = 0
        min_diff = float('inf')
        for i, (label, val) in enumerate(self.tiempos_por_div):
            diff = abs(val - tiempo_por_div_necesario)
            if diff < min_diff:
                min_diff = diff
                best_match_idx = i

        self.var_tiempo_div.set(self.tiempos_por_div[best_match_idx][0])
        

        self.scl_toffset.config(from_=-SCREEN_DIVISIONS_X / 2, to=SCREEN_DIVISIONS_X / 2)


    def ajustar_unidades_tiempo(self, tiempo_s):
        """Ajusta la escala y unidad de tiempo para visualización (ns, us, ms, s)."""
        max_abs = np.max(np.abs(tiempo_s))
        if max_abs < 1e-8: # Si los valores son extremadamente pequeños, usar ns
            return tiempo_s * 1e9, "ns"
        elif max_abs < 1e-5: # < 10 us
            return tiempo_s * 1e6, "µs"
        elif max_abs < 1e-2: # < 10 ms
            return tiempo_s * 1e3, "ms"
        else:
            return tiempo_s, "s"

    def ajustar_unidades_valor(self, valores):
        """Ajusta la escala y unidad de valor para visualización (µV, mV, V)."""
        max_abs = np.max(np.abs(valores))
        if max_abs < 1e-4: # < 100 µV
            return valores * 1e6, "µV"
        elif max_abs < 1: # < 1 V
            return valores * 1e3, "mV"
        else:
            return valores, "V"

    def on_resize(self, event):
        """Maneja el evento de redimensionamiento de la figura para actualizar la cuadrícula."""
        self.actualizar_grafica()


    def actualizar_grafica(self, event=None):
        self.update_voltage_offset_range()
        """
        Limpia y redibuja el gráfico, aplicando offsets, escalas,
        y actualizando cursores y cuadrícula.
        """
        # Si es CSV de Bode, plot_bode()
        if self.is_bode:
            self.plot_bode()
            return
        # Guardado de las posiciones
        abs_pos = self.obtener_posiciones_absolutas()
        self.fig.clear()
        self.ax = self.fig.add_subplot(1,1,1)

        if not self.is_bode:
            self.fig.clear()
            self.ax = self.fig.add_subplot(1,1,1)
        posiciones_relativas = self.obtener_posiciones_relativas()
        
        self.ax.clear()
        self.lineas.clear() # Limpia las referencias a las líneas antiguas

        # Establece el color de fondo del eje y la figura
        self.fig.set_facecolor(self.current_colors["plot_bg"])
        self.ax.set_facecolor(self.current_colors["plot_bg"])
        
        # Configura colores de los bordes del grafico y ticks
        for spine in self.ax.spines.values():
            spine.set_edgecolor(self.current_colors["fg"])
        self.ax.tick_params(axis='x', colors=self.current_colors["fg"])
        self.ax.tick_params(axis='y', colors=self.current_colors["fg"])
        self.ax.xaxis.label.set_color(self.current_colors["fg"])
        self.ax.yaxis.label.set_color(self.current_colors["fg"])
        self.ax.title.set_color(self.current_colors["fg"])
        
        if self.df is None:
            self.ax.set_title("Load a CSV file", color=self.current_colors["fg"])
            self.ax.set_xlabel("Time", color=self.current_colors["fg"])
            self.ax.set_ylabel("Voltage", color=self.current_colors["fg"])
            self.canvas.draw_idle()
            return

        tiempo_col = self.df.columns[0]
        tiempo_original = self.df[tiempo_col].values

        tiempo_div_str = self.var_tiempo_div.get()
        tiempo_div_segs = dict(self.tiempos_por_div).get(tiempo_div_str, 1e-3) # Default a 1ms/div si no se encuentra


        center_time = tiempo_original[0] + (tiempo_original[-1] - tiempo_original[0]) / 2 + (self.offset_divisiones * tiempo_div_segs)
        
        t_start_visible = center_time - (SCREEN_DIVISIONS_X / 2 * tiempo_div_segs)
        t_end_visible = center_time + (SCREEN_DIVISIONS_X / 2 * tiempo_div_segs)

        # Filtra los datos para la ventana de tiempo actual
        idx_visible = np.where((tiempo_original >= t_start_visible) & (tiempo_original <= t_end_visible))[0]

        if len(idx_visible) < 2:
            self.ax.set_title("No hay suficientes datos en el rango visible.", color=self.current_colors["fg"])
            self.ax.set_xlabel(f"Tiempo ({self.unidad_tiempo})", color=self.current_colors["fg"])
            self.ax.set_ylabel(f"Voltaje ({self.unidad_valor})", color=self.current_colors["fg"])
            self.canvas.draw_idle()
            return
        
        tiempo_ventana = tiempo_original[idx_visible]
        tiempo_ajustado, self.unidad_tiempo = self.ajustar_unidades_tiempo(tiempo_ventana)
        
        # Establecer límites X del gráfico
        self.ax.set_xlim(tiempo_ajustado.min(), tiempo_ajustado.max())
        
        ymin_current_view = float('inf')
        ymax_current_view = float('-inf')

        num_canales = len(self.df.columns) - 1
        
        # Si no hay datos, o si todas las columnas de datos están vacías,
        # asegura un rango Y por defecto
        if num_canales == 0:
            ymin_current_view = -5 # 1 V/div, 10 div = 10V. Cero en el medio.
            ymax_current_view = 5
        else:
             # Calcula el rango visible de Y para cada canal y luego combinar
            for i in range(num_canales):
                datos_originales = self.df[self.df.columns[i + 1]].values[idx_visible]
                
                volt_div_str = (self.volt_div_vars[i].get() if i < len(self.volt_div_vars) else "1 V/div")
                factor_volt_div = dict(self.voltajes_por_div).get(volt_div_str, 1)

                datos_ajustados = datos_originales / factor_volt_div

                # Aplica offset de tensión
                if i == 0:
                    datos_ajustados += self.offset_tension_ch1 / factor_volt_div # Offset está en V, se divide por factor_volt_div
                elif i == 1:
                    datos_ajustados += self.offset_tension_ch2 / factor_volt_div
                
                if datos_ajustados.size > 0:
                    ymin_current_view = min(ymin_current_view, np.min(datos_ajustados))
                    ymax_current_view = max(ymax_current_view, np.max(datos_ajustados))

            # Asegurar un rango Y mínimo si los datos son planos
            if ymax_current_view - ymin_current_view < 1e-9: # Si el rango es casi cero
                avg_val = (ymin_current_view + ymax_current_view) / 2
                ymin_current_view = avg_val - 5 # +- 5 V si no hay rango
                ymax_current_view = avg_val + 5
            
            # Ajustar los límites Y del eje para que los datos quepan dentro de 8 divisiones verticales
            # Se centra el rango y se asegura que el total sea 8 * volt_div_factor_medio
            volt_div_factor_medio = 1 
            if num_canales > 0 and len(self.volt_div_vars) > 0:
                # Tomar el volt/div del primer canal como referencia para el escalado general Y
                ref_volt_div_str = self.volt_div_vars[0].get()
                volt_div_factor_medio = dict(self.voltajes_por_div).get(ref_volt_div_str, 1)
            
            y_range_target = SCREEN_DIVISIONS_Y * volt_div_factor_medio

            current_y_center = (ymin_current_view + ymax_current_view) / 2
            
            self.ax.set_ylim(current_y_center - y_range_target / 2, current_y_center + y_range_target / 2)


        # Dibujar las líneas de datos (sin duplicación y con visibilidad controlada)
        colores = self.current_colors["line_colors"]

        for i in range(num_canales):
            # Chequea si el canal está habilitado por los checkboxes
            if (i == 0 and not self.mostrar_ch1.get()) or (i == 1 and not self.mostrar_ch2.get()):
                continue  # Salta canal oculto

            datos_originales = self.df[self.df.columns[i + 1]].values[idx_visible]

            volt_div_str = self.volt_div_vars[i].get() if i < len(self.volt_div_vars) else "1 V/div"
            factor_volt_div = dict(self.voltajes_por_div).get(volt_div_str, 1)
            datos_ajustados = datos_originales / factor_volt_div

            # Aplica offset según canal
            if i == 0:
                datos_ajustados += self.offset_tension_ch1 / factor_volt_div
            elif i == 1:
                datos_ajustados += self.offset_tension_ch2 / factor_volt_div

            linea, = self.ax.plot(
                tiempo_ajustado, datos_ajustados,
                color=colores[i % len(colores)],
                label=f"{self.df.columns[i + 1]} ({volt_div_str})"
            )
            self.lineas.append(linea)

        


        self.ax.set_xlabel(f"Time ({self.unidad_tiempo})", color=self.current_colors["fg"])
        self.ax.set_ylabel(f"Voltage ({self.unidad_valor})", color=self.current_colors["fg"])
        if self.lineas:
            self.ax.legend(facecolor=self.current_colors["plot_bg"], edgecolor=self.current_colors["fg"], labelcolor=self.current_colors["fg"])

        # Redibuja las divisiones de la cuadrícula
        self.dibujar_divisiones()

        # Actualiza cursores si están activados
        if self.var_cursores.get() and abs_pos:
            self.crear_cursores_absoluto(abs_pos)
        elif self.var_cursores.get():
            self.crear_cursores()  # posiciones por defecto
        else:
            # remover cursores
            for attr in ['cursor_x1','cursor_x2','cursor_y1','cursor_y2']:
                cur = getattr(self, attr)
                if cur and cur in self.ax.lines:
                    self.ax.lines.remove(cur)
                    setattr(self, attr, None)
        self.canvas.draw_idle()


    def obtener_posiciones_relativas(self):
        """
        Calcula las posiciones relativas (0 a 1) de los cursores
        dentro de los límites actuales del gráfico.
        """
        posiciones = {}
        # Solo si todos los cursores están instanciados
        if not all([self.cursor_x1, self.cursor_x2, self.cursor_y1, self.cursor_y2]):
            return None

        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()

        if (x_max - x_min) == 0 or (y_max - y_min) == 0:
            return None

        try:
            posiciones['x1'] = (self.cursor_x1.get_xdata()[0] - x_min) / (x_max - x_min)
            posiciones['x2'] = (self.cursor_x2.get_xdata()[0] - x_min) / (x_max - x_min)
            posiciones['y1'] = (self.cursor_y1.get_ydata()[0] - y_min) / (y_max - y_min)
            posiciones['y2'] = (self.cursor_y2.get_ydata()[0] - y_min) / (y_max - y_min)
            return posiciones
        except Exception:
            return None

    def crear_cursores(self, posiciones=None):
        """
        Crea o actualiza los cursores X e Y.
        Si 'posiciones' es None, los inicializa en el centro de la vista actual.
        """
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()

        # Eliminar cursores existentes antes de crear nuevos
        for cursor_attr in ['cursor_x1', 'cursor_x2', 'cursor_y1', 'cursor_y2']:
            cursor = getattr(self, cursor_attr)
            if cursor:
                try:
                    if cursor in self.ax.lines:
                        self.ax.lines.remove(cursor)
                except Exception as e:
                    print(f"Error al intentar eliminar cursor {cursor_attr}: {e}")
                setattr(self, cursor_attr, None)


        # Posiciones predeterminadas si no se especifican
        if posiciones is None:
            pos_x1 = x_min + (x_max - x_min) * 0.25
            pos_x2 = x_min + (x_max - x_min) * 0.75
            pos_y1 = y_min + (y_max - y_min) * 0.25
            pos_y2 = y_min + (y_max - y_min) * 0.75
        else:
            # Usa posiciones guardadas, asegurándose de que estén dentro de los límites
            dx_range = (x_max - x_min)
            dy_range = (y_max - y_min)
            
            pos_x1 = x_min + max(0, min(1, posiciones.get('x1', 0.25))) * dx_range
            pos_x2 = x_min + max(0, min(1, posiciones.get('x2', 0.75))) * dx_range
            pos_y1 = y_min + max(0, min(1, posiciones.get('y1', 0.25))) * dy_range
            pos_y2 = y_min + max(0, min(1, posiciones.get('y2', 0.75))) * dy_range

        self.cursor_x1 = self.ax.axvline(pos_x1, color=self.current_colors["cursor_x"], linestyle='--', picker=5)
        self.cursor_x2 = self.ax.axvline(pos_x2, color=self.current_colors["cursor_x"], linestyle='--', picker=5)
        self.cursor_y1 = self.ax.axhline(pos_y1, color=self.current_colors["cursor_y"], linestyle='--', picker=5)
        self.cursor_y2 = self.ax.axhline(pos_y2, color=self.current_colors["cursor_y"], linestyle='--', picker=5)

        self.canvas.draw_idle()


    def on_press(self, event):
        """Maneja el evento de presionar el botón del mouse para seleccionar un cursor."""
        if not self.var_cursores.get() or event.inaxes != self.ax:
            return

        # Iterar sobre los cursores para ver cuál fue seleccionado
        for cursor_name, cursor_obj in [('cursor_x1', self.cursor_x1), ('cursor_x2', self.cursor_x2),
                                         ('cursor_y1', self.cursor_y1), ('cursor_y2', self.cursor_y2)]:
            if cursor_obj is not None:
                contains, _ = cursor_obj.contains(event)
                if contains:
                    self.selected_cursor = cursor_obj
                    self.canvas.mpl_disconnect('motion_notify_event') # Desconecta temporalmente para evitar que se mueva durante on_press
                    self.canvas.mpl_connect('motion_notify_event', self.on_motion) # Reconecta para mover
                    break

    def on_release(self, event):
        """Maneja el evento de soltar el botón del mouse."""
        if not self.var_cursores.get():
            return
        self.selected_cursor = None # Desselecciona el cursor
        self.actualizar_deltas_cursores() # Recalcular deltas al soltar el cursor


    def on_motion(self, event):
        """Maneja el evento de mover el mouse para arrastrar un cursor."""
        if not self.var_cursores.get() or self.selected_cursor is None or event.inaxes != self.ax:
            return

        if self.selected_cursor in [self.cursor_x1, self.cursor_x2]:
            if event.xdata is not None:
                self.selected_cursor.set_xdata([event.xdata, event.xdata])
        elif self.selected_cursor in [self.cursor_y1, self.cursor_y2]:
            if event.ydata is not None:
                self.selected_cursor.set_ydata([event.ydata, event.ydata])
        
        self.canvas.draw_idle() # Actualiza solo el área afectada

    def calcular_deltas(self):
        pass

    def actualizar_deltas_cursores(self):
        """Calcula y muestra los valores delta (ΔX y ΔY) de los cursores."""
        if not all([self.cursor_x1, self.cursor_x2, self.cursor_y1, self.cursor_y2]):
            self.actualizar_label_deltas(0, 0, show_channel=False) # No hay cursores, resetear
            return

        try:
            x1 = self.cursor_x1.get_xdata()[0]
            x2 = self.cursor_x2.get_xdata()[0]
            y1 = self.cursor_y1.get_ydata()[0]
            y2 = self.cursor_y2.get_ydata()[0]

            delta_x = abs(x2 - x1)
            delta_y = abs(y2 - y1)

            # Para delta Y, escala según el canal elegido para los cursores
            canal_idx = self.canal_cursores.get() - 1 # 0 para Ch1, 1 para Ch2

            if self.df is not None and canal_idx < len(self.volt_div_vars):
                volt_div_str = self.volt_div_vars[canal_idx].get()
                factor_volt_div = dict(self.voltajes_por_div).get(volt_div_str, 1)

                if self.unidad_valor == "mV":
                    delta_y_real = delta_y / 1e3
                elif self.unidad_valor == "µV":
                    delta_y_real = delta_y / 1e6
                else: # "V"
                    delta_y_real = delta_y

                self.actualizar_label_deltas(delta_x, delta_y_real, channel_num=canal_idx + 1)
            else:
                self.actualizar_label_deltas(delta_x, delta_y, show_channel=False) # Fallback si no hay canal seleccionado o datos

        except Exception as e:
            self.actualizar_label_deltas(0, 0, show_channel=False)


    def formatear_valor(self, valor, unidad_referencia):
        """Formatea un valor numérico a una cadena con la unidad adecuada."""
        if unidad_referencia == "ns":
            return f"{valor:.3g} ns"
        elif unidad_referencia == "µs":
            return f"{valor:.3g} µs"
        elif unidad_referencia == "ms":
            return f"{valor:.3g} ms"
        elif unidad_referencia == "s":
            return f"{valor:.3g} s"
        elif unidad_referencia == "mV":
            return f"{valor:.3g} mV"
        elif unidad_referencia == "µV":
            return f"{valor:.3g} µV"
        elif unidad_referencia == "V":
            return f"{valor:.3g} V"
        else:
            return f"{valor:.3g} {unidad_referencia}"


    def actualizar_label_deltas(self, dx, dy, channel_num=None, show_channel=True):
        """Actualiza la etiqueta que muestra los deltas de los cursores."""
        texto_dx = self.formatear_valor(dx, self.unidad_tiempo)
        texto_dy = self.formatear_valor(dy, "V") # Mostrar siempre en V para los deltas reales

        if show_channel and channel_num is not None:
            self.label_deltas.config(text=f"ΔX = {texto_dx}, ΔY = {texto_dy} (Canal {channel_num})")
        else:
            self.label_deltas.config(text=f"ΔX = {texto_dx}, ΔY = {texto_dy}")
    
    def plot_bode(self):
        """Dibuja el diagrama de Bode (Gain dB y Phase ° vs Frequency) respetando el tema."""
        # Limpio la figura y creo dos ejes apilados
        self.fig.clear()
        ax1 = self.fig.add_subplot(211)
        ax2 = self.fig.add_subplot(212)

        # Columnas esperadas
        f = self.df["Frequency (Hz)"].values
        g = self.df["Gain (dB)"].values
        p = self.df["Phase ()"].values

        # Aplico colores del tema a ambos ejes
        for ax in (ax1, ax2):
            ax.set_facecolor(self.current_colors["plot_bg"])
            for spine in ax.spines.values():
                spine.set_edgecolor(self.current_colors["fg"])
            ax.tick_params(axis='x', colors=self.current_colors["fg"])
            ax.tick_params(axis='y', colors=self.current_colors["fg"])
            ax.xaxis.label.set_color(self.current_colors["fg"])
            ax.yaxis.label.set_color(self.current_colors["fg"])

        # Ganancia (dB)
        ax1.semilogx(f, g, linestyle='-', marker='o', markersize=4,
                     color=self.current_colors["line_colors"][0])
        ax1.set_title("BODE Diagram", color=self.current_colors["fg"])
        ax1.set_ylabel("Gain (dB)", color=self.current_colors["fg"])
        ax1.grid(True, which='both', linestyle='--', linewidth=0.5,
                 color=self.current_colors["grid"])

        # Fase (°)
        ax2.semilogx(f, p, linestyle='-', marker='o', markersize=4,
                     color=self.current_colors["line_colors"][1])
        ax2.set_xlabel("Frequency (Hz)", color=self.current_colors["fg"])
        ax2.set_ylabel("Phase (°)", color=self.current_colors["fg"])
        ax2.grid(True, which='both', linestyle='--', linewidth=0.5,
                 color=self.current_colors["grid"])

        # Fondo de figura
        self.fig.set_facecolor(self.current_colors["plot_bg"])
        self.canvas.draw_idle()
    def obtener_posiciones_absolutas(self):
        """
        Captura las posiciones actuales de los cursores en coordenadas de datos.
        """
        if not all([self.cursor_x1, self.cursor_x2, self.cursor_y1, self.cursor_y2]):
            return None
        try:
            return {
                'x1': self.cursor_x1.get_xdata()[0],
                'x2': self.cursor_x2.get_xdata()[0],
                'y1': self.cursor_y1.get_ydata()[0],
                'y2': self.cursor_y2.get_ydata()[0]
            }
        except Exception:
            return None

    def crear_cursores_absoluto(self, posiciones):
        """
        Vuelve a colocar los cursores en posiciones absolutas de datos, sin cambiar su valor.
        """
        # Eliminar cursores existentes
        for attr in ['cursor_x1','cursor_x2','cursor_y1','cursor_y2']:
            cur = getattr(self, attr)
            if cur and cur in self.ax.lines:
                self.ax.lines.remove(cur)
            setattr(self, attr, None)
        # Dibujar en coordenadas de datos sin escalar
        self.cursor_x1 = self.ax.axvline(posiciones['x1'], color=self.current_colors['cursor_x'], linestyle='--', picker=5)
        self.cursor_x2 = self.ax.axvline(posiciones['x2'], color=self.current_colors['cursor_x'], linestyle='--', picker=5)
        self.cursor_y1 = self.ax.axhline(posiciones['y1'], color=self.current_colors['cursor_y'], linestyle='--', picker=5)
        self.cursor_y2 = self.ax.axhline(posiciones['y2'], color=self.current_colors['cursor_y'], linestyle='--', picker=5)

    def update_voltage_offset_range(self):
        """
        Ajusta el rango del slider de offset de tensión para que la onda completa
        quepa en pantalla (± mitad del rango global de Y / Volt/div).
        """
        # Necesitamos un rango global válido
        if self.df is None or self.ymin_global is None or self.ymax_global is None:
            return

        total_range = self.ymax_global - self.ymin_global
        if total_range <= 0:
            return

        # Canal seleccionado para offset (0-index)
        ch = self.canal_offset.get() - 1
        if 0 <= ch < len(self.volt_div_vars):
            # factor volt/div
            vd_str = self.volt_div_vars[ch].get()
            vd_val = dict(self.voltajes_por_div).get(vd_str, 1)
            if vd_val <= 0:
                return
            # cuántas divisiones necesitamos para cubrir ± half_range
            half_divs = (total_range / vd_val) / 2
            # reconfiguramos el slider
            self.scl_tension_offset.config(from_=-half_divs, to=half_divs)


if __name__ == "__main__":
    root = tk.Tk()
    app = TC1ScopeApp(root)
    root.mainloop()