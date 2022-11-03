import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import quad
from scipy.optimize import root_scalar as fzero
import scipy.integrate
from scipy import optimize
from scipy import interpolate
import pandas as pd
from scipy.interpolate import interp1d
from scipy.optimize import minimize

import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import quad
from scipy.optimize import root_scalar as fzero
import scipy.integrate
import scipy.optimize
from pathlib import Path

def integral(*args):
    return quad(*args)[0]


def eq78(alpha1, alpha2):
    # eq. (28)
    alpha3 = 1 / (alpha1 * alpha2)

    # eq. (18)
    deltaP = lambda lambd: np.sqrt((alpha1 ** 2 + lambd) * (alpha2 ** 2 + lambd) * (alpha3 ** 2 + lambd))
    fung1 = lambda lambd: lambd / ((alpha2 ** 2 + lambd) * (alpha3 ** 2 + lambd) * deltaP(lambd))
    g1pp = integral(fung1, 0, np.Inf)
    fung2 = lambda lambd: lambd / ((alpha1 ** 2 + lambd) * (alpha3 ** 2 + lambd) * deltaP(lambd))
    g2pp = integral(fung2, 0, np.Inf)
    fung3 = lambda lambd: lambd / ((alpha1 ** 2 + lambd) * (alpha2 ** 2 + lambd) * deltaP(lambd))
    g3pp = integral(fung3, 0, np.Inf)

    # eq. (39)
    I = 2 / 5 * (g1pp + g2pp) / (g2pp * g3pp + g3pp * g1pp + g1pp * g2pp)

    # eq. (40)
    J = 2 / 5 * (g1pp - g2pp) / (g2pp * g3pp + g3pp * g1pp + g1pp * g2pp)

    # eq. (78)
    diff = (alpha1 ** 2 + alpha2 ** 2 - 2 / (alpha1 ** 2 * alpha2 ** 2)) / (alpha1 ** 2 - alpha2 ** 2) - J / I

    return diff

def getAlpha2(alpha1):
    if alpha1 == 1:
        return 1
    fun = lambda x: eq78(alpha1, x)
    alpha2 = fzero(fun, bracket=[1e-5, 1 - 1e-9]).root
    return alpha2


def getI_raw(alpha1, alpha2):
    # eq. (28)
    alpha3 = 1 / (alpha1 * alpha2)

    # eq. (18)
    deltaP = lambda lambd: np.sqrt((alpha1 ** 2 + lambd) * (alpha2 ** 2 + lambd) * (alpha3 ** 2 + lambd))
    fung1 = lambda lambd: lambd / ((alpha2 ** 2 + lambd) * (alpha3 ** 2 + lambd) * deltaP(lambd))
    g1pp = integral(fung1, 0, np.Inf)

    fung2 = lambda lambd: lambd / ((alpha1 ** 2 + lambd) * (alpha3 ** 2 + lambd) * deltaP(lambd))
    g2pp = integral(fung2, 0, np.Inf)
    fung3 = lambda lambd: lambd / ((alpha1 ** 2 + lambd) * (alpha2 ** 2 + lambd) * deltaP(lambd))
    g3pp = integral(fung3, 0, np.Inf)

    # eq. (39)
    I = 2 / 5 * (g1pp + g2pp) / (g2pp * g3pp + g3pp * g1pp + g1pp * g2pp)

    return I

def getK_raw(alpha1, alpha2):
    # eq. (28)
    alpha3 = 1 / (alpha1 * alpha2)

    # eq. (20)
    deltaP = lambda lambd: np.sqrt((alpha1 ** 2 + lambd) * (alpha2 ** 2 + lambd) * (alpha3 ** 2 + lambd))
    fung3p = lambda lambd: 1 / ((alpha1 ** 2 + lambd) * (alpha2 ** 2 + lambd) * deltaP(lambd))
    g3p = integral(fung3p, 0, np.Inf)

    # eq. (43)
    K = 1 / (5 * g3p) * (alpha1 ** 2 + alpha2 ** 2) / (alpha1 ** 2 * alpha2 ** 2)

    return K

from scipy import interpolate

def getFormFactorFunctions():
    output = Path(__file__).parent / "form_factors.npy"
    if not output.exists():
        alpha1 = np.arange(1., 10, 0.01)
        alpha2 = np.array([getAlpha2(a1) for a1 in alpha1])
        I = np.array([getI_raw(a1, a2) for a1, a2 in zip(alpha1, alpha2)])
        K = np.array([getK_raw(a1, a2) for a1, a2 in zip(alpha1, alpha2)])
        alpha1_alpha2 = alpha1/alpha2

        np.save(output, np.array([alpha1_alpha2, alpha1, alpha2, K, I]))

    alpha1_alpha2, alpha1, alpha2, K, I = np.load(output)

    _getAlpha1 = interpolate.interp1d(alpha1_alpha2, alpha1)
    _getAlpha2 = interpolate.interp1d(alpha1_alpha2, alpha2)
    _getK = interpolate.interp1d(alpha1_alpha2, K)
    _getI = interpolate.interp1d(alpha1_alpha2, I)
    return _getAlpha1, _getAlpha2, _getK, _getI

def integral(*args):
    return quad(*args)[0]

getAlpha1, getAlpha2, getK, getI = getFormFactorFunctions()

def eq41(alpha1, alpha2, theta, kappa):
    t1 = -(alpha1 ** 2 + alpha2 ** 2) / (2 * alpha1 * alpha2)
    t2 = 1 - (alpha1 ** 2 - alpha2 ** 2) / (alpha1 ** 2 + alpha2 ** 2) * np.cos(2 * theta)

    nu = t1 * t2 * kappa / 2
    return nu


def eq79(alpha1, alpha2, theta, sigma):
    # eq. (39)
    I = getI(alpha1/alpha2)

    # eq. (79) with minus (!)
    kappa = (alpha1 ** 2 - alpha2 ** 2) / (2 * I) / (sigma * np.sin(2 * theta))

    return kappa


def eq80(alpha1, alpha2, sigma, tau):
    K = getK(alpha1/alpha2)

    t1 = (alpha1 ** 2 - alpha2 ** 2) / (alpha1 ** 2 + alpha2 ** 2)
    t2 = 1 + (tau - sigma) / (K * sigma) * ((alpha1 ** 2 + alpha2 ** 2) / (2 * alpha1 * alpha2)) ** 2
    n1 = 1 + (tau - sigma) / (K * sigma) * ((alpha1 ** 2 - alpha2 ** 2) / (2 * alpha1 * alpha2)) ** 2

    theta = np.arccos(t1 * t2 / n1) / 2

    return theta

def getEta1(alpha1, alpha2, theta, eta0):
    K = getK(alpha1/alpha2)
    A = (alpha1**2 + alpha2**2) / (alpha1**2 - alpha2**2)
    B = (alpha1**2 + alpha2**2) / (2 * alpha1 * alpha2)
    C = (alpha1**2 - alpha2**2) / (2 * alpha1 * alpha2)
    eta1 = eta0 * (5/2 * K * (1-np.cos(2*theta)*A) / (C**2 * np.cos(2*theta)*A - B**2) + 1)
    #print(np.cos(2*theta))
    #print(1/A * (1 + 2/(5*K)*(eta1-eta0)/eta0 * B**2)/ (1 + 2/(5*K)*(eta1-eta0)/eta0 * C**2))
    #np.testing.assert_almost_equal(np.array(np.cos(2*theta)), np.array(1/A * (1 + 2/(5*K)*(eta1-eta0)/eta0 * B**2)/ (1 + 2/(5*K)*(eta1-eta0)/eta0 * C**2)))
    return eta1

def getMu1(alpha1, alpha2, theta, stress):
    I = getI(alpha1/alpha2)
    mu1 = 5/2 * stress * (2*I) / (alpha1**2 - alpha2**2) * np.sin(2*theta)
    return mu1

def getRoscoeStrain(alpha1, alpha2):
    I = getI(alpha1 / alpha2)
    epsilon = (alpha1 ** 2 - alpha2 ** 2) / (2*I)
    return epsilon

def getShearRate(viscLiquid, NHmodulus, viscSolid, alpha1_alpha2):
    # physical parameters in Roscoe notation
    eta0 = viscLiquid
    mu1 = NHmodulus
    eta1 = viscSolid

    # transform parameters, eq. (62)
    sigma = 5 * eta0 / (2 * mu1)
    tau = (3 * eta0 + 2 * eta1) / (2 * mu1)

    # compute alpha2 from (78)
    alpha1 = getAlpha1(alpha1_alpha2)
    alpha2 = getAlpha2(alpha1_alpha2)

    # compute theta from (80)
    theta = eq80(alpha1, alpha2, sigma, tau)

    # compute shear rate from (79)
    kappa = eq79(alpha1, alpha2, theta, sigma)

    # transcribe
    shearRate = kappa

    return shearRate

def getThetaTTFreq(viscLiquid, NHmodulus, viscSolid, kappa, alpha1, alpha2):
    # physical parameters in Roscoe notation
    eta0 = viscLiquid
    mu1 = NHmodulus
    eta1 = viscSolid

    # transform parameters, eq. (62)
    sigma = 5 * eta0 / (2 * mu1)
    tau = (3 * eta0 + 2 * eta1) / (2 * mu1)

    # compute theta from (80)
    theta = eq80(alpha1, alpha2, sigma, tau)

    # compute TT frequency from (41)
    nu = - eq41(alpha1, alpha2, theta, kappa)

    # transcribe
    ttFreq = nu
    thetaDeg = theta / (2 * np.pi) * 360

    return thetaDeg, ttFreq

def RoscoeCore(viscLiquid, NHmodulus, viscSolid, alpha1, alpha2):
    # physical parameters in Roscoe notation
    eta0 = viscLiquid
    mu1 = NHmodulus
    eta1 = viscSolid

    # transform parameters, eq. (62)
    sigma = 5 * eta0 / (2 * mu1)
    tau = (3 * eta0 + 2 * eta1) / (2 * mu1)

    # compute theta from (80)
    theta = eq80(alpha1, alpha2, sigma, tau)

    # compute shear rate from (79)
    kappa = eq79(alpha1, alpha2, theta, sigma)

    # compute TT frequency from (41)
    nu = - eq41(alpha1, alpha2, theta, kappa)

    # transcribe
    shearRate = kappa
    ttFreq = nu
    thetaDeg = theta / (2 * np.pi) * 360

    return shearRate, alpha2, thetaDeg, ttFreq


def RoscoeShearSingle(viscLiquid, NHmodulus, viscSolid, shearRateWanted, alpha1min=1.001, alpha1step=0.01):
    # define function to find root
    # find alpha1=x which gives the desired shear rate
    fun = lambda x: shearRateWanted - RoscoeCore(viscLiquid, NHmodulus, viscSolid, x)[0]

    # determine suitable interval for alpha1
    shearRateMin = RoscoeCore(viscLiquid, NHmodulus, viscSolid, alpha1min)[0]
    if shearRateMin.imag != 0:
        raise ValueError('Minimum shear rate is imaginary!')

    diffMin = shearRateWanted - shearRateMin

    # take small steps and detect sign change
    alpha1max = alpha1min
    cont = 1
    while cont:
        alpha1max = alpha1max + alpha1step
        shearRateMax = RoscoeCore(viscLiquid, NHmodulus, viscSolid, alpha1max)[0]
        print(cont, shearRateMax)

        if shearRateMax.imag != 0:
            # imaginary shear rate means that step was too large
            # reduce and retry
            alpha1max = alpha1max - alpha1step
            alpha1step = alpha1step / 10
            alpha1max = alpha1max + alpha1step
            shearRateMax = RoscoeCore(viscLiquid, NHmodulus, viscSolid, alpha1max)[0]

        diffMax = shearRateWanted - shearRateMax
        if diffMax * diffMin < 0:
            cont = 0

    # now we have an interval, find root
    alpha1 = fzero(fun, bracket=[alpha1min, alpha1max]).root

    # compute actual values for return
    shearRateObtained, alpha2, thetaDeg, ttFreq = RoscoeCore(viscLiquid, NHmodulus, viscSolid, alpha1)

    return alpha1, alpha2, thetaDeg, ttFreq

def getRatio(eta0, alpha, tau, vdot, NHmodulus, viscSolid):
    eta = eta0 / (1 + tau ** alpha * vdot ** alpha)
    viscLiquid = eta
    ratio = np.zeros_like(eta)
    for i in range(len(ratio)):
        test_rations = np.geomspace(1, 10, 1000)
        try:
            j = np.nanargmax(getShearRate(viscLiquid[i], NHmodulus[i], viscSolid[i], test_rations))
        except ValueError:
            ratio[i] = np.nan
            continue
        max_ratio = test_rations[j]
        if j == len(test_rations)-1 and getShearRate(viscLiquid[i], NHmodulus[i], viscSolid[i], max_ratio) - vdot[i] < 0:
            break
        while getShearRate(viscLiquid[i], NHmodulus[i], viscSolid[i], max_ratio) - vdot[i] < 0:
            test_rations = np.geomspace(test_rations[j], test_rations[j+1], 1000)
            j = np.nanargmax(getShearRate(viscLiquid[i], NHmodulus[i], viscSolid[i], test_rations))
            max_ratio = test_rations[j]

        ratio[i] = scipy.optimize.root_scalar(lambda ratio: getShearRate(viscLiquid[i], NHmodulus[i], viscSolid[i], ratio) - vdot[i], bracket=[1, max_ratio]).root

    vdot = vdot[ratio > 0]
    eta = eta[ratio > 0]
    viscLiquid = viscLiquid[ratio > 0]
    ratio = ratio[ratio > 0]
    alpha1 = getAlpha1(ratio)
    alpha2 = getAlpha2(ratio)
    theta, ttfreq = getThetaTTFreq(viscLiquid, NHmodulus, viscSolid, vdot, alpha1, alpha2)
    strain = (alpha1 - alpha2) / np.sqrt(alpha1 * alpha2)
    stress = eta*vdot
    return ratio, alpha1, alpha2, strain, stress, theta, ttfreq, eta, vdot





# transfrom angles from 0,180 to -90,90
def transform_angle(df):
    mask = df['p'] > 90
    df['angle'] = df['p']
    df['angle'][mask] = df['p'] - 180.
    return df

def matchVelocities(last_frame_cells, new_cells, config):
    if len(last_frame_cells) != 0 and len(new_cells) != 0:
        conditions = (
                (np.abs(np.array(last_frame_cells.frame)[:, None] - np.array(new_cells.frame)[None, :]) == 1) &
                # radial pos
                (np.abs(np.array(last_frame_cells.y)[:, None] - np.array(new_cells.y)[None, :]) < 5) &
                # long_axis
                (np.abs(np.array(last_frame_cells.w)[:, None] - np.array(new_cells.w)[None, :]) < 5) &
                # short axis
                (np.abs(np.array(last_frame_cells.h)[:, None] - np.array(new_cells.h)[None, :]) < 5) &
                # angle
                (np.abs(np.array(last_frame_cells.p)[:, None] - np.array(new_cells.p)[None, :]) < 5) &
                # positive velocity
                (np.abs(np.array(last_frame_cells.x)[:, None] < np.array(new_cells.x)[None, :]))  # &
        )
        # print(conditions)
        indices = np.argmax(conditions, axis=0)
        # print(indices)
        found = conditions[indices, np.arange(conditions.shape[1])]
        for i in range(len(indices)):
            if found[i]:
                j = indices[i]
                c1 = new_cells.iloc[i]
                c2 = last_frame_cells.iloc[j]
                dt = (c1.timestamp - c2.timestamp)
                # prevent division by zeros
                if dt > 1e-9:
                    v = (c1.x - c2.x) * config['pixel_size'] / dt
                    new_cells.iat[i, new_cells.columns.get_loc("measured_velocity")] = v
                    new_cells.iat[i, new_cells.columns.get_loc("cell_id")] = c2.cell_id

    return new_cells

from scipy.optimize import curve_fit


def fit_func_velocity(config):
    if "vel_fit" in config:
        p0, p1, p2 = config["vel_fit"]
        p2 = 0
    else:
        p0, p1, p2 = None, None, None

    def velfit(r, p0=p0, p1=p1, p2=p2):  # for stress versus strain
        R = config["channel_width_m"] / 2 * 1e6
        return p0 * (1 - np.abs((r + p2) / R) ** p1)

    return velfit


def correctCenter(data, config):
    # remove nans
    d = data[np.isfinite(data.measured_velocity)]
    # remove outlier points
    d = d[d.measured_velocity < np.nanpercentile(d.measured_velocity, 95) * 1.5]
    d = d[d.measured_velocity > 0]

    y_pos = d.radial_position
    vel = d.measured_velocity

    if len(vel) == 0:
        raise ValueError("No velocity values found.")
    vel_fit, pcov = curve_fit(fit_func_velocity(config), y_pos, vel,
                              [np.nanpercentile(vel, 95), 3,
                               -np.mean(y_pos)])  # fit a parabolic velocity profile
    y_pos += vel_fit[2]
    # data.y += vel_fit[2]
    data.radial_position += vel_fit[2]

    config["vel_fit"] = list(vel_fit)
    config["center"] = vel_fit[2]

    # data["velocity_gradient"] = fit_func_velocity_gradient(config)(data.radial_position)
    # data["velocity_fitted"] = fit_func_velocity(config)(data.radial_position)
    # data["imaging_pos_mm"] = config["imaging_pos_mm"]
    return data


def stressfunc(radial_position: np.ndarray, pressure: np.ndarray,
               channel_length: np.ndarray, channel_height: np.ndarray) -> np.ndarray:
    radial_position = np.asarray(radial_position)
    G = pressure / channel_length  # pressure gradient
    pre_factor = (4 * (channel_height ** 2) * G) / np.pi ** 3
    # sum only over odd numbers
    n = np.arange(1, 100, 2)[None, :]
    u_primy = pre_factor * np.sum(((-1) ** ((n - 1) / 2)) * (np.pi / ((n ** 2) * channel_height)) \
                                  * (np.sinh((n * np.pi * radial_position[:, None]) / channel_height) / np.cosh(
        n * np.pi / 2)), axis=1)

    stress = np.abs(u_primy)
    return stress


def getStressStrain(data: pd.DataFrame, config: dict):
    """ calculate the stress and the strain of the cells """
    r = np.sqrt(data.long_axis / 2 * data.short_axis / 2) * 1e-6
    data["stress"] = 0.5 * stressfunc(data.radial_position * 1e-6 + r, -config["pressure_pa"],
                                      config["channel_length_m"], config["channel_width_m"]) \
                     + 0.5 * stressfunc(data.radial_position * 1e-6 - r, -config["pressure_pa"],
                                        config["channel_length_m"],
                                        config["channel_width_m"])
    # data["stress_center"] = stressfunc(data.radial_position * 1e-6, -config["pressure_pa"], config["channel_length_m"],
    #                                  config["channel_width_m"])

    data["strain"] = (data.long_axis - data.short_axis) / np.sqrt(data.long_axis * data.short_axis)


def flatten_input(f):
    return lambda x: f(x.ravel()).reshape(x.shape)


def getQuadrature(N: int, xmin: float, xmax: float) -> (np.ndarray, np.ndarray):
    """
    Provides N quadrature points for an integration from xmin to xmax together with their weights.

    Parameters
    ----------
    N : int
        The number of quadrature points to use. Has to be 1 <= N <= 5.
    xmin : float
        The start of the integration range
    xmax : float
        The end of the integration range

    Returns
    -------
    points : np.ndarray
        The points of the quadrature
    w : np.ndarray
        The weights of the points
    """
    if N < 1:
        raise ValueError()

    if N == 1:
        points = [0]
        w = [2]

    if N == 2:
        points = [-np.sqrt(1 / 3), np.sqrt(1 / 3)]
        w = [1, 1]

    if N == 3:
        points = [-np.sqrt(3 / 5), 0, np.sqrt(3 / 5)]
        w = [5 / 9, 8 / 9, 5 / 9]

    if N == 4:
        points = [-np.sqrt(3 / 7 - 2 / 7 * np.sqrt(6 / 5)), +np.sqrt(3 / 7 - 2 / 7 * np.sqrt(6 / 5)),
                  -np.sqrt(3 / 7 + 2 / 7 * np.sqrt(6 / 5)), +np.sqrt(3 / 7 + 2 / 7 * np.sqrt(6 / 5))]
        w = [(18 + np.sqrt(30)) / 36, (18 + np.sqrt(30)) / 36, (18 - np.sqrt(30)) / 36, (18 - np.sqrt(30)) / 36]

    if N == 5:
        points = [0,
                  -1 / 3 * np.sqrt(5 - 2 * np.sqrt(10 / 7)), +1 / 3 * np.sqrt(5 - 2 * np.sqrt(10 / 7)),
                  -1 / 3 * np.sqrt(5 + 2 * np.sqrt(10 / 7)), +1 / 3 * np.sqrt(5 + 2 * np.sqrt(10 / 7))]
        w = [128 / 225, (322 + 13 * np.sqrt(70)) / 900, (322 + 13 * np.sqrt(70)) / 900, (322 - 13 * np.sqrt(70)) / 900,
             (322 - 13 * np.sqrt(70)) / 900]

    if N > 5:
        raise ValueError()

    points = np.array(points)
    w = np.array(w)
    factor = (xmax - xmin) / 2
    points = factor * points[:, None] + (xmax + xmin) / 2
    w = w[:, None] * factor
    return points, w


def quad(f, a, b, deg=5):
    points, w = getQuadrature(deg, a, b)
    integral = np.sum(flatten_input(f)(points) * w, axis=0)
    return integral


def newton(func, x0, args=[], maxiter=100, mtol=1e-5):
    for i in range(maxiter):
        y, ydot = func(x0, *args)
        dx = - y/ydot
        if np.all(np.abs(y) < mtol):
            break
        x0 += dx
    return x0


def getVelocity(eta0, alpha, tau, H, W, P, L, x_sample=100):
    #print([eta0, alpha, tau, H, W, P, L])
    pi = np.pi
    n = np.arange(1, 99, 2)[None, :]

    def getBeta(y):
        return 4 * H ** 2 * P / (pi ** 3 * L) * np.sum(
            (-1) ** ((n - 1) / 2) * pi / (n ** 2 * H) * np.sinh((n * pi * y) / H) / np.cosh((n * pi * W) / (2 * H)), axis=1)

    tau_alpha = tau ** alpha

    def f(beta):
        def f2(vdot):
            return 1 - eta0 / beta * vdot + tau_alpha * vdot ** alpha
        return f2


    def f_fprime(beta):
        beta += 1e-10
        def f2(vdot):
            #if vdot == 0:
            #    return 0, 0
            return 1 - eta0 / beta * vdot + tau_alpha * vdot ** alpha, - eta0 / beta + alpha * tau_alpha * vdot ** (alpha-1)
        return f2

    def f_max(beta):
        return (eta0 / (tau_alpha * alpha * beta + 1e-4))**(1/(alpha-1))

    ys = np.arange(1e-6, H/2+1e-6, 1e-6)
    ys = np.linspace(0, H/2, x_sample)
    if 0:
        vdot = np.zeros_like(ys)
        for i, y in enumerate(ys):
            if y == 0:
                vdot[i] = 0
                continue
            beta = getBeta(y)
            sol = optimize.root_scalar(f(beta), bracket=[0, 1000_000], method='brentq')
            vdot[i] = sol.root
        v = np.cumsum(vdot)*np.diff(ys)[0]
        v -= v[-1]

    if 0:
        def getVdot(y):
            if y == 0:
                return 0
            beta = getBeta(y)
            sol = optimize.root_scalar(f(beta), bracket=[0, 1e7], method='brentq')
            return sol.root

        getVdot = np.vectorize(getVdot)

    def getVdot(y):
        beta = getBeta(y[:, None])
        start = f_max(beta)
        yy = newton(f_fprime(beta), start+0.00001)
        yy[y==0] = 0
        return yy

    if 0:
        x = np.arange(-10, 300, 0.01)
        beta = getBeta(ys[1:][:, None])
        xx = f(beta[80])(x)
        plt.plot(x, xx)
        plt.show()

    v = quad(getVdot, H / 2, ys)
    vdot = getVdot(ys)

    return ys, v, vdot

def getFitFunc(x, eta0, alpha, tau, H, W, P, L, x_sample=100):
    ys, v, vdot = getVelocity(eta0, alpha, tau, H, W, P, L, x_sample)
    return -interpolate.interp1d(ys, v, fill_value="extrapolate")(np.abs(x))

def getFitFuncDot(x, eta0, alpha, tau, H, W, P, L):
    ys, v, vdot = getVelocity(eta0, alpha, tau, H, W, P, L)
    return -interpolate.interp1d(ys, vdot, fill_value="extrapolate")(np.abs(x))

def fit_velocity(data, config, p=None, channel_width=None):
    if channel_width is None:
        H = config["channel_width_m"]
        W = config["channel_width_m"]
    else:
        H = channel_width
        W = channel_width
    P = config["pressure_pa"]
    L = config["channel_length_m"]

    x, y = data.radial_position * 1e-6, data.measured_velocity * 1e-3
    i = np.isfinite(x) & np.isfinite(y)
    x2 = x[i]
    y2 = y[i]

    def getAllCost(p):
        cost = 0
        cost += np.sum((getFitFunc(x2, p[0], p[1], p[2], H, W, P, L) - y2) ** 2)
        return cost

    if p is None:
        res = optimize.minimize(getAllCost, [3.8, 0.64, 0.04], method="TNC", options={'maxiter': 200, 'ftol': 1e-16},
                                bounds=[(0, np.inf), (0, 0.9), (0, np.inf)])

        p = res["x"]
    eta0, alpha, tau = p
    return p, getFitFunc(x, eta0, alpha, tau, H, W, P, L), getFitFuncDot(x, eta0, alpha, tau, H, W, P, L)


def fit_velocity_pressures(data, config, p=None, channel_width=None, pressures=None, x_sample=100, start_params=[3.8, 0.64, 0.04], method="TNC"):
    if channel_width is None:
        H = config["channel_width_m"]
        W = config["channel_width_m"]
    else:
        H = channel_width
        W = channel_width
    L = config["channel_length_m"]

    x, y = data.radial_position * 1e-6, data.measured_velocity * 1e-3
    i = np.isfinite(x) & np.isfinite(y)
    x2 = x[i]
    y2 = y[i]

    all_pressures = np.unique(data.pressure)
    if pressures is None:
        fit_pressures = all_pressures
    else:
        fit_pressures = pressures
    press = np.array(data.pressure)
    press2 = press[i]

    def getAllCost(p):
        cost = 0
        for P in fit_pressures:
            difference = getFitFunc(x2[press2 == P], p[0], p[1], p[2], H, W, P*1e5, L, x_sample) - y2[press2 == P]
            c = np.abs(difference)
            #c = difference**2
            if np.sum(np.isnan(c)):
                return np.Inf
            # clip cost for possible outliers
            c = np.clip(c, 0, np.percentile(c, 95))
            cost += np.sum(c)
        return cost

    if p is None:
        res = optimize.minimize(getAllCost, start_params, method=method, options={'maxiter': 200, 'ftol': 1e-16},
                                bounds=[(0, np.inf), (0, 0.9), (0, np.inf)])

        p = res["x"]

    eta0, alpha, tau = p
    y = np.zeros_like(x)
    yy = np.zeros_like(x)
    for P in all_pressures:
        indices = press == P
        y[indices] = getFitFunc(x[indices], eta0, alpha, tau, H, W, P*1e5, L)
        yy[indices] = getFitFuncDot(x[indices], eta0, alpha, tau, H, W, P*1e5, L)
    return p, y, yy


def getFitXY(config, pressure, p):
    H = config["channel_width_m"]
    W = config["channel_width_m"]
    L = config["channel_length_m"]
    x = np.linspace(-W/2, W/2, 1000)
    eta0, alpha, tau = p
    y = getFitFunc(x, eta0, alpha, tau, H, W, pressure * 1e5, L)
    return x, y


def getFitXYDot(config, pressure, p, count=1000):
    H = config["channel_width_m"]
    W = config["channel_width_m"]
    L = config["channel_length_m"]
    x = np.linspace(-W/2, W/2, count)
    eta0, alpha, tau = p
    y = getFitFuncDot(x, eta0, alpha, tau, H, W, pressure * 1e5, L)
    return x, y




def improved_fit(data, plot=False):
    curve_height = np.mean(data.query("-5 < radial_position < 5").measured_velocity) * 1e-3

    x0 = np.array(data.radial_position)
    y0 = np.array(data.measured_velocity * 1e-3)
    i = np.isfinite(x0) * np.isfinite(y0)
    x0 = x0[i]
    y0 = y0[i]

    config = {"channel_length_m": 5.8e-2, "channel_width_m": 186e-6}

    def getFitLine(pressure, p):
        #config = {"channel_length_m": 5.8e-2, "channel_width_m": 186e-6}
        x, y = getFitXY(config, np.mean(pressure), p)
        return x * 1e+6, y

    def getEta0(delta, tau):
        def cost(eta0):
            x, y = getFitLine(data.iloc[0].pressure, [eta0, delta, tau])
            return np.abs(curve_height - np.max(y))

        res = minimize(cost, [1], method="Nelder-Mead", bounds=[(0, np.inf)])
        eta0 = res["x"][0]
        return eta0

    def getEta0Error(delta, tau):
        def cost(eta0):
            x, y = getFitLine(data.iloc[0].pressure, [eta0, delta, tau])
            return np.abs(curve_height - np.max(y))

        res = minimize(cost, [1], method="Nelder-Mead", bounds=[(0, np.inf)])
        eta0 = res["x"][0]
        x, y = getFitLine(data.iloc[0].pressure, [eta0, delta, tau])
        f = interp1d(x, y, fill_value="extrapolate")
        y2 = f(x0)
        y_true = y0
        difference = y2 - y_true

        c = np.abs(difference)
        c = np.clip(c, 0, np.percentile(c, 95))
        error = np.sum(c)
        return error, (eta0, delta, tau)

    import time
    t = time.time()
    errors = [getEta0Error(i, j) for i in np.arange(0.01, 0.8, 0.1) for j in [1, 0.3, 0.1, 0.03, 0.01]]
    eta0, delta, tau = errors[np.argmin([e[0] for e in errors])][1]
    #print(time.time()-t)
    #data, p0 = apply_velocity_fit(data, start_params=[eta0, delta, tau], method="Nelder-Mead")

    def getCostAll(p):
        eta0, delta, tau = p

        x, y = getFitLine(data.iloc[0].pressure, [eta0, delta, tau])
        f = interp1d(x, y, fill_value="extrapolate")
        y2 = f(data.radial_position)
        y_true = data.measured_velocity * 1e-3
        difference = y2 - y_true

        #error = np.sqrt(np.sum(difference**2))
        error = np.sum(np.abs(difference)**2)
        return error

    res = minimize(getCostAll, [eta0, delta, tau], method="Nelder-Mead", bounds=[(0, np.inf), (0, 0.9), (0, np.inf)])
    eta0, delta, tau = res["x"]

    H = config["channel_width_m"]
    W = config["channel_width_m"]
    L = config["channel_length_m"]
    P = data.iloc[0].pressure
    vel = getFitFunc(data.radial_position * 1e-6, eta0, delta, tau, H, W, P*1e5, L)
    vel_grad = getFitFuncDot(data.radial_position * 1e-6, eta0, delta, tau, H, W, P*1e5, L)

    eta = eta0 / (1 + tau ** delta * np.abs(vel_grad) ** delta)

    data["vel_fit_error"] = np.sqrt(np.sum(((vel - data.measured_velocity) / data.measured_velocity) ** 2))

    data["vel"] = vel
    data["vel_grad"] = vel_grad
    data["eta"] = eta
    data["eta0"] = eta0
    data["delta"] = delta
    data["tau"] = tau
    #print(data["vel_fit_error"],data["vel"],data["vel_grad"],data["eta"],data["eta0"],data["delta"],data["tau"])
    if plot:
        def getFitLine(pressure, p):
        #    config = {"channel_length_m": 5.8e-2, "channel_width_m": 186e-6}
            x, y = getFitXY(config, np.mean(pressure), p)
            return x * 1e+6, y
        plt.plot(x0, y0, "o")
        plt.plot(*getFitLine(data.iloc[0].pressure, [eta0, delta, tau]))
        #plt.plot(*getFitLine(data.iloc[0].pressure, [4.938963739240634, 0.45672202786092697, 0.18545486100]))
        #plt.plot(*getFitLine(data.iloc[0].pressure, p0))
        plt.plot(data.radial_position, vel, "+")
        plt.show()

    return data, [eta0, delta, tau]


def match_cells_from_all_data(data, config, image_width=720):
    timestamps = {i: d.timestamp for i, d in data.groupby("frame").mean().iterrows()}
    for i, d in data.iterrows():
        x = d.x
        v = d.vel * 1e3 / config["pixel_size"]
        t = d.timestamp
        for dir in [1]:
            for j in range(1, 10):
                frame2 = d.frame + j * dir
                try:
                    dt = timestamps[frame2] - t
                except KeyError:
                    continue
                x2 = x + v * dt
                # if we ran out of the image, stop
                if not (0 <= x2 <= image_width):
                    break
                d2 = data[data.frame == frame2]
                # if the cell is already present in the frame, to not do any matching
                if len(d2[d2.cell_id == d.cell_id]):
                    continue
                d2 = d2[np.abs(d2.radial_position - d.radial_position) < 10]
                d2 = d2[np.abs(d2.x - x2) < 15]
                # if it survived the filters, merge
                if len(d2):
                    data.loc[data['cell_id'] == d2.iloc[0].cell_id, 'cell_id'] = d.cell_id


def get_cell_properties(data):
    import scipy.special

    alpha1 = getAlpha1(data.long_axis / data.short_axis)
    alpha2 = getAlpha2(data.long_axis / data.short_axis)

    epsilon = getRoscoeStrain(alpha1, alpha2)

    mu1 = getMu1(alpha1, alpha2, np.abs(np.deg2rad(data.angle)), data.stress)
    eta1 = getEta1(alpha1, alpha2, np.abs(np.deg2rad(data.angle)), data.eta)

    if "tt_omega" in data:
        omega = np.abs(data.tt_omega)

        ttfreq = - eq41(alpha1, alpha2, np.abs(np.deg2rad(data.angle)), np.abs(data.vel_grad))
        # omega = ttfreq

        # omega = data.freq * 2 * np.pi

        Gp1 = mu1
        Gp2 = eta1 * np.abs(omega)
        alpha_cell = np.arctan(Gp2 / Gp1) * 2 / np.pi
        k_cell = Gp1 / (omega ** alpha_cell * scipy.special.gamma(1 - alpha_cell) * np.cos(np.pi / 2 * alpha_cell))

        mu1_ = k_cell * omega ** alpha_cell * scipy.special.gamma(1 - alpha_cell) * np.cos(np.pi / 2 * alpha_cell)
        eta1_ = k_cell * omega ** alpha_cell * scipy.special.gamma(1 - alpha_cell) * np.sin(
            np.pi / 2 * alpha_cell) / omega

        # data["omega"] = omega
        data["tt_mu1"] = mu1
        data["tt_eta1"] = eta1
        data["tt_Gp1"] = Gp1
        data["tt_Gp2"] = Gp2
        data["tt_k_cell"] = k_cell
        data["tt_alpha_cell"] = alpha_cell
        data["tt_epsilon"] = epsilon

    def func(x, a, b):
        return x / 2 * 1 / (1 + a * x ** b)

    x = [0.113, 0.45]

    omega_weissenberg = func(np.abs(data.vel_grad), *x)
    w_Gp1 = mu1
    w_Gp2 = eta1 * np.abs(omega_weissenberg)
    w_alpha_cell = np.arctan(w_Gp2 / w_Gp1) * 2 / np.pi
    w_k_cell = w_Gp1 / (omega_weissenberg ** w_alpha_cell * scipy.special.gamma(1 - w_alpha_cell) * np.cos(
        np.pi / 2 * w_alpha_cell))

    data["omega"] = omega_weissenberg
    data["Gp1"] = w_Gp1
    data["Gp2"] = w_Gp2
    data["k"] = w_k_cell
    data["alpha"] = w_alpha_cell



def calculate_mech_prop(df,ts,config):
    frames = np.array(df.frame, dtype=np.int)
    timestamps = np.array(ts)
    df['timestamp'] = timestamps[frames]

    df = transform_angle(df)

    # calculate long and short axes from w,h
    df['long_axis'] = df['w'] * config["pixel_size"]
    df['short_axis'] = df['h'] * config["pixel_size"]

    # add radial position
    df['radial_position'] = (df['y'] - config["channel_width_px"] / 2) * config["pixel_size"]
    df['measured_velocity'] = np.zeros(len(df))
    df['cell_id'] = np.arange(len(df))

    cells = []
    for i in range(len(df.frame) - 1):
        t0, t1 = int(df['frame'][i]), int(df['frame'][i + 1])

        new_cells = matchVelocities(df.iloc[i:i + 1], df.iloc[i + 1:i + 2], config)

    df['measured_velocity'][df['measured_velocity'] == 0] = np.nan

    # correct center
    df = correctCenter(df, config)
    # print(config["vel_fit"], config["center"])

    # get Stress Strain
    getStressStrain(df, config)

    df["area"] = df.long_axis * df.short_axis * np.pi
    df["pressure"] = config["pressure_pa"] * 1e-5

    df, p = improved_fit(df, config, plot=False)

    try:
        match_cells_from_all_data(df, config, 720)
    except AttributeError as err:
        print("Err", err)
        pass

    mask_ls = df["long_axis"] > df["short_axis"]
    df = df[mask_ls]

    get_cell_properties(df)

    return df