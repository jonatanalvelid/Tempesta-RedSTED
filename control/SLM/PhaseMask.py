# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 09:39:18 2016

@author: aurelien.barbotin, jonatan.alvelid
"""
from __future__ import division
import numpy as np
import math
# import matplotlib.pyplot as plt
# import cmath
# from scipy import signal as sg
"""
SLM model : X10468-02
792 x 600 pixels
800+/-50nm maximum 785nm
"""

n = 601    # width of the phase pattern in pixels
m = 601    # height of the phase pattern in pixels
pad = 600  # padding for the fft, in pixels
r = 300    # radius of the phase pattern
s_pix = 0.02  # pixel size in mm (SLM)
lbd = 785 * 10**-6    # wavelength in mm
f = 4.7    # focal length in mm (20x/1.0 zeiss)


def helMask(m, n, r, u=0, v=0, rotation=True):
    """This function generates an helicoidal phase mask centered in (u,v) where (0,0) corresponds to
    the center of the image"""
    x, y = np.ogrid[(-m // 2 - u): (m // 2 - u), (-n // 2 - v): (n // 2 - v)]
    d2 = x**2 + y**2
    theta = np.arctan2(x, y)
    theta[d2 > r**2] = 0
    theta %= 2 * math.pi
    # To change the rotation direction of the helix
    if(rotation):
        mask_bis = np.ones((m, n)) * np.pi * 2
        mask_bis[d2 > r**2] = 0
        theta = mask_bis - theta
    return theta


def topHat(sizex, sizey, r, sigma, u, v):
    """Creates a top hat mask with radius r. The input beam is supposed gaussain
    with a standard deviation sigma."""
    mask = np.zeros((sizex, sizey), dtype="float")
    # Looking for the middle of the gaussian intensity distribution:
    mid_radius = sigma * np.sqrt(2 * np.log(2 / (1 + np.exp(-r**2 / (2 * sigma**2)))))
    y, x = np.ogrid[(-sizex // 2 - u): (sizex // 2 - u), (-sizey // 2 - v): (sizey // 2 - v)]
    d2 = x**2 + y**2
    ring = (d2 <= r**2) * (d2 > mid_radius**2)
    mask[ring] = np.pi
    return mask


def HalfPattern(sizex, sizey, r, u, v, rotang):
    """Creates a top hat mask with radius r. The input beam is supposed gaussain
    with a standard deviation sigma."""
    mask = np.zeros((sizex, sizey), dtype="float")
    y, x = np.ogrid[-sizex//2-u:sizex//2-u, -sizey//2-v:sizey//2-v]
    d2 = x**2 + y**2
    theta = np.arctan2(x, y) + rotang
    midLine = (abs(theta) < np.pi / 2)*(d2 <= r**2)
    mask[midLine] = np.pi
    return mask


def QuadrantPattern(sizex, sizey, r, u, v, rotang):
    """Creates a top hat mask with radius r. The input beam is supposed gaussain
    with a standard deviation sigma."""
    mask = np.zeros((sizex, sizey), dtype="float")
    y, x = np.ogrid[-sizex//2-u:sizex//2-u, -sizey//2-v:sizey//2-v]
    theta = np.arctan2(x, y) + rotang
    d2 = x**2 + y**2
    quadLine = (theta < np.pi)*(theta > np.pi / 2)*(d2<=r**2)+ (theta < 0 )*(theta > -np.pi / 2)*(d2 <= r**2)
    mask[quadLine] = np.pi
    return mask


def HexPattern(sizex, sizey, r, u, v, rotang):
    """Creates a top hat mask with radius r. The input beam is supposed gaussain
    with a standard deviation sigma."""
    mask = np.zeros((sizex, sizey), dtype="float")
    y, x = np.ogrid[-sizex//2-u:sizex//2-u, -sizey//2-v:sizey//2-v]
    theta = np.arctan2(x, y) + rotang
    d2 = x**2 + y**2
    hexLine = (theta < np.pi / 3)*(theta > 0)*(d2<=r**2)+ (theta > -2 * np.pi / 3)*(theta < -np.pi / 3)*(d2 <= r**2) + (theta > 2 * np.pi / 3)*(theta < np.pi)*(d2<=r**2) 
    mask[hexLine] = np.pi
    return mask


def SplitBullseyePattern(sizex, sizey, r, u, v, rotang):
    """Creates a top hat mask with radius r. The input beam is supposed gaussain
    with a standard deviation sigma."""
    radius_factor = 0.6
    mask = np.zeros((sizex, sizey), dtype="float")
    mask1 = np.zeros((sizex, sizey), dtype="float")
    mask2 = np.zeros((sizex, sizey), dtype="float")
    #Looking for the middle of the gaussian intensity distribution:
    mid_radius = radius_factor * r
    y, x = np.ogrid[-sizex//2-u:sizex//2-u, -sizey//2-v:sizey//2-v]
    theta = np.arctan2(x, y) + rotang
    d2 = x**2 + y**2
    ring = (d2 <= r**2)*(d2 > mid_radius**2)
    mask1[ring] = np.pi
    midLine = (abs(theta) < np.pi / 2)*(d2 <= r**2)
    mask2[midLine] = np.pi
    mask = (mask1 + mask2) % (2 * np.pi)
    return mask


def aberrationsMask(sizex, sizey, r, u, v, aberrationFactors):
    """Creates a top hat mask with radius r. The input beam is supposed gaussain
    with a standard deviation sigma."""
    x, y = np.ogrid[(-sizex // 2 - u): (sizex // 2 - u), (-sizey // 2 - v): (sizey // 2 - v)]
    d = np.sqrt(x**2 + y**2)

    circularMask = np.ones((x.size, y.size))
    circularMask[d > r] = 0

    fTilt = aberrationFactors[0]
    fTip = aberrationFactors[1]
    fDefoc = aberrationFactors[2]
    fSph = aberrationFactors[3]
    fVertComa = aberrationFactors[4]
    fHozComa = aberrationFactors[5]
    fVertAstPar = aberrationFactors[6]
    fOblAstPar = aberrationFactors[7]

    tiltMask = np.fromfunction(lambda i, j: fTilt * 2 * np.sqrt(((i - sizex // 2 - u) / r)**2 + ((j - sizey // 2 - v) / r)**2) * np.sin(np.arctan2(((j - sizey // 2 - v) / r), ((i - sizex // 2 - u) / r))), (sizex, sizey), dtype="float")
    tipMask = np.fromfunction(lambda i, j: fTip * 2 * np.sqrt(((i - sizex // 2 - u) / r)**2 + ((j - sizey // 2 - v) / r)**2) * np.cos(np.arctan2(((j - sizey // 2 - v) / r), ((i - sizex // 2 - u) / r))), (sizex, sizey), dtype="float")
    defocusMask = np.fromfunction(lambda i, j: fDefoc * np.sqrt(3) * (2 * (((i - sizex // 2 - u) / r)**2 + ((j - sizey // 2 - v) / r)**2) - 1), (sizex, sizey), dtype="float")
    sphericalMask = np.fromfunction(lambda i, j: fSph * np.sqrt(5) * (6 * (((i - sizex // 2 - u) / r)**2 + ((j - sizey // 2 - v) / r)**2)**4 - 6 * (((i - sizex // 2 - u) / r)**2 + ((j - sizey // 2 - v) / r)**2) + 1), (sizex, sizey), dtype="float")
    verticalComaMask = np.fromfunction(lambda i, j: fVertComa * np.sqrt(8) * np.sin(np.arctan2(((j - sizey // 2 - v) / r), ((i - sizex // 2 - u) / r))) * (3 * (np.sqrt(((i - sizex // 2 - u) / r)**2 + ((j - sizey // 2 - v) / r)**2))**3 - 2 * np.sqrt(((i - sizex // 2 - u) / r)**2 + ((j - sizey // 2 - v) / r)**2)), (sizex, sizey), dtype="float")
    horizontalComaMask = np.fromfunction(lambda i, j: fHozComa * np.sqrt(8) * np.cos(np.arctan2(((j - sizey // 2 - v) / r), ((i - sizex // 2 - u) / r))) * (3 * (np.sqrt(((i - sizex // 2 - u) / r)**2 + ((j - sizey // 2 - v) / r)**2))**3 - 2 * np.sqrt(((i - sizex // 2 - u) / r)**2 + ((j - sizey // 2 - v) / r)**2)), (sizex, sizey), dtype="float")
    verticalAstigmatismMask = np.fromfunction(lambda i, j: fVertAstPar * np.sqrt(6) * np.cos(2 * np.arctan2(((j - sizey // 2 - v) / r), ((i - sizex // 2 - u) / r))) * ((np.sqrt(((i - sizex // 2 - u) / r)**2 + ((j - sizey // 2 - v) / r)**2))**2), (sizex, sizey), dtype="float")
    obliqueAstigmatismMask = np.fromfunction(lambda i, j: fOblAstPar * np.sqrt(6) * np.sin(2 * np.arctan2(((j - sizey // 2 - v) / r), ((i - sizex // 2 - u) / r))) * ((np.sqrt(((i - sizex // 2 - u) / r)**2 + ((j - sizey // 2 - v) / r)**2))**2), (sizex, sizey), dtype="float")

    mask = np.multiply(circularMask, tiltMask + tipMask + defocusMask + sphericalMask + verticalComaMask + horizontalComaMask + verticalAstigmatismMask + obliqueAstigmatismMask + math.pi)
    mask %= 2 * math.pi

    return mask


def setCircular(mask, radius, x=-1, y=-1):
    """transforms an array-like phase pattern into a circular pattern"""
    (m, n) = mask.shape
    if x < 0:
        centerx = m // 2
    else:
        centerx = x
    if y < 0:
        centery = n // 2
    else:
        centery = y

    x, y = np.ogrid[-centerx: m - centerx, -centery: n - centery]
    mask_bin = x * x + y * y <= radius * radius
    result = np.zeros((m, n))
    result[mask_bin] = mask[mask_bin]
    return result
