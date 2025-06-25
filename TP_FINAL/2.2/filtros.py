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

def analizar_circuito(num, den, titulo_filtro, figura_num, mostrar_bode=True, mostrar_pzmap=True):
    """
    Analiza un circuito dado por su función de transferencia,
    generando diagramas de Bode y/o de polos y ceros.
    """
    sys = ct.tf(num, den)

    print(f"\n--- Análisis del Circuito {figura_num} ({titulo_filtro}) ---")
    print("Función de Transferencia:")
    print(sys)

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
        polos = ct.poles(sys)
        ceros = ct.zeros(sys)
        
        all_points_real = np.real(np.concatenate((polos, ceros)))
        all_points_imag = np.imag(np.concatenate((polos, ceros)))

        plot_limit = Wo * 1.5 
        if len(all_points_real) > 0 and len(all_points_imag) > 0:
            max_abs_real = np.max(np.abs(all_points_real))
            max_abs_imag = np.max(np.abs(all_points_imag))
            plot_limit = max(plot_limit, max_abs_real * 1.2, max_abs_imag * 1.2, 1e-3) 
            
        ax.set_xlim([-plot_limit, plot_limit])
        ax.set_ylim([-plot_limit, plot_limit])
        ax.set_aspect('equal', adjustable='box') 
        plt.grid(True)

        # Dibujar ejes X e Y en negrita
        ax.axhline(0, color='black', linewidth=1.5, linestyle='-', zorder=1)
        ax.axvline(0, color='black', linewidth=1.5, linestyle='-', zorder=1)

        # Dibujar círculo de Wo
        circle = plt.Circle((0, 0), Wo, color='blue', linestyle='--', fill=False, label=f'Radio = Wo ({Wo:.2e} rad/s)', zorder=2)
        ax.add_patch(circle)
        
        # Dibujar polos y ceros
        ct.pzmap(sys, plot=True, ax=ax)

        plt.title(f'Diagrama de Polos y Ceros - Circuito {figura_num}: {titulo_filtro}')
        plt.xlabel('Eje Real (rad/s)')
        plt.ylabel('Eje Imaginario (rad/s)')
        plt.legend() 
        plt.show()

    # Parámetros del sistema
    polos = ct.poles(sys)
    ceros = ct.zeros(sys)
    print(f"Polos: {polos}")
    print(f"Ceros: {ceros}")

    # Estabilidad
    tolerancia_estabilidad = 1e-9 
    if np.all(np.real(polos) <= tolerancia_estabilidad):
        print("El sistema es estable (polos en el semiplano izquierdo o sobre el eje imaginario).")
    else:
        print("El sistema es inestable (polo(s) en el semiplano derecho).")

    # Amortiguación y frecuencia natural (solo para segundo orden)
    if len(polos) == 2:
        try:
            wn_all, zeta_all, _ = ct.damp(sys, plot=False)
            
            if len(wn_all) > 0 and len(zeta_all) > 0:
                valid_indices = ~np.isnan(zeta_all)
                if np.any(valid_indices):
                    wn = wn_all[valid_indices][0]
                    zeta = zeta_all[valid_indices][0]

                    Q = 1 / (2 * zeta) if zeta != 0 else np.inf
                    print(f"Frecuencia Natural No Amortiguada (Sistema, Wo) = {wn:.2f} rad/s")
                    print(f"Frecuencia Natural No Amortiguada (Sistema, Fo) = {wn / (2 * np.pi):.2f} Hz")
                    print(f"Factor de Amortiguamiento (Zeta) = {zeta:.2f}")
                    print(f"Factor de Calidad (Q) = {Q:.2f}")

                    if zeta > 1:
                        print("Tipo de Amortiguamiento: Sobreamortiguado")
                    elif zeta == 1:
                        print("Tipo de Amortiguamiento: Críticamente Amortiguado")
                    elif zeta < 1 and zeta >= 0:
                        print("Tipo de Amortiguamiento: Subamortiguado")
                    else:
                        print("Tipo de Amortiguamiento: Inestable (zeta negativo)")
                else:
                    print("No se pudieron calcular la frecuencia natural y el factor de amortiguamiento válidos.")
            else:
                print("No se pudieron calcular la frecuencia natural y el factor de amortiguamiento para este sistema.")
        except Exception as e:
            print(f"Error al calcular wn, zeta, Q: {e}")
            print("Esto puede ocurrir si el sistema no es un sistema de segundo orden 'estándar'.")


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