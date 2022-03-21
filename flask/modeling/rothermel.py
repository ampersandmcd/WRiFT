####################################
####################################
####################################
##### Equations for Rothermel Surface Spread
##### source: https://www.fs.fed.us/rm/pubs_series/rmrs/gtr/rmrs_gtr371.pdf
#####
##### Here we implement the basic, static fuel model Rothermel variation
#####

import numpy as np
from numba import jit

################################################
############ Rothermel Surface Spread EQs
################################################


@jit(nopython=True, fastmath=True)
def eq_A(sigma):
    """
    :param sigma: Surface-area-to-volume ratio (ft2/ft3)
    :return: A: A
    """
    return 113 * (sigma ** -0.7913)

@jit(nopython=True, fastmath=True)
def eq_r_M(M_f, M_x):
    """
    :param M_f: Moisture content (fraction)
    :param M_x: Dead fuel moisture of extinction (fraction)
    :return: r_M: r_M
    """
    return min(M_f / M_x, 1)

@jit(nopython=True, fastmath=True)
def eq_12(M_f):
    """
    :param M_f: Moisture content (fraction)
    :return: Q_ig: heat of pre-ignition (Kj/Kg)
    """
    return 250 + 1116 * M_f

@jit(nopython=True, fastmath=True)
def eq_14(sigma):
    """
    :param sigma: Surface-area-to-volume ratio (ft2/ft3)
    :return: epsilon: effective heating number, dimensionless
    """
    return np.exp(-138 / sigma)

@jit(nopython=True, fastmath=True)
def eq_24(w_0, S_T=0.0555):
    """
    :param w_0: Oven-dry fuel load (lb/ft2)
    :param S_T: Total mineral content, equal to 0.0555
    :return: w_n: Net fuel load (lb/ft^2)
    """
    return w_0 * (1 - S_T)

@jit(nopython=True, fastmath=True)
def eq_27(Gamma_prime, w_n, eta_M, eta_s, h=8000):
    """
    :param Gamma_prime: Optimum reaction velocity (min^-1)
    :param w_n: Net fuel load (lb/ft^2)
    :param h: Low heat content (Btu/lb) Often 8,000 Btu/lb
    :param eta_M: Moisture damping coefficient
    :param eta_s: Mineral damping coefficient
    :return: IR, Reacton Intensity (Kj/min/m^2)
    """
    return Gamma_prime * w_n * h * eta_M * eta_s

@jit(nopython=True, fastmath=True)
def eq_29(r_M):
    """
    :param r_M: r_M
    :return: eta_M: Moisture damping coefficient
    """
    return 1 - 2.59 * (r_M) + 5.11 * (r_M ** 2) - 3.52 * (r_M ** 3)

@jit(nopython=True, fastmath=True)
def eq_30(S_e=0.010):
    """
    :param S_e: Effective mineral content (fraction) Generally 0.010
    :return: eta_s: Mineral damping coefficient
    """
    return min(0.174 * (S_e ** -0.19), 1)

@jit(nopython=True, fastmath=True)
def eq_31(rho_b, rho_p=32):
    """
    :param rho_b: Oven-dry bulk density (lb/ft3)
    :param rho_p: Oven-dry particle density (lb/ft3), which is equal to 32
    :return: beta: Packing ratio
    """
    return rho_b / rho_p

@jit(nopython=True, fastmath=True)
def eq_36(sigma):
    """
    :param sigma: Surface-area-to-volume ratio (ft2/ft3)
    :return: Gamma_prime_max: Maximum reaction velocity (min^-1)
    """
    return (sigma ** 1.5) / (495 + 0.0594 * (sigma ** 1.5))

@jit(nopython=True, fastmath=True)
def eq_37(sigma):
    """
    :param sigma: Surface-area-to-volume ratio (ft2/ft3)
    :return: beta_op: Packing ratio optimum
    """
    return 3.348 * (sigma ** -0.8189)

@jit(nopython=True, fastmath=True)
def eq_38(Gamma_prime_max, beta, beta_op, A):
    """
    :param Gamma_prime_max: Maximum reaction velocity (min^-1)
    :param beta: Packing ratio
    :param beta_op: Packing ratio optimum
    :param A: A
    :return: Gamma_prime: Optimum reaction velocity (min^-1)
    """
    return Gamma_prime_max * (beta / beta_op) ** A * np.exp(A * (1 - beta / beta_op))

@jit(nopython=True, fastmath=True)
def eq_40(w_0, delta):
    """
    :param w_0: Oven-dry fuel load (lb/ft2)
    :param delta: Fuel bed depth (ft)
    :return: rho_b: Oven-dry bulk density (lb/ft3)
    """
    return w_0 / delta

@jit(nopython=True, fastmath=True)
def eq_42(sigma, beta):
    """
    :param sigma: Surface-area-to-volume ratio (ft2/ft3)
    :param beta: Packing ratio
    :return: xi: propogating flux ratio, unitless
    """
    return np.exp((0.792 + 0.681 * np.sqrt(sigma)) * (beta + 0.1)) / (192 + 0.2595 * sigma)

@jit(nopython=True, fastmath=True)
def eq_47(C, U, B, beta, beta_op, E):  # eq_12
    """
    :param C: Function of fuel partical size in fuel bed
    :param U: Wind velocity at midflame height (ft/min)
    :param B: Function of fuel partical size in fuel bed
    :param beta: packing ratio of fuel bed (from fuel type data)
    :param beta_op: optimum packing ratio
    :param E: Function of fuel partical size in fuel bed
    :return: Phi_w, dimensionless coefficient for midflame wind speed
    """
    CUB = C * (U ** B)
    return CUB * (beta / beta_op) ** (-E)

@jit(nopython=True, fastmath=True)
def eq_48(sigma):
    """
    :param sigma: Surface-area-to-volume ratio (ft2/ft3)
    :return: C: Function of fuel partical size in fuel bed
    """
    return 7.47 * np.exp(-.133 * (sigma ** 0.55))

@jit(nopython=True, fastmath=True)
def eq_49(sigma):
    """
    :param sigma: Surface-area-to-volume ratio (ft2/ft3)
    :return: B: Function of fuel partical size in fuel bed
    """
    return 0.02526 * (sigma ** 0.54)

@jit(nopython=True, fastmath=True)
def eq_50(sigma):
    """
    :param sigma: Surface-area-to-volume ratio (ft2/ft3)
    :return: E: Function of fuel partical size in fuel bed
    """
    return 0.715 * np.exp(-3.59 * (10 ** -4) * sigma)

@jit(nopython=True, fastmath=True)
def eq_51(beta, tan_phi):
    """
    :param beta: Packing ratio
    :param tan_phi: Slope steepness, maximum (fraction) Vertical rise / horizontal distance
    """
    return 5.275 * (beta ** -0.3) * (tan_phi ** 2)

@jit(nopython=True, fastmath=True)
def eq_52(IR, xi, rho_b, epsilon, Q_ig, Phi_w, Phi_s):  # eq_18
    """
    :param IR: Reacton Intensity (Kj/min/m^2)
    :param xi: propogating flux ratio, unitless
    :param rho_b: ovendry bulk density (kg/m^3)
    :param epsilon: effective heating number, dimensionless
    :param Q_ig: heat of pre-ignition (Kj/Kg)
    :param Phi_w: dimensionless coefficient for midflame wind speed, from eq_11
    :param Phi_s: dimensionless coefficient of slope, from eq_12
    :return: R, fire spread rate (m/min)
    """
    num = IR * xi * (1 + Phi_w + Phi_s)
    den = rho_b * epsilon * Q_ig
    return num / den

@jit(nopython=True, fastmath=True)
def compute_surface_spread(inputs, wind_speed):
    """
    Wraps all the above functions into one function, computing surface spread rate
    :param inputs: input array, explained below
    :param wind_speed: wind speed (ft/min)
    :return: R, fire spreadrate (m/min)
    """

    delta = inputs[0]  # Fuel bed depth (ft)
    sigma = inputs[1]  # Surface-area-to-volume ratio (ft2/ft3)
    w_0 = inputs[2]  # Oven-dry fuel load (lb/ft2)
    Mx = inputs[3]  # Extinction Moisture (portion of 1)
    Mf = inputs[4]  # Fuel Moisture (portion of 1)
    tan_phi = inputs[5]  # Slope steepness, maximum (fraction) Vertical rise / horizontal distance

    U = wind_speed

    C, B, E = eq_48(sigma), eq_49(sigma), eq_50(sigma)  # Fuel Partical Size Constants
    Q_ig = eq_12(Mf)  # Heat of pre-ignition (Kj/Kg)
    epsilon = eq_14(sigma)  # Effective heating number, dimensionless
    eta_s = eq_30()  # Mineral Damping Coefficient
    r_M = eq_r_M(Mf, Mx)  # Ratio Mf/Mx
    eta_M = eq_29(r_M)  # Moisture Damping Constant
    w_n = eq_24(w_0)  # Net Fuel Load lb/ft^2 (CACHE THIS?)
    A = eq_A(sigma)  # Some Constant
    beta_op = eq_37(sigma)  # Optimum Packing Ratio
    rho_b = eq_40(w_0, delta)  # Oven-dry bulk fuel density (lb/ft^3)
    beta = eq_31(rho_b)  # Packing Ratio
    Phi_s = eq_51(beta, tan_phi)  # Slope Steepness
    Phi_w = eq_47(C, U, B, beta, beta_op, E)  # coefficient for midflame wind speed
    xi = eq_42(sigma, beta)  # propogating flux ratio, unitless
    Gamma_prime_max = eq_36(sigma)  # Maximum reaction velocity (min^-1)
    Gamma_prime = eq_38(Gamma_prime_max, beta, beta_op, A)  # Optimum reaction velocity (min^-1)
    IR = eq_27(Gamma_prime, w_n, eta_M, eta_s)  # Reacton Intensity (Kj/min/m^2)
    R = eq_52(IR, xi, rho_b, epsilon, Q_ig, Phi_w, Phi_s)  # Rate of Fire Spread in Wind Dir (ft/min)

    return R
