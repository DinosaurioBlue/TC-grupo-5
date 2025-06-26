import numpy as np
import matplotlib.pyplot as plt
import control as ct

# Parámetros del circuito RLC (Grupo 5)
C = 47e-9  # Capacitancia (F)
R = 50     # Resistencia (Ohm)
L = 1e-3   # Inductancia (H)

# Frecuencia de resonancia
Wo = 1 / np.sqrt(L * C)  # Angular (rad/s)
Fo = Wo / (2 * np.pi)    # En Hz

print(f"Frecuencia de Resonancia Angular (Wo) = {Wo:.2f} rad/s")
print(f"Frecuencia de Resonancia (Fo) = {Fo:.2f} Hz")

# Denominador común para todos los filtros RLC serie
den_RLC_serie = [1, R / L, 1 / (L * C)]

# Factor de escala para convertir rad/s a KHz para los ejes del plano s
# s = j*omega; f = omega / (2*pi); 1 KHz = 1000 Hz
rads_to_kHz_factor = 1 / (2 * np.pi * 1e3)

def analizar_circuito(num, den, titulo_filtro, figura_num, mostrar_bode=True, mostrar_pzmap=True):
    """
    Analiza un circuito dado por su función de transferencia,
    generando diagramas de Bode y/o de polos y ceros.
    """
    sys = ct.tf(num, den)

    print(f"\n--- Análisis del Circuito {figura_num} ({titulo_filtro}) ---")
    print("Función de Transferencia:")
    print(sys)

    # Obtener polos y ceros para cálculos y gráficos
    polos = ct.poles(sys)
    ceros = ct.zeros(sys)

    # Inicializar parámetros del sistema de segundo orden
    wn = None
    zeta = None
    Q = None
    bandwidth = None
    f_c1 = None
    f_c2 = None
    
    # Intenta calcular parámetros usando ct.damp primero
    if len(polos) == 2:
        try:
            wn_all_damp, zeta_all_damp, _ = ct.damp(sys, plot=False)
            
            print(f"DEBUG: ct.damp() salida para {titulo_filtro}: wn_all={wn_all_damp}, zeta_all={zeta_all_damp}")

            valid_indices_damp = ~np.isnan(zeta_all_damp)
            if np.any(valid_indices_damp):
                # Tomar el primer wn y zeta válido. Para sistemas RLC serie, suelen ser los mismos para ambos polos.
                wn = wn_all_damp[valid_indices_damp][0]
                zeta = zeta_all_damp[valid_indices_damp][0]
                print(f"DEBUG: Zeta de ct.damp: {zeta}")
            else:
                print(f"DEBUG: ct.damp no encontró zeta válido (no-NaN) para {titulo_filtro}.")

        except Exception as e:
            print(f"DEBUG: Error con ct.damp para {titulo_filtro}: {e}")
            pass # wn y zeta permanecen None si damp falla

        # Fallback: Cálculo manual de zeta y wn desde los polos si ct.damp falló o retornó None
        # Esto es especialmente útil para sistemas de 2do orden con polos complejos conjugados
        if zeta is None and len(polos) == 2:
            p1 = polos[0] # Tomamos el primer polo para el cálculo
            
            # Asumimos polos complejos conjugados para este tipo de filtros RLC de 2do orden
            if p1.imag != 0: # Si tiene componente imaginaria, asumimos polos complejos conjugados
                sigma = -p1.real # Parte real (amortiguamiento)
                omega_d = np.abs(p1.imag) # Frecuencia amortiguada
                
                wn_manual = np.sqrt(sigma**2 + omega_d**2)
                zeta_manual = sigma / wn_manual
                
                # Validación básica para evitar valores inválidos de la división
                if not np.isclose(wn_manual, 0) and not np.isnan(zeta_manual) and not np.isinf(zeta_manual) and zeta_manual >= 0:
                    wn = wn_manual
                    zeta = zeta_manual
                    print(f"DEBUG: Zeta calculado manualmente desde polos: {zeta_manual}")
                else:
                    print(f"DEBUG: El cálculo manual de zeta resultó en un valor inválido para {titulo_filtro}.")
            else: # Polos reales (sistema sobreamortiguado o críticamente amortiguado)
                # Para polos reales, ct.damp debería ser robusto. Si falla aquí, se complica el cálculo manual generalizado.
                # Dejamos que los parámetros sean None si ct.damp falló para este caso.
                print(f"DEBUG: Polos reales detectados para {titulo_filtro}. El cálculo manual de zeta para polos reales es más complejo y se basó en que ct.damp lo manejara.")

    # Continuar con los cálculos de Q, BW, Fc si zeta finalmente está disponible
    if zeta is not None:
        # Asegurarse de que zeta no sea demasiado pequeño o cero para evitar Q infinito/muy grande.
        # Si zeta es muy cercano a cero, puede ser numéricamente inestable para 1/(2*zeta)
        if np.isclose(zeta, 0):
            Q = np.inf
        else:
            Q = 1 / (2 * zeta)

        if Q is not np.inf and Q > 0: # Solo si Q es un valor finito y positivo
            bandwidth = Fo / Q 
            
            # Frecuencias de corte. Usar la formula basada en Fo y Q para filtros de 2do orden.
            # Esta fórmula asume la frecuencia de resonancia Fo y el factor de calidad Q.
            sqrt_term = np.sqrt(1 + 1 / (4 * Q**2))
            f_c1 = Fo * (sqrt_term - 1 / (2 * Q))
            f_c2 = Fo * (sqrt_term + 1 / (2 * Q))
        else:
            print(f"DEBUG: Q es infinito o no positivo después de la determinación de zeta para {titulo_filtro}. No se calculan BW y Frec. Corte.")
    else:
        print(f"DEBUG: Zeta es None para {titulo_filtro}, por lo que Q, BW y Frec. Corte no se calcularon.")

    # --- IMPRESIONES DE DEPURACIÓN EN TERMINAL (Solicitado por el usuario) ---
    print(f"DEBUG: Polos: {polos}")
    print(f"DEBUG: Ceros: {ceros}")
    
    tolerancia_estabilidad = 1e-9 
    if np.all(np.real(polos) <= tolerancia_estabilidad):
        print("DEBUG: El sistema es estable (polos en el semiplano izquierdo o sobre el eje imaginario).")
    else:
        print("DEBUG: El sistema es inestable (polo(s) en el semiplano derecho).")

    if len(polos) == 2 and zeta is not None:
        print(f"DEBUG: Frecuencia Natural No Amortiguada (Wo, del den): {Wo:.2f} rad/s") # Wo es el calculado del RLC den
        print(f"DEBUG: Frecuencia Natural No Amortiguada (Fo, del den): {Fo:.2f} Hz")
        print(f"DEBUG: Frecuencia Natural (wn, de los polos): {wn:.2f} rad/s")
        print(f"DEBUG: Factor de Amortiguamiento (Zeta, $\\zeta$): {zeta:.4f}") # Aumentar precisión para debug
        
        if Q is not None:
            print(f"DEBUG: Factor de Calidad (Q): {Q:.2f}")
        if bandwidth is not None:
            print(f"DEBUG: Ancho de Banda (BW): {bandwidth:.2f} Hz ({bandwidth / 1e3:.2f} kHz)")
        if f_c1 is not None and f_c2 is not None:
            print(f"DEBUG: Frecuencias de Corte (-3dB): {f_c1:.2f} Hz ({f_c1 / 1e3:.2f} kHz), {f_c2:.2f} Hz ({f_c2 / 1e3:.2f} kHz)")
        elif f_c1 is not None:
            print(f"DEBUG: Frecuencia de Corte (-3dB): {f_c1:.2f} Hz ({f_c1 / 1e3:.2f} kHz)")
        
        if zeta > 1:
            print("DEBUG: Tipo de Amortiguamiento: Sobreamortiguado")
        elif zeta == 1:
            print("DEBUG: Tipo de Amortiguamiento: Críticamente Amortiguado")
        elif zeta < 1 and zeta >= 0:
            print("DEBUG: Tipo de Amortiguamiento: Subamortiguado")
        else: # zeta < 0
            print("DEBUG: Tipo de Amortiguamiento: Inestable (zeta negativo)")
    elif len(polos) != 2:
        print("DEBUG: Cálculo de Q, BW, Zeta y frecuencias de corte solo disponible para sistemas de segundo orden (2 polos).")
    else:
        print("DEBUG: No se pudieron calcular la frecuencia natural y el factor de amortiguamiento para este sistema (zeta es None).")

    # --- Fin de Impresiones de Depuración ---

    if mostrar_bode:
        plt.figure(figsize=(12, 8))

        # Rango de frecuencias para el Bode
        omega_min = 0.01 * Wo
        omega_max = 100 * Wo
        omega_plot = np.logspace(np.log10(omega_min), np.log10(omega_max), 500)

        # Más puntos para la muesca del filtro Rechaza-Banda (Figura 5)
        if figura_num == 5:
            omega_notch_start = Wo * 0.999
            omega_notch_end = Wo * 1.001
            omega_notch_dense = np.logspace(np.log10(omega_notch_start), np.log10(omega_notch_end), 500)
            omega_plot = np.sort(np.unique(np.concatenate((omega_plot, omega_notch_dense))))
        
        # Escala a kHz para los gráficos
        scale_factor = 1e3 # Hz a kHz
        freq_unit = "kHz"
        f_plot_scaled = (omega_plot / (2 * np.pi)) / scale_factor
        Fo_scaled = Fo / scale_factor

        # Respuesta en frecuencia
        response = ct.frequency_response(sys, omega_plot)
        mag_complex = response.fresp[0, 0, :]

        # Magnitud en dB y fase en grados
        mag_db = 20 * np.log10(np.maximum(np.abs(mag_complex), 1e-15))
        phase_deg = np.unwrap(np.angle(mag_complex)) * 180 / np.pi

        # Bode de Magnitud
        plt.subplot(2, 1, 1)
        plt.semilogx(f_plot_scaled, mag_db)
        plt.title(f'Diagrama de Bode (Magnitud) - Circuito {figura_num}: {titulo_filtro}')
        plt.ylabel('Magnitud (dB)')
        plt.grid(True, which="both", ls="-")
        
        if figura_num == 5: # Ajuste de límite para el filtro Notch
            plt.ylim([-100, 10]) 
        else:
            plt.ylim([-40, 40]) 

        # Marcar Fo en el eje X
        plt.axvline(x=Fo_scaled, color='r', linestyle='--', label=f'Fo = {Fo_scaled:.2f} {freq_unit}')
        plt.legend()
        
        # Ticks personalizados en kHz
        ticks_locs_hz_base = np.array([0.01 * Fo, 0.1 * Fo, Fo, 10 * Fo, 100 * Fo])
        ticks_locs_scaled = ticks_locs_hz_base / scale_factor
        ticks_labels_scaled = [f'{t:.2f}' for t in ticks_locs_scaled]

        min_f_scaled = (omega_min / (2*np.pi)) / scale_factor
        max_f_scaled = (omega_max / (2*np.pi)) / scale_factor
        
        valid_ticks_locs_scaled = [t for t in ticks_locs_scaled if min_f_scaled <= t <= max_f_scaled]
        valid_ticks_labels_scaled = [ticks_labels_scaled[i] for i, t in enumerate(ticks_locs_scaled) if min_f_scaled <= t <= max_f_scaled]
        
        if valid_ticks_locs_scaled:
            plt.xticks(ticks=valid_ticks_locs_scaled, labels=valid_ticks_labels_scaled)
        
        plt.xlabel(f'Frecuencia ({freq_unit})') 
        
        # Bode de Fase
        plt.subplot(2, 1, 2)
        plt.semilogx(f_plot_scaled, phase_deg)
        plt.title(f'Diagrama de Bode (Fase) - Circuito {figura_num}: {titulo_filtro}')
        plt.ylabel('Fase (grados)')
        plt.xlabel(f'Frecuencia ({freq_unit})')
        plt.grid(True, which="both", ls="-")

        # Marcar Fo en el eje X
        plt.axvline(x=Fo_scaled, color='r', linestyle='--', label=f'Fo = {Fo_scaled:.2f} {freq_unit}')
        plt.legend()
        if valid_ticks_locs_scaled:
            plt.xticks(ticks=valid_ticks_locs_scaled, labels=valid_ticks_labels_scaled)
            
        # Ticks y límites para el eje Y de la fase
        phase_ticks = np.arange(-180, 181, 45) 
        plt.yticks(phase_ticks)
        plt.ylim([np.min(phase_deg) - 10, np.max(phase_deg) + 10]) 

        plt.tight_layout(rect=[0, 0.03, 1, 0.98])
        plt.show()

    # Diagrama de Polos y Ceros
    if mostrar_pzmap:
        plt.figure(figsize=(8, 8))
        ax = plt.gca()

        # Ajustar límites del plot
        plot_limit = Wo * 1.5 
        
        all_points_real = np.real(np.concatenate((polos, ceros)))
        all_points_imag = np.imag(np.concatenate((polos, ceros)))

        if len(all_points_real) > 0 and len(all_points_imag) > 0:
            # Convertir los valores para ajustar el límite del plot a kHz
            max_abs_real_kHz = np.max(np.abs(all_points_real)) * rads_to_kHz_factor
            max_abs_imag_kHz = np.max(np.abs(all_points_imag)) * rads_to_kHz_factor
            plot_limit_kHz = max(Wo * rads_to_kHz_factor * 1.5, max_abs_real_kHz * 1.2, max_abs_imag_kHz * 1.2, 1e-3) 
        else:
            plot_limit_kHz = Wo * rads_to_kHz_factor * 1.5 # Valor por defecto en kHz
            
        ax.set_xlim([-plot_limit_kHz, plot_limit_kHz])
        ax.set_ylim([-plot_limit_kHz, plot_limit_kHz])
        ax.set_aspect('equal', adjustable='box') 
        plt.grid(True)

        # 1. Dibujar ejes X e Y en negrita
        ax.axhline(0, color='black', linewidth=1.5, linestyle='-', zorder=1)
        ax.axvline(0, color='black', linewidth=1.5, linestyle='-', zorder=1)

        # 2. Dibujar círculo de Wo
        # El radio del círculo se dibuja en las unidades del eje (KHz)
        circle = plt.Circle((0, 0), Wo * rads_to_kHz_factor, color='blue', linestyle='--', fill=False, zorder=2)
        ax.add_patch(circle)
        
        # 3. Graficar polos y ceros manualmente con sus valores numéricos en KHz
        legend_handles = [] # Para construir la leyenda
        
        # Polos
        if len(polos) > 0:
            legend_handles.append(plt.Line2D([0], [0], marker='x', color='red', linestyle='None', markersize=10, mew=2, label='Polos'))
            for p in polos:
                p_real_kHz = p.real * rads_to_kHz_factor
                p_imag_kHz = p.imag * rads_to_kHz_factor
                ax.plot(p_real_kHz, p_imag_kHz, 'x', markersize=10, color='red', mew=2, zorder=3)
                
                # Formato binomial sin exponencial
                if p_imag_kHz >= 0:
                    text_str = f'({p_real_kHz:.2f} + j {p_imag_kHz:.2f}) KHz'
                else:
                    text_str = f'({p_real_kHz:.2f} - j {np.abs(p_imag_kHz):.2f}) KHz'

                # Colocar el texto del polo ABAJO del marcador 'x'
                ax.text(p_real_kHz + 0.02 * plot_limit_kHz, p_imag_kHz - 0.02 * plot_limit_kHz, 
                        text_str, 
                        color='red', fontsize=8, ha='left', va='top', zorder=4)

        # Ceros
        if len(ceros) > 0:
            legend_handles.append(plt.Line2D([0], [0], marker='o', color='green', linestyle='None', markersize=10, mfc='none', mew=2, label='Ceros'))
            for z in ceros:
                z_real_kHz = z.real * rads_to_kHz_factor
                z_imag_kHz = z.imag * rads_to_kHz_factor
                ax.plot(z_real_kHz, z_imag_kHz, 'o', markersize=10, color='green', mfc='none', mew=2, zorder=3)
                
                # Formato binomial sin exponencial
                if z_imag_kHz >= 0:
                    text_str = f'({z_real_kHz:.2f} + j {z_imag_kHz:.2f}) KHz'
                else:
                    text_str = f'({z_real_kHz:.2f} - j {np.abs(z_imag_kHz):.2f}) KHz'

                # Colocar el texto del cero ARRIBA del marcador 'o'
                ax.text(z_real_kHz + 0.02 * plot_limit_kHz, z_imag_kHz + 0.02 * plot_limit_kHz, 
                        text_str, 
                        color='green', fontsize=8, ha='left', va='bottom', zorder=4)

        plt.title(f'Diagrama de Polos y Ceros - Circuito {figura_num}: {titulo_filtro}')
        plt.xlabel('Eje Real (KHz)')
        plt.ylabel('Eje Imaginario (KHz)')
        
        plt.legend(handles=legend_handles, loc='upper right')

        # Bloque de texto con parámetros
        # Wo se convierte a KHz para mostrar en el texto
        param_text = f'Radio = Wo ({Wo * rads_to_kHz_factor:.2f} KHz)\n'
        
        # Construir la cadena solo si los parámetros están disponibles
        if Q is not None:
            param_text += f'Q = {Q:.2f}\n'
        if zeta is not None:
            param_text += f'$\\zeta$ = {zeta:.4f}\n' # Usar más decimales para Zeta en el gráfico
        if bandwidth is not None:
            param_text += f'BW = {bandwidth / 1e3:.2f} {freq_unit}\n'
        
        if f_c1 is not None and f_c2 is not None:
            param_text += f'Frec. Corte: {f_c1 / 1e3:.2f} {freq_unit}, {f_c2 / 1e3:.2f} {freq_unit}'
        elif f_c1 is not None:
            param_text += f'Frec. Corte: {f_c1 / 1e3:.2f} {freq_unit}'
        
        # Añadir el bloque de texto al gráfico en la esquina superior izquierda
        ax.text(0.02, 0.98, param_text, 
                transform=ax.transAxes, 
                fontsize=9, color='blue', ha='left', va='top', 
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.5'),
                zorder=5)

        plt.show()


# --- Definición y análisis de los filtros RLC ---

# Circuito 2: Pasa-Bajos
num2_pb = [1 / (L * C)]
analizar_circuito(num2_pb, den_RLC_serie, "Filtro Pasa-Bajos", 2, mostrar_bode=True, mostrar_pzmap=True)

# Circuito 3: Pasa-Altos
num3_pa = [1, 0, 0]
analizar_circuito(num3_pa, den_RLC_serie, "Filtro Pasa-Altos", 3, mostrar_bode=True, mostrar_pzmap=True)

# Circuito 4: Pasa-Banda
num4_pb = [R / L, 0]
analizar_circuito(num4_pb, den_RLC_serie, "Filtro Pasa-Banda", 4, mostrar_bode=True, mostrar_pzmap=True)

# Circuito 5: Rechaza-Banda
num5_rb = [1, 0, 1 / (L * C)]
analizar_circuito(num5_rb, den_RLC_serie, "Filtro Rechaza-Banda", 5, mostrar_bode=True, mostrar_pzmap=True)