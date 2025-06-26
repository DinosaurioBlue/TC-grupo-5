import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# 1) Utilidad para generar polinomios a partir de raíces + ganancia
# ---------------------------------------------------------------------------
def from_zeros_poles_gain(zeros, poles, k=1):
    """
    Devuelve (num, den) dado:
        zeros : lista de ceros (raíces del numerador)
        poles : lista de polos (raíces del denominador)
        k     : ganancia (float)
    """
    num = k * np.poly(zeros)   # np.poly convierte raíces → coeficientes
    den = np.poly(poles)
    return num, den

# ---------------------------------------------------------------------------
# 2) Bode Analysis genérico
# ---------------------------------------------------------------------------
def bode_analysis(num, den, *,
                  w_min=0.1, w_max=1e3, n_points=1000,
                  mag_ylim=None, phase_ylim=None,
                  w_eval=None):
    """
    Traza Bode y devuelve métricas.
    Parámetros clave:
        num, den         : coef. polinomiales (orden descendente)
        w_min, w_max     : rango de frecuencia (rad/s)
        w_eval (list)    : frecuencias [rad/s] para evaluar H(jw) puntualmente
    """
    # ---- Polos y ceros -----------------------------------------------------
    zeros = np.roots(num)
    poles = np.roots(den)
    n_z, n_p = len(zeros), len(poles)

    # ---- Mallado logarítmico de frecuencia ---------------------------------
    w = np.logspace(np.log10(w_min), np.log10(w_max), n_points)
    s = 1j * w

    # Evaluación de polinomios (evita importar control)
    def polyval(c, sval):
        res = 0
        for coeff in c:
            res = res * sval + coeff
        return res

    eps = 1e-20
    H = polyval(num, s) / (polyval(den, s) + eps)
    mag_db   = 20 * np.log10(np.maximum(np.abs(H), eps))
    phase_deg = np.unwrap(np.angle(H)) * 180 / np.pi

    # ---- Ganancia DC (s = 0) ----------------------------------------------
    H_dc = polyval(num, 0) / polyval(den, 0)
    H_dc_db = 20 * np.log10(abs(H_dc) + eps)

    # ---- Alta frecuencia (ω → ∞) ------------------------------------------
    slope_hf  = (n_z - n_p) * 20         # dB/década
    phase_hf  = (n_z - n_p) * 90         # grados

    # ---- Pico de magnitud dentro del rango --------------------------------
    idx_peak       = np.argmax(mag_db)
    peak_mag_db    = mag_db[idx_peak]
    peak_mag_w     = w[idx_peak]

    # ---- Evaluación opcional en w_eval ------------------------------------
    eval_table = {}
    if w_eval is not None:
        for w0 in w_eval:
            Hj = polyval(num, 1j * w0) / polyval(den, 1j * w0)
            eval_table[w0] = {
                "mag_db": 20 * np.log10(abs(Hj) + eps),
                "phase_deg": np.angle(Hj, deg=True)
            }

    # ---- GRÁFICAS ----------------------------------------------------------
    plt.figure()
    plt.semilogx(w, mag_db)
    plt.title("Bode Magnitude")
    plt.xlabel("ω [rad/s]"); plt.ylabel("|H(jω)| [dB]")
    plt.grid(True, which="both")
    if mag_ylim: plt.ylim(mag_ylim)
    plt.tight_layout()

    plt.figure()
    plt.semilogx(w, phase_deg)
    plt.title("Bode Phase")
    plt.xlabel("ω [rad/s]"); plt.ylabel("Phase [°]")
    plt.grid(True, which="both")
    if phase_ylim: plt.ylim(phase_ylim)
    plt.tight_layout()

    plt.show()

    # ---- Advertencia polos en el origen -----------------------------------
    if np.any(np.isclose(poles, 0)):
        print("⚠️  Al menos un polo en el origen → fase fija −90° por polo.")

    # ---- Resumen devuelto --------------------------------------------------
    return dict(
        zeros=zeros,
        poles=poles,
        H_dc=H_dc,
        H_dc_db=H_dc_db,
        slope_hf=slope_hf,
        phase_hf=phase_hf,
        peak_mag_db=peak_mag_db,
        peak_mag_w=peak_mag_w,
        eval_table=eval_table
    )

# ---------------------------------------------------------------------------
# 3) Ejemplo de uso ----------------------------------------------------------
#    H(s) = 5(s+1)(s+3)(s+5) / (s+2)(s+4)(s+7)(s+9)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    zeros = [-1, -3, -5]
    poles = [-2, -4, -7, -9]
    k = 5
    num, den = from_zeros_poles_gain(zeros, poles, k)

    info = bode_analysis(num, den,
                         w_min=0.05, w_max=20000,
                         mag_ylim=(-60, 20),
                         phase_ylim=(-270, 90),
                         w_eval=[1, 10])

    # ---- Imprime resultados clave ----------------------------------------
    print("\n=== Resultados ===")
    print("Zeros :", np.round(info['zeros'], 3))
    print("Poles :", np.round(info['poles'], 3))
    print(f"Ganancia DC : {info['H_dc']:.3g}  ({info['H_dc_db']:.2f} dB)")
    print(f"Pendiente HF: {info['slope_hf']} dB/déc")
    print(f"Fase HF     : {info['phase_hf']}°")
    print(f"Pico        : {info['peak_mag_db']:.2f} dB @ ω = {info['peak_mag_w']:.2f} rad/s")
    if info["eval_table"]:
        print("\n--- Evaluaciones puntuales ---")
        for w0, res in info["eval_table"].items():
            print(f"ω = {w0} rad/s → |H| = {res['mag_db']:.2f} dB, φ = {res['phase_deg']:.1f}°")
