import ltspice
import numpy as np
import matplotlib.pyplot as plt
import os

# --- Configuración del Análisis ---
# Define la ruta al archivo .raw de LTspice y los nombres de las señales de interés.
RAW_FILE = os.path.join("figura 5", "Notch.raw") # ¡Asegúrate de que esta ruta sea correcta!
INPUT_VOLTAGE_NAME = 'V(vin)'
OUTPUT_VOLTAGE_NAME = 'V(vout)'

# Límite inferior de frecuencia para el gráfico (1 Hz = 0.001 kHz).
MIN_FREQ_PLOT_START_KHZ = 0.001

# --- Funciones de Utilidad ---

def identify_filter_type_and_fo(frequencies_hz, magnitudes_db):
    """
    Identifica el tipo de filtro y calcula su frecuencia característica (Fo).
    """
    num_points = len(magnitudes_db)
    # Considera el 5% inicial y final de los puntos para evaluar los extremos.
    # Mínimo 10 puntos para un promedio robusto.
    num_edge_points = max(10, int(num_points * 0.05))

    # Magnitudes promedio en los extremos del espectro.
    mag_low_freq = np.mean(magnitudes_db[:num_edge_points])
    mag_high_freq = np.mean(magnitudes_db[-num_edge_points:])

    # La magnitud máxima general sirve como referencia para la banda de paso.
    ref_mag_db = np.max(magnitudes_db)

    # Umbrales para la detección de tipo de filtro.
    ATTENUATION_THRESHOLD_DB = -20 # Magnitud por debajo de este valor es considerada atenuada.
    PASS_BAND_TOLERANCE_DB = 3     # Tolerancia para considerar que está en la banda de paso.

    # 1. Intento de detección de filtro Notch (Anula-Banda):
    # Busca el mínimo global de la magnitud.
    fo_idx_notch = np.argmin(magnitudes_db)
    fo_notch_hz = frequencies_hz[fo_idx_notch]
    mag_at_fo_notch = magnitudes_db[fo_idx_notch]

    # Un Notch tiene un valle profundo y centrado.
    is_notch_candidate = (mag_at_fo_notch < (ref_mag_db - PASS_BAND_TOLERANCE_DB)) and \
                         (mag_at_fo_notch < ATTENUATION_THRESHOLD_DB) and \
                         (fo_idx_notch > num_edge_points) and \
                         (fo_idx_notch < (num_points - num_edge_points))

    if is_notch_candidate:
        return "Notch", fo_notch_hz, "Fo (Valle)"

    # 2. Detección de filtro Pasa-Bajos:
    # Alta en bajas frecuencias, atenuada en altas.
    is_low_pass = (mag_low_freq >= (ref_mag_db - PASS_BAND_TOLERANCE_DB)) and \
                  (mag_high_freq < (ref_mag_db - PASS_BAND_TOLERANCE_DB))

    if is_low_pass:
        # Frecuencia de corte (-3dB) respecto a la ganancia en DC.
        initial_gain_db = mag_low_freq
        idx_cutoff = np.where(magnitudes_db < (initial_gain_db - 3))[0]
        fo_hz = frequencies_hz[idx_cutoff[0]] if len(idx_cutoff) > 0 else frequencies_hz[-1]
        return "Pasa-Bajos", fo_hz, "Fo (-3dB)"

    # 3. Detección de filtro Pasa-Altos:
    # Atenuada en bajas frecuencias, alta en altas.
    is_high_pass = (mag_low_freq < (ref_mag_db - PASS_BAND_TOLERANCE_DB)) and \
                   (mag_high_freq >= (ref_mag_db - PASS_BAND_TOLERANCE_DB))

    if is_high_pass:
        # Frecuencia de corte (-3dB) respecto a la ganancia final.
        final_gain_db = mag_high_freq
        idx_cutoff = np.where(magnitudes_db > (final_gain_db - 3))[0]
        fo_hz = frequencies_hz[idx_cutoff[0]] if len(idx_cutoff) > 0 else frequencies_hz[0]
        return "Pasa-Altos", fo_hz, "Fo (-3dB)"

    # 4. Detección de filtro Pasa-Banda:
    # Atenuada en ambos extremos con un pico central.
    fo_idx_peak = np.argmax(magnitudes_db)
    fo_peak_hz = frequencies_hz[fo_idx_peak]
    mag_at_fo_peak = magnitudes_db[fo_idx_peak]

    is_band_pass = (mag_low_freq < (ref_mag_db - PASS_BAND_TOLERANCE_DB)) and \
                   (mag_high_freq < (ref_mag_db - PASS_BAND_TOLERANCE_DB)) and \
                   (mag_at_fo_peak > (ref_mag_db - PASS_BAND_TOLERANCE_DB)) and \
                   (fo_idx_peak > num_edge_points) and \
                   (fo_idx_peak < (num_points - num_edge_points))

    if is_band_pass:
        return "Pasa-Banda", fo_peak_hz, "Fo (Pico)"

    # Caso por defecto si no se identifica claramente.
    print("Advertencia: Tipo de filtro no identificado. Usando el pico/valle más prominente como Fo.")
    default_fo_idx = np.argmax(magnitudes_db) # Por defecto, busco el pico
    default_fo_hz = frequencies_hz[default_fo_idx]
    return "Desconocido", default_fo_hz, "Fo (Pico/Valle)"

# --- Carga y Procesamiento de Datos ---
# Carga y parsea el archivo .raw de LTspice.
l = ltspice.Ltspice(RAW_FILE)
l.parse()

# Extrae las frecuencias y los datos de tensión.
frequencies_hz = l.get_frequency()
vin_data = l.get_data(INPUT_VOLTAGE_NAME)
vout_data = l.get_data(OUTPUT_VOLTAGE_NAME)

# Calcula la magnitud en dB y la fase en grados.
magnitudes_db = 20 * np.log10(np.abs(vout_data / vin_data))
phases_degrees = np.unwrap(np.angle(vout_data / vin_data)) * 180 / np.pi

# --- Detección de Frecuencia Característica y Tipo de Filtro ---
# Llama a la función para identificar el filtro y su Fo.
filter_type, fo_hz, fo_label = identify_filter_type_and_fo(frequencies_hz, magnitudes_db)
fo_khz = fo_hz / 1000

print(f"Tipo de filtro detectado: {filter_type}")
print(f"{fo_label} = {fo_khz:.2f} kHz")

# --- Preparación de Datos para el Gráfico ---
frequencies_khz = frequencies_hz / 1000
min_freq_sim_khz = np.min(frequencies_khz)
max_freq_sim_khz = np.max(frequencies_khz)

# Define las posiciones de los ticks del eje X alrededor de Fo.
decades = [-2, -1, 0, 1, 2] # Para Fo/100, Fo/10, Fo, 10*Fo, 100*Fo
tick_positions_khz = [fo_khz * (10 ** d) for d in decades]

# Genera las etiquetas numéricas para los ticks del eje X.
tick_labels = []
for val in tick_positions_khz:
    if 0.1 <= val <= 10000: # Formato decimal para rangos comunes.
        tick_labels.append(f'{val:.2f}')
    else: # Notación científica para valores extremos.
        tick_labels.append(f'{val:.1e}')

# Filtra los ticks para mostrar solo los que están dentro del rango simulado.
filtered_ticks_data = [(val, lbl) for val, lbl in zip(tick_positions_khz, tick_labels)
                       if min_freq_sim_khz <= val <= max_freq_sim_khz]

custom_ticks = [val for val, _ in filtered_ticks_data]
custom_tick_labels = [lbl for _, lbl in filtered_ticks_data]

# Establece los límites del eje X del gráfico.
x_min_bound = max(min_freq_sim_khz, MIN_FREQ_PLOT_START_KHZ)
x_max_bound = max(max_freq_sim_khz, custom_ticks[-1]) if custom_ticks else max_freq_sim_khz

# --- Generación de los Gráficos de Bode ---
plt.figure(figsize=(12, 10))

# --- Subgráfico de Magnitud ---
plt.subplot(2, 1, 1) # Divide la figura en 2 filas, 1 columna, y selecciona el primer subgráfico.
plt.semilogx(frequencies_khz, magnitudes_db)
plt.title(f'Diagrama de Bode (Magnitud) - Filtro {filter_type} (Simulación LTspice)')
plt.ylabel('Magnitud (dB)')
plt.grid(which='both', axis='both', ls='--', lw=0.6) # Rejilla para facilitar la lectura.
plt.axvline(x=fo_khz, color='r', linestyle='--', label=f'{fo_label} = {fo_khz:.2f} kHz') # Línea de Fo.
plt.legend(loc='lower left')
plt.xticks(custom_ticks, labels=custom_tick_labels) # Aplica los ticks y etiquetas personalizados.
plt.xlim(x_min_bound, x_max_bound) # Define los límites del eje X.

# --- Subgráfico de Fase ---
plt.subplot(2, 1, 2) # Selecciona el segundo subgráfico.
plt.semilogx(frequencies_khz, phases_degrees)
plt.xlabel('Frecuencia (kHz)')
plt.ylabel('Fase (grados)')
plt.grid(which='both', axis='both', ls='--', lw=0.6)
plt.axvline(x=fo_khz, color='r', linestyle='--', label=f'{fo_label} = {fo_khz:.2f} kHz')
plt.legend(loc='lower left')
plt.xticks(custom_ticks, labels=custom_tick_labels)
plt.xlim(x_min_bound, x_max_bound)
plt.yticks(np.arange(-180, 46, 45)) # Ticks de fase en incrementos de 45 grados.

# Ajusta el layout para evitar superposiciones de elementos.
plt.tight_layout()
plt.show() # Muestra los gráficos.