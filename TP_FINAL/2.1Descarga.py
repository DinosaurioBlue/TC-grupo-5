"""
Descarga del circuito  R1-C-R2 // L-R3
(Pérdidas serie en C y L incluidas)

* Llave se abre en t = 0  →  fuente Vi queda aislada
* Se parte del estado final alcanzado al terminar la carga:
      V0 = vC(0+) ,  I0 = iL(0+)

Mejoras aplicadas respecto al borrador anterior
──────────────────────────────────────────────
1. Ventana temporal coherente con la etapa de carga  (t_end = 5 ms)
2. Paso máximo 50 ns  →  ≥ 100 puntos por período (f ≈ 18 kHz)
3. Derivada numérica con  `edge_order = 2`  (más precisa en t = 0)
4. Chequeo adicional de  vC(0+)  e  iC(0+)  frente a los valores analíticos
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

# ─────────────────────────
# 1) Parámetros de la red
# ─────────────────────────
Vi  = 10.0                     # V – valor de la fuente en la etapa de carga
R1, R2, R3 = 50.0, 7.0, 6.0    # Ω
C   = 82e-9                    # F
L   = 1e-3                     # H

# ─────────────────────────
# 2) Condiciones iniciales (fin de la carga)
# ─────────────────────────
V0 = Vi * R3 / (R1 + R3)       # vC(0+)  =  V_C(∞) etapa de carga
I0 = Vi / (R1 + R3)            # iL(0+)  =  I_L(∞) etapa de carga

# ─────────────────────────
# 3) Sistema de ecuaciones – descarga
# ─────────────────────────
def f(t: float, x: np.ndarray) -> list[float]:
    """x = [vC, iL]"""
    vC,  iL = x
    dvC = -iL / C
    diL = (vC - (R2 + R3) * iL) / L
    return [dvC, diL]

# ─────────────────────────
# 4) Integración numérica
# ─────────────────────────
t_end = 5e-3                    # 5 ms
sol = solve_ivp(
        f,
        (0.0, t_end),
        y0=[V0, I0],
        max_step=5e-8,          # 50 ns
        rtol=1e-9,
        atol=1e-12)

t   = sol.t
vC  = sol.y[0]
iL  = sol.y[1]
iC  = -iL                                       # KCL  iC + iL = 0
vL  = L * np.gradient(iL, t, edge_order=2)      # vL = L·diL/dt

# ─────────────────────────
# 5) Chequeo de consistencia en t = 0+
# ─────────────────────────
vL0_an = V0 - (R2 + R3) * I0    # expresión analítica  (-1.25 V)
print(f"vC(0+)  numérico : {vC[0]: .6f}  V   |  analítico : {V0: .6f}  V")
print(f"iC(0+)  numérico : {iC[0]: .6f}  A   |  analítico : {-I0: .6f}  A")
print(f"vL(0+)  numérico : {vL[0]: .6f}  V   |  analítico : {vL0_an: .6f}  V")

# ─────────────────────────
# 6) Gráficos
# ─────────────────────────
plt.figure(figsize=(9, 4))
plt.plot(t*1e3, vC, label='v_C(t)  [V]')
plt.plot(t*1e3, iC, label='i_C(t)  [A]')
plt.plot(t*1e3, vL, label='v_L(t)  [V]')
plt.xlabel('tiempo [ms]')
plt.title('Descarga del circuito — solución numérica refinada')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
