# ---------------------------------------------------------------
# Respuesta de un RLC serie (pulso 0 → 5 V) – tres amortiguamientos
# Autor: ChatGPT • mayo-2025
# ---------------------------------------------------------------

import numpy as np
import matplotlib.pyplot as plt

# === Parámetros que podés modificar =============================
t_max = 0.0018          # ventana de tiempo [s]  ← cambialo a gusto (p. ej. 0.02 = 20 ms)
n_puntos = 10_000     # densidad de puntos    ← bajalo si querés acelerar el dibujo
# ===============================================================

t = np.linspace(0, t_max, n_puntos)     # vector temporal

# ~~~ Ecuaciones de Uc(t) (extraídas de tu captura) ~~~
uc_sub   = np.exp(-7624.93 * t) * (-5 * np.cos(13206.77 * t) - 2.5 * np.sin(13206.77 * t)) + 5
uc_crit  = np.exp(-15249.86 * t) * (-5 - 76249.3 * t) + 5
uc_sobre = -5.39 * np.exp(-4086.19 * t) + 0.39 * np.exp(-56913.25 * t) + 5
pulso    = 5 * np.ones_like(t)          # pulso ideal (0 → 5 V)

# ---------- Gráfico --------------------------------------------
plt.figure(figsize=(10, 6))

plt.plot(t * 1e3, uc_sub,   label='Sub-amortiguado',  linewidth=2)
plt.plot(t * 1e3, uc_crit,  label='Crítico',          linewidth=2)
plt.plot(t * 1e3, uc_sobre, label='Sobre-amortiguado',linewidth=2)
plt.plot(t * 1e3, pulso, '--', label='Pulso 0 → 5 V', linewidth=1.8)

plt.xlabel('Tiempo [ms]')
plt.ylabel('$u_C(t)$ [V]')
plt.title('Respuesta del capacitor en las tres condiciones de amortiguamiento\nRLC serie con pulso de 5 V')
plt.grid(True, which='both', linestyle=':')
plt.legend()
plt.tight_layout()
plt.show()
