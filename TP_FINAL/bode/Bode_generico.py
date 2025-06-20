import numpy as np
import matplotlib.pyplot as plt

def bode_analysis(num, den, w_min=0.1, w_max=100, n_points=1000,
                  mag_ylim=None, phase_ylim=None):
    """Bode genérico para cualquier H(s)=N(s)/D(s)."""
    zeros = np.roots(num)
    poles = np.roots(den)

    w = np.logspace(np.log10(w_min), np.log10(w_max), n_points)
    s = 1j * w

    def polyval(coeffs, s_val):
        res = 0
        for c in coeffs:
            res = res * s_val + c
        return res

    H = polyval(num, s) / polyval(den, s)
    mag_db = 20 * np.log10(np.abs(H))
    phase_deg = np.unwrap(np.angle(H)) * 180 / np.pi

    idx_peak = np.argmax(mag_db)
    peak_mag_db = mag_db[idx_peak]
    peak_w = w[idx_peak]

    # Magnitud
    plt.figure()
    plt.semilogx(w, mag_db)
    plt.xlabel('ω (rad/s)'); plt.ylabel('|H(jω)| [dB]')
    plt.title('Bode Magnitude'); plt.grid(True, which='both')
    if mag_ylim is not None: plt.ylim(mag_ylim)
    plt.tight_layout()

    # Fase
    plt.figure()
    plt.semilogx(w, phase_deg)
    plt.xlabel('ω (rad/s)'); plt.ylabel('Phase [°]')
    plt.title('Bode Phase'); plt.grid(True, which='both')
    if phase_ylim is not None: plt.ylim(phase_ylim)
    plt.tight_layout()

    plt.show()

    return {
        "zeros": zeros,
        "poles": poles,
        "peak_mag_db": peak_mag_db,
        "peak_w": peak_w
}

# ---------- Ejemplo rápido --------------
num = [10, 10]     # Numerador 10s + 10
den = [1, 7, 10]   # Denominador s² + 7s + 10

info = bode_analysis(num, den,
                     w_min=0.05, w_max=200,
                     mag_ylim=(-25, 10),
                     phase_ylim=(-110, 20))

print("Zeros :", info['zeros'])
print("Poles :", info['poles'])
print(f"Peak  : {info['peak_mag_db']:.2f} dB @ ω = {info['peak_w']:.2f} rad/s")
