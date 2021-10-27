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
    zcoords: 1-d np array of z coords as returned by func "make_zcoords()"
    pcl    : 3-columns xyz np array representing the whole point cloud
    thick  : thickness of the slice
    npts   : total number of points of the point cloud
    
    Given zcoords, pcl and the slice thickness, returns the dictionary
    "slices", defined as key=zcoord_i & value=slice_i, 
    where slice_i=np.array([[x1, y1, z1], [x2, y2, z2],..., [xn, yn, zn]]).
    
    npts and netpcl are needed only for 3D visualization purposes, as well as
    for the z coordinates in  slice_i
    """
    slices = {}  # Dictionary to be filled with key=zcoord_i, value=slice_i
    invmask = np.ones(npts, dtype=bool)  # For 3D visualization purposes
    
    for z in zcoords:
        mask = np.logical_and(pcl[:, 2] >= (z - thick/2), pcl[:, 2] <= (z + thick/2))
        slices[z] = pcl[mask, :]  # Fill the dict with key=z and value=slice_i
        invmask *= np.invert(mask)  # For 3D visualization purposes
    netpcl = pcl[invmask, :]  # Net point cloud for 3D visualization purposes
    return slices, netpcl



def find_centroids(minwthick, zcoords, slices, tolsl=10, tolpt=2, tol=0.01, checkpts=0.1, tolincr=1.35):
    """
    minwthick: Minimum wall thickness
    zcoords  : 1-d np array of z coords as that returned by func "make_zcoords()"
    slices   : Dictionary as that returned by function "make_slices()"
    
    tolsl    : Minimum number of pts that a slice must have to be considered, default=10
    tolpt    : Minimum number of points needed to calculate the centroid, default=2
    tol      : Radius of the circle which defines the area where to look for near points, default=0.01 if [m]
    checkpts : Fraction of the slice's points used to derive newtol, default=0.1
    tolincr  : Increment factor used to find the appropriate tolerance, default=1.35
    
    Given the arguments, returns the dictionary ctrds defined as key=zcoord_i &
    value=centroids_i, where centroids_i=np.array([[x1, y1, z1], [x2, y2, z2]....]).
    Z coordinates are stored in centroids_i only for 3D visualization purposes.
    """
    ctrds = {}  # Dict to be filled: key=zcoord_i, value=centroids derived from slice_i
    for z in zcoords:
        
        ##### CALIBRATION OF "tol" FOR EVERY SLICE #####
        # Extract a random subset from the whole slice -> slcheckpts
        slcheckpts = slices[z][np.random.choice(slices[z].shape[0], size=round(slices[z].shape[0] * checkpts), replace=False)]
        newtol = tol  # Only newtol will be used in the following. It could remain equal to tol or be increased
        while True:
            sumnearpts = 0
            for checkpt in slcheckpts:
                # For every point p in slcheckpts, count how many points are at most newtol away from it
                dists = np.sqrt(np.square(slices[z][:, 0] - checkpt[0]) + np.square(slices[z][:, 1] - checkpt[1]))
                nearpts = slices[z][dists <= newtol]
                sumnearpts += nearpts.shape[0]
            if newtol >= minwthick / tolincr:
                print('\nTolerance adopted for slice ', "%.3f" % z, ':', "%.5f" % newtol)
                break
            elif sumnearpts < (3.5 * tolpt * slcheckpts.shape[0]):  # Values smaller than 3tolpt don't work really well. Default = 3.5, grezzo = 15
                newtol *= tolincr
                continue
            else:
                print('\nTolerance adopted for slice ', "%.3f" % z, ':', "%.5f" % newtol)
                break

        ##### PROCEDURE FOR THE FIRST CENTROID #####
        empsl = slices[z][:, [0, 1]]        # Slice (2 columns np array) to be emptied
        if empsl.shape[0] < tolsl:
            ctrds[z] = None
            print("Slice:   ", "%.3f" % z, "            is empty")
            continue
        try:
            while True:
                stpnt = empsl[0]                    # Starting point
                empsl = np.delete(empsl, 0, 0)      # Removes the starting point from empsl
                dists = np.sqrt(np.square(empsl[:, 0] - stpnt[0]) + np.square(empsl[:, 1] - stpnt[1]))
                nearpts = empsl[dists <= newtol]
                if nearpts.shape[0] < tolpt:
                    continue
                ctrds[z] = np.array([[nearpts[:, 0].mean(), nearpts[:, 1].mean(), z]])
                empsl = empsl[dists > newtol]         # Removes the used points from empsl
                ncs = 1                               # Number of found centroids
                break
        except IndexError:
            print("Slice:   ", "%.3f" % z, "        Slice n of points:  ", slices[z].shape[0], "     discarded because n of points to generate the centroids is not sufficient")
            ctrds[z] = None
            continue
        
        ##### PROCEDURE FOR THE FOLLOWING CENTROIDS #####
        while True:
            nearestidx = np.argmin(np.sqrt(np.square(empsl[:, 0] - ctrds[z][ncs-1, 0]) + np.square(empsl[:, 1] - ctrds[z][ncs-1, 1])))
            nearest = empsl[nearestidx]              # The new starting point (nearest to the last found centroid)
            empsl = np.delete(empsl, nearestidx, 0)  # Removes the nearest point (new starting point) from empsl
            dists = np.sqrt(np.square(empsl[:, 0] - nearest[0]) + np.square(empsl[:, 1] - nearest[1]))
            nearpts = empsl[dists <= newtol]
            if nearpts.shape[0] < tolpt and empsl.shape[0] > 0:
                continue
            elif empsl.shape[0] < 1:
                break
            ctrds[z] = np.vstack((ctrds[z], np.array([nearpts[:, 0].mean(), nearpts[:, 1].mean(), z])))
            empsl = empsl[dists > newtol]
            ncs += 1
            if empsl.shape[0] < 1:
                break
        print('Slice:   ', "%.3f" % z, '        Slice n of points:  ', slices[z].shape[0], "     Derived centroids:  ", ctrds[z].shape[0])
    return ctrds
        





















if __name__ == "__main__":
    # SOME TEST CODE
    zcoords1 = make_zcoords(1, 50, 5, 1)
    zcoords2 = make_zcoords(1, 50, 5, 2)

