####################################
####################################
####################################
##### Equations for Canopy Spread
##### source: https://www.fs.fed.us/rm/pubs/rmrs_rp004.pdf
#####
##### Static Canopy Spread Inspired by FARSITE
#####

import numpy as np
from numba import jit

################################################
############ Canopy Spread EQs
################################################


@jit(nopython=True, fastmath=True)
def eq_20(IR, R, sigma):
    """
    :param IR: Reaction Intensity (Kj/min/m^2)
    :param R: fire spread rate (m/min)
    :param sigma: surface area to volume ratio of fuel bed (m^-1)
    :return: Ib, fireline intensity (Kw/m)
    """
    return (IR/60)*(12.6*R/sigma)

@jit(nopython=True, fastmath=True)
def eq_21(CBH, M):
    """
    :param M: Crown foliar moisture constant (percentage)
    :param CBH: Height to Crown Base (m)
    :return: Io, threshold to transition to crown fire (Kw/m)
    """

@jit(nopython=True, fastmath=True)
def eq_22(CBD):
    """
    :param CBD: crown bulk density (Kg/m^3)
    :return: RAC, fire spread rate in crown (m/min)
    """
    return 3.0/CBD

@jit(nopython=True, fastmath=True)
def eq_23(R, CFB, R_Cmax):
    """
    :param R: Fire Spread Rate (m/min)
    :param CFB: Crown Fraction Burned
    :param R_Cmax: maximum crown fire spread rate (m/min)
    :return: R_Cactual, "actual" crown fire spread (m/min)
    """
    return R + CFB*(R_Cmax - R)

@jit(nopython=True, fastmath=True)
def feq_24(R_10, Ei):
    """
    :param R_10: Active crown fire spread rate (m/min)
    :param Ei: Fraction of forward crown fire spread rate at ith index
    :return: R_Cmax, maximum crown fire spread rate (m/min)
    """
    return 3.34*R_10*Ei

@jit(nopython=True, fastmath=True)
def feq_25(a_c, R, Ro):
    """
    :param a_c: scaling coefficient for crown fraction burn, from eq_26
    :param R: fire spread rate, from eq_18 (m/min)
    :param Ro: crital surface fire spread rate, from eq_27 (m/min)
    :return: CFB, Crown Fraction Burned
    """
    return (1 - np.exp(-a_c*(R-Ro)))

@jit(nopython=True, fastmath=True)
def feq_26(RAC, Ro):
    """
    :param RAC: fire spread rate in crown, from eq_22 (m/min)
    :param Ro: crital surface fire spread rate, from eq_27 (m/min)
    :return: a_c, scaling coefficient for crown fraction burn
    """
    return -np.log(.1)/(.9*(RAC-Ro))

@jit(nopython=True, fastmath=True)
def feq_27(R, Ib, Io):
    """
    :param R: fire spread rate, from eq_18 (m/min)
    :param Ib: fireline intensity, from eq_20 (Kw/m)
    :param Io: threshold for transition to crown fire, from eq_21 (Kw/m)
    :return: Ro, crital surface fire spread rate (m/min)
    """
    return Io*(R/Ib)

@jit(nopython=True, fastmath=True)
def compute_crown_spread(IR, R, CBD, M, CBH, sigma):
    """
    new parameters: CBD, CBH
    parameters from surface fire: IR, R, M, Sigma
    :param IR: surface reaction intensity (Kj/min/m^2)
    :param R: surface spread rate (m/min)
    :param CBD: crown bulk density (Kg/m^3)
    :param M: Crown Foliar Moisture (percent) - we can use M_f from surface spread
    :param CBH: height to crown base (m)
    """
    Io = eq_21(CBH, M)
    RAC = eq_22(CBD)
    Ib = eq_20(IR, R, sigma)
    Ro = eq_27(R, Ib, Io)
    a_c = eq_26(RAC, Ro)
    CFB = eq_25(a_c, R, Ro)
    R_Cmax = eq_24(R, 1) # why 1? I am not sure what should go here
    R_Cactual = eq_23(R, CFB, R_Cmax)
    return R_Cactual
