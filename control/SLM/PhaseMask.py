# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 09:39:18 2016

@author: aurelien.barbotin, jonatan.alvelid
"""
from __future__ import division
import math
import numpy as np
# import matplotlib.pyplot as plt
# import cmath
# from scipy import signal as sg

# SLM model : X10468-02
# 792 x 600 pixels
# 800+/-50nm maximum 785nm

def helMask(sizex, sizey, r, u=0, v=0, rotation=True):
    """This function generates an helicoidal phase mask centered in (u,v) where (0,0) corresponds to
    the center of the image"""
    x, y = np.ogrid[(-sizex // 2 - u): (sizex // 2 - u), (-sizey // 2 - v): (sizey // 2 - v)]
    d2 = x**2 + y**2
    theta = np.arctan2(x, y)
    theta[d2 > r**2] = 0
    theta %= 2 * math.pi
    # To change the rotation direction of the helix
    if rotation:
        mask_bis = np.ones((sizex, sizey)) * np.pi * 2
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
    #x, y = np.ogrid[(-sizex // 2 - u): (sizex // 2 - u), (-sizey // 2 - v): (sizey // 2 - v)]
    #d = np.sqrt(x**2 + y**2)

    #circular_mask = np.ones((x.size, y.size))
    #circular_mask[d > r] = 0

    theta_patt = np.fromfunction(lambda i, j: np.arctan2(((j - sizey // 2 - v) / r), ((i - sizex // 2 - u) / r)), (sizex, sizey), dtype="float").astype(float)
    rho_patt = np.fromfunction(lambda i, j: np.sqrt(((i - sizex // 2 - u) / r)**2 + ((j - sizey // 2 - v) / r)**2), (sizex, sizey), dtype="float").astype(float)
    rho_glob = np.fromfunction(lambda i, j: np.sqrt(((i - sizex // 2 - u))**2 + ((j - sizey // 2 - v))**2), (sizex, sizey), dtype="float").astype(float)

    f_tilt = aberrationFactors[0]
    f_tip = aberrationFactors[1]
    f_defoc = aberrationFactors[2]
    f_sph = aberrationFactors[3]
    f_vertcoma = aberrationFactors[4]
    f_hozcoma = aberrationFactors[5]
    f_vertast = aberrationFactors[6]
    f_oblast = aberrationFactors[7]
    f_verttre = aberrationFactors[8]
    f_obltre = aberrationFactors[9]

    circular_mask = (rho_glob <= r).astype(int)
    tilt_mask = f_tilt * 2 * rho_patt * np.sin(theta_patt)
    tip_mask = f_tip * 2 * rho_patt * np.cos(theta_patt)
    defoc_mask = f_defoc * np.sqrt(3) * (2 * rho_patt**2 - 1)
    sph_mask = f_sph * np.sqrt(5) * (6 * rho_patt**4 - 6 * rho_patt**2 + 1)
    vertcoma_mask = f_vertcoma * np.sqrt(8) * (3 * rho_patt**3 - 2 * rho_patt) * np.sin(theta_patt)
    hozcoma_mask = f_hozcoma * np.sqrt(8) * (3 * rho_patt**3 - 2 * rho_patt) * np.cos(theta_patt)
    vertast_mask = f_vertast * np.sqrt(6) * rho_patt**2 * np.cos(2 * theta_patt)
    oblast_mask = f_oblast * np.sqrt(6) * rho_patt**2 * np.sin(2 * theta_patt)
    verttre_mask = f_verttre * np.sqrt(8) * rho_patt**3 * np.sin(3 * theta_patt)
    obltre_mask = f_obltre * np.sqrt(8) * rho_patt**3 * np.cos(3 * theta_patt)

    mask = np.multiply(circular_mask, tilt_mask + tip_mask + defoc_mask + sph_mask +
                       vertcoma_mask + hozcoma_mask + vertast_mask +
                       oblast_mask + verttre_mask + obltre_mask + math.pi)
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
    mask_bin = (x * x + y * y <= radius * radius)
    result = np.zeros((m, n))
    result[mask_bin] = mask[mask_bin]
    return result
