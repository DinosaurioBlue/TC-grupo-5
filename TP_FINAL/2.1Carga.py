"""
Carga del circuito con C-R2 y L-R3 en paralelo (ver figura adjunta).

Ecuaciones:
    dvC/dt = (Vi - vC - R1*iL)/( C * (R1 + R2) )
    diL/dt = ( vC - (R1*R2 + R3*(R1+R2))*iL )/( L*(R1+R2) ) + R2*Vi/( L*(R1+R2) )
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

# ───────── PARÁMETROS ─────────
Vi  = 10.0                      # V
R1, R2, R3 = 50.0, 7.0, 6.0     # Ω
C   = 82e-9                     # F
L   = 1e-3                      # H

# ─────── SISTEMA DE EDOs ──────
def f(t, x):
    vC, iL = x
    dvC = (Vi - vC - R1*iL) / (C*(R1 + R2))
    diL = (vC - (R1*R2 + R3*(R1 + R2))*iL) / (L*(R1 + R2)) \
          + R2*Vi / (L*(R1 + R2))
    return [dvC, diL]

# ─── INTEGRACIÓN NUMÉRICA ───
t_end = 5e-3                    # 5 ms (ventana completa de carga)
sol = solve_ivp(
        f, (0.0, t_end),
        y0=[0.0, 0.0],          # vC(0)=0, iL(0)=0
        max_step=1e-7,          # 100 ns  → > 100 puntos por periodo
        rtol=1e-9, atol=1e-12)

t   = sol.t
vC  = sol.y[0]
iL  = sol.y[1]

# Corrientes y tensiones derivadas
iC  = C * np.gradient(vC, t, edge_order=2)   # i_C = C·dvC/dt
vL  = L * np.gradient(iL, t, edge_order=2)   # v_L = L·diL/dt

# ────────── GRÁFICOS ──────────
plt.figure(figsize=(9,4))
plt.plot(t*1e3, vC, label='v_C [V]')
plt.plot(t*1e3, iC, label='i_C [A]')
plt.plot(t*1e3, vL, label='v_L [V]')
plt.xlabel('tiempo [ms]')
plt.title('Carga del circuito')
plt.grid(True); plt.legend(); plt.tight_layout(); plt.show()

# ────────── CHEQUEO INICIAL ──────────
iC0_teor = Vi / (R1 + R2)           # I_C(0+) = V_i / (R1+R2)
vL0_teor = 0.0                      # L abierto → vL(0+)=0
print(f"i_C(0+) numérico  : {iC[0]: .5f} A")
print(f"i_C(0+) analítico : {iC0_teor: .5f} A")
print(f"v_L(0+) numérico  : {vL[0]: .5f} V")
print(f"v_L(0+) analítico : {vL0_teor: .5f} V")
