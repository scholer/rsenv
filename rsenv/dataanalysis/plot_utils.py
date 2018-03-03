
import numpy as np
import matplotlib


def mkfigsize(w, h, unit, dpi=None):
    if dpi is None:
        dpi = matplotlib.rcParams['figure.dpi']
        if matplotlib.rcParams['savefig.dpi'].lower() != 'figure':
            print("NOTICE: Using `dpi={dpi}` from matplotlib `figure.dpi` setting, but `savefig.dpi` is not 'figure'.")
    if unit in ('px', 'pixel', 'pixels'):
        unit = 'px'
        figsize = np.array([w, h]) / dpi
    elif unit in ('pt', 'point', 'points'):
        unit = 'pt'
        figsize = np.array([w, h]) / 72
    else:
        unit = 'in'
        figsize = np.array([w, h])
    figsize_str = f"{w}x{h}{unit}"
    return figsize, figsize_str


