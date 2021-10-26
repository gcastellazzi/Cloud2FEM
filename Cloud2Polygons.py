###############################################################################
# This module contains all the functions that, given a point cloud, allow to
# obtain a set of polygons at specified z coordinates
###############################################################################

## WORK IN PROGRESS !!!!!


import numpy as np



def make_zcoords(a, b, c, d):
    """
    a: zmin
    b: zmax
    c: n° of slices or slices' spacing, depending on param d
    d: 1=fixed number of slices, 2=fixed step height, 3=custom spacing
    
    Given zmin, zmax, param c and the spacing rule, returns a
    1-d numpy array of z coordinates
    """
    if d == 1:
        zcoords = np.linspace(float(a), float(b), int(c))
    elif d == 2:
        zcoords = np.arange(float(a), float(b), float(c))
    elif d == 3:
        pass  ### To be DONE ###########
    return zcoords



def make_slices(zcoords, pcl, thick, npts):
    """
    zcoords: 1-d np array of z coordinates of the slices
    pcl    : 3-columns xyz np array representing the whole point cloud
    thick  : thickness of the slice
    npts   : total number of points of the point cloud
    
    Given zcoords, pcl and the slice thickness, returns the dictionary
    "slices", defined as key=zcoord_i & value=slice_i, 
    where slice_i=np.array([[x1, y1, z1], [x2, y2, z2],..., [xn, yn, zn]]).
    
    npts and npcl are needed only for 3D visualization purposes    
    """
    slices = {}  # Dictionary to be filled with key=zcoord_i, value=slice_i
    invmask = np.ones(npts, dtype=bool)  # For 3D visualization purposes
    
    for z in zcoords:
        mask = np.logical_and(pcl[:, 2] >= (z - thick/2), pcl[:, 2] <= (z + thick/2))
        slices[z] = pcl[mask, :]  # Fill the dict with key=z and value=slice_i
        invmask *= np.invert(mask)  # For 3D visualization purposes
    netpcl = pcl[invmask, :]  # Net point cloud for 3D visualization purposes
    return slices, netpcl








if __name__ == "__main__":
    # SOME TEST CODE
    zcoords1 = make_zcoords(1, 50, 5, 1)
    zcoords2 = make_zcoords(1, 50, 5, 2)

