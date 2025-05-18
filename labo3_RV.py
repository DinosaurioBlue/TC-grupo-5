import numpy as np

# Parámetros del circuito
L = 0.430      # H
C = 10e-9      # F
Rf = 2200      # Ohm

# Valores de X (multiplicador de omega_0)
X_vals = [0.5, 1, 2]
omega_0 = 1 / np.sqrt(L * C)  # Frecuencia natural no amortiguada

# Cálculos
for X in X_vals:
    alpha = X * omega_0
    Rv = 2 * L * alpha - Rf
    print(f"X = {X}")
    print(f"  ω₀ = {omega_0:.2f} rad/s")
    print(f"  α  = {alpha:.2f} 1/s")
    print(f"  Rv = {Rv:.2f} Ω\n")

