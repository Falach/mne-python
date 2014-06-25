# Authors: Denis Engemann <denis.engemann@gmail.com>
#
# License: Simplified BSD

import os.path as op
import numpy as np

from ..externals.six import BytesIO
from ..utils import _sphere_to_cartesian


class Montage(object):
    """Sensor layouts

    Layouts are typically loaded from a file using read_layout. Only use this
    class directly if you're constructing a new layout.

    Parameters
    ----------
    pos : array, shape (n_channels, 3)
        The positions of the channels in 3d.
    names : list
        The channel names
    ids : list
        The channel ids
    kind : str
        The type of Layout (e.g. 'Vectorview-all')
    """
    def __init__(self, pos, names, kind):
        self.pos = pos
        self.names = names
        self.kind = kind

    def __repr__(self):
        return '<Montage | %s - Channels: %s ...>' % (self.kind,
                                                      ', '.join(self.names[:3]))


def read_montage(kind, names=None, path=None, scale=True):
    """Read layout from a file

    Parameters
    ----------
    kind : str
        The name of the .lout file (e.g. kind='Vectorview-all' for
        'Vectorview-all.lout'
    names : list of str
        The names to read. If None, all names are returned.
    path : str | None
        The path of the folder containing the Layout file
    scale : bool
        Apply useful scaling for out the box plotting using layout.pos

    Returns
    -------
    layout : instance of Layout
        The layout
    """
    if path is None:
        path = op.dirname(__file__)
    if kind.endswith('.sfp'):
        # EGI geodesic
        dtype = np.dtype('S4, f8, f8, f8')
        fname = op.join(path, kind)
        data = np.loadtxt(fname, dtype=dtype)
        pos = np.c_[data['f1'], data['f2'], data['f3']]
        names_ = data['f0']
    elif kind.endswith('.elc'):
        # 10-5 system
        fname = op.join(path, kind)
        names_ = []
        pos = []
        with open(fname) as fid:
            for line in fid:
                if 'Positions\n' in line:
                    break
            for line in fid:
                if 'Labels\n' in line:
                    break
                pos.append(line)
            for line in fid:
                if not line or not set(line) - set([' ']):
                    break
                names_.append(line.strip(' ').strip('\n'))
        pos = np.loadtxt(BytesIO(''.join(pos)))
    elif kind.endswith('.txt'):
        # easycap
        dtype = np.dtype('S4, f8, f8')
        fname = op.join(path, kind)
        data = np.loadtxt(fname, dtype=dtype, skiprows=1)
        theta, phi = data['f1'], data['f2']
        x, y, z = _sphere_to_cartesian(np.deg2rad(theta),
                                       np.deg2rad(theta), 1.0)
        pos = np.c_[x, y, z]
        names_ = data['f0']
    elif kind.endswith('.csd'):
        # CSD toolbox
        dtype = [('label', 'S4'), ('theta', 'f8'), ('phi', 'f8'),
                 ('radius', 'f8'), ('x', 'f8'), ('y', 'f8'), ('z', 'f8'),
                 ('off_sph', 'f8')]
        fname = op.join(path, kind)
        table = np.loadtxt(fname, skiprows=2, dtype=dtype)
        pos = np.c_[table['x'], table['y'], table['z']]
        names_ = table['label']
    else:
        raise ValueError('Currently %s is not supported.' % kind)

    if names is not None:
        sel, names_ = zip(*[(i, e) for i, e in enumerate(names) if e in names])
        pos = pos[sel]
    kind = op.split(kind)[-1]
    return Montage(pos=pos, names=names_, kind=kind)
