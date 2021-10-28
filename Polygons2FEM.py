

import numpy as np
import shapely
import shapely.geometry as sg





def make_mesh(xeldim, yeldim, xmin, ymin, xmax, ymax):
    #
    #                    Grid definition 
    #  
    #                ___|_______|_______|___ yn2
    #                   |       |       |
    #                   |       |       |
    #                   |   *   |   *   |  ye1
    #                   |       |       |
    #                ___|_______|_______|___ yn1
    #                   |       |       |
    #                   |       |       |
    #                   |   *   |   *   |  ye0
    #                   |  xe0  |  xe1  |
    #                ___|_______|_______|___ yn0
    #   y|              |       |       |
    #    |____x         |       |       |
    #                  xn0     xn1     xn2
    #
    
    """
    xeldim: Dimension 
    

    """
    xngrid = np.arange(xmin - xeldim, xmax + 2 * xeldim, xeldim)  # x node grid
    xelgrid = xngrid[: -1] + xeldim / 2                               # x element grid
    yngrid = np.arange(ymin - yeldim, ymax + 2 * yeldim, yeldim)
    yelgrid = yngrid[: -1] + yeldim / 2

    # Selects the elements inside the Shapely MultiPolygons
    # and returns a dict of np array whose lines represent an element=[xelgridID, yelgridID]
    import time
    t0 = time.time()
    mct.elemlist = {}
    for z in mct.zcoords:
        initstack = 0
        for x in range(len(mct.xelgrid)):
            for y in range(len(mct.yelgrid)):
                if mct.polygs[z].contains(sg.Point(mct.xelgrid[x], mct.yelgrid[y])):
                    if initstack != 0:
                        mct.elemlist[z] = np.vstack((mct.elemlist[z], np.array([x, y])))
                    else:
                        mct.elemlist[z] = np.array([[x, y]])
                        initstack += 1
    t1 = time.time()
    t = t1 - t0
    print('Shapely code, elapsed time:  ', str(t))

    # Creates the list of nodes and elements connectivity. Elements are extruded from the bottom to the top
    t0 = time.time()

    nodeID = 1              # Node ID
    elID = 1                # Element ID
    mct.nodelist = []
    # mct.elconnect = []
    elconnect = []
    ignore = []  # Nodes to ignore when comparing
    zignore = 0  # Nodes found in the current slice that will be ignored later

    for z in range(len(mct.zcoords)):
        crntz = mct.zcoords[z]              # Current z
        print('GENERATING ELEMENTS FOR SLICE ', crntz)
        if z != len(mct.zcoords) - 1:
            elh = mct.zcoords[z+1] - crntz  # Elements height
        else:
            elh = crntz - mct.zcoords[z-1]  # Height of the elements of the last slice
        abcde = np.array([[0, 1, 2, 3]]) ##################### TEST FOR VSTACK NEW NODES
        z_elconnect = []  ################ TEST FOR VSTACK NEW ELEMENTS
        c_info = 0
        for elem in mct.elemlist[mct.zcoords[z]]:
            # Print info message
            c_info += 1
            if c_info % 1000 == 0:
                print('Zcoord: ', mct.zcoords[z], ', element', c_info, ' of ', mct.elemlist[mct.zcoords[z]].shape[0])
            ###
            tempel = [elID]
            for node in range(8):  # Element node number 0 -> 7
                if node == 0:
                    tempn = [nodeID, mct.xngrid[elem[0]], mct.yngrid[elem[1]], crntz]
                elif node == 1:
                    tempn = [nodeID, mct.xngrid[elem[0] + 1], mct.yngrid[elem[1]], crntz]
                elif node == 2:
                    tempn = [nodeID, mct.xngrid[elem[0] + 1], mct.yngrid[elem[1] + 1], crntz]
                elif node == 3:
                    tempn = [nodeID, mct.xngrid[elem[0]], mct.yngrid[elem[1] + 1], crntz]
                elif node == 4:
                    tempn = [nodeID, mct.xngrid[elem[0]], mct.yngrid[elem[1]], crntz + elh]
                elif node == 5:
                    tempn = [nodeID, mct.xngrid[elem[0] + 1], mct.yngrid[elem[1]], crntz + elh]
                elif node == 6:
                    tempn = [nodeID, mct.xngrid[elem[0] + 1], mct.yngrid[elem[1] + 1], crntz + elh]
                elif node == 7:
                    tempn = [nodeID, mct.xngrid[elem[0]], mct.yngrid[elem[1] + 1], crntz + elh]

                if elID != 1:
                    if z > 2:
                        ignoring = 1  # Comparing only with the nodes in the slice below
                        nexistsxy = np.logical_and(tempn[1] == mct.nodelist[ignore[z-2]:, 1], tempn[2] == mct.nodelist[ignore[z-2]:, 2])
                        nexists = np.where(np.logical_and(nexistsxy == True, tempn[3] == mct.nodelist[ignore[z-2]:, 3]))[0]
                    elif z <= 2:
                        ignoring = 0
                        nexistsxy = np.logical_and(tempn[1] == mct.nodelist[:, 1], tempn[2] == mct.nodelist[:, 2])
                        nexists = np.where(np.logical_and(nexistsxy == True, tempn[3] == mct.nodelist[:, 3]))[0]

                    # Old and slower way to compare nodes ############################
                    # nexistsxy = np.logical_and(tempn[1] == mct.nodelist[:, 1], tempn[2] == mct.nodelist[:, 2])
                    # nexists = np.where(np.logical_and(nexistsxy == True, tempn[3] == mct.nodelist[:, 3]))[0]
                    ##################################################################

                    if len(nexists) == 1:
                        if ignoring == 1:
                            small_nodelist = mct.nodelist[ignore[z - 2]:]
                            tempel.append(small_nodelist[nexists, 0][0])
                        elif ignoring == 0:
                            tempel.append(mct.nodelist[nexists, 0][0])
                    else:
                        mct.nodelist = np.vstack((mct.nodelist, tempn))
                        tempel.append(nodeID)
                        nodeID += 1
                        zignore += 1

                else:
                    if nodeID == 1:
                        mct.nodelist = np.array([tempn])
                        tempel.append(nodeID)
                        nodeID += 1
                    else:
                        mct.nodelist = np.vstack((mct.nodelist, tempn))
                        tempel.append(nodeID)
                        nodeID += 1

            # Add new elements to z_elconnect
            z_elconnect.append(tempel)
            elID += 1

            # Old and slower way of adding new elements ###############
            # if elID != 1:
            #     # Stack the new elements
            #     mct.elconnect = np.vstack((mct.elconnect, tempel))
            #     elID += 1
            # else:
            #     # Store the first element
            #     mct.elconnect = np.array([tempel])
            #     elID += 1
            ###########################################################

        # Add z_elconnect to the list that contains all the elements
        elconnect += z_elconnect
        ignore.append(zignore)

    mct.elconnect = np.array(elconnect)
    t1 = time.time()
    t = t1 - t0
    print('Connectivity generation, elapsed time: ', str(t))
    print('Mesh Generated')

