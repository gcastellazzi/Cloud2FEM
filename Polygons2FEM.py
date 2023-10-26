###############################################################################
# This module contains all the functions that, given a set of slices 
# as Shapely MultiPolygons, allow to derive a 3D voxel mesh that can be 
# exported as an Abaqus .inp file.
###############################################################################



import numpy as np
import shapely.geometry as sg
import time





def make_mesh(xeldim, yeldim, xmin, ymin, xmax, ymax, zcoords, polygs):
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
    """
    xeldim   : Dimension of elements in the x direction
    yeldim   : Dimension of elements in the y direction
    xmin     : Smallest x coordinate of the point cloud
    ymin     : Smallest y coordinate of the point cloud
    xmax     : Biggest x coordinate of the point cloud
    ymax     : Biggest y coordinate of the point cloud
    zcoords  : 1-d np array of z coordinates of the slices
    polygs   : Dictionary with key=zcoords[i], value=Multipolygon
    
    Given the arguments, returns:
    a dictionary elemlist defined as key=zcoords[i] and value=np.array([[x1, y1], [x2, y2], ..., [x3, y3]]), 
    where each row represents the coordinates of the centroid of an element;
    the list of nodes defined as:
    noselist=np.array([[nID1, x1, y1, z1], [nID2, x2, y2, z2], ..., [nIDn, xn, yn, zn]]);
    the connectivity matrix defined as
    elconnect=np.array([[eID1, nID1, nID2, nID3, nID4, nID5, nID6, nID7, nID8], [eID2, nID?, nID?,....,...], [...]])
    """
    xngrid = np.arange(xmin - xeldim, xmax + 2 * xeldim, xeldim)  # x node grid
    xelgrid = xngrid[: -1] + xeldim / 2                           # x element grid
    yngrid = np.arange(ymin - yeldim, ymax + 2 * yeldim, yeldim)  # y node grid
    yelgrid = yngrid[: -1] + yeldim / 2                           # y element grid

    # Find the elements inside the Shapely MultiPolygons and fill a dict of np arrays
    # whose generic row represents an element=[xelgridID, yelgridID]
    t0 = time.time()
    elemlist = {}
    tot_elements = 0  # Total number of elements
    print('Searching for "pixels" inside polygons...')
    for z in zcoords:
        initstack = 0
        for x in range(len(xelgrid)):
            for y in range(len(yelgrid)):
                if polygs[z].contains(sg.Point(xelgrid[x], yelgrid[y])):
                    if initstack != 0:
                        # elemlist[z] = np.vstack((elemlist[z], np.array([x, y]))) # Python .append is much faster than np.vstack
                        elemlist[z].append([x, y])
                        tot_elements += 1
                    else:
                        # elemlist[z] = np.array([[x, y]])  # Python .append is much faster than np.vstack
                        elemlist[z] = [[x, y]]
                        initstack += 1
                        tot_elements += 1
        elemlist[z] = np.array(elemlist[z])
    print('Total number of elements: ', tot_elements)
    t1 = time.time()
    t = t1 - t0
    print('Shapely code, elapsed time:  ', str(t))

    # Create the list of nodes and elements connectivity. Elements are extruded bottom -> top
    t0 = time.time()

    nodeID = 1              # Initlialize node ID
    elID = 1                # Initlialize element ID
    nodelist = []           # Initialize nodelist
    elconnect = []          # Initialize connectivity matrix
    ignore = []             # Initialize  the n° nodes to ignore when comparing
    zignore = 0             # Initialize nodes found in the current slice that will be ignored later
    
    arr_dim = 0.5           # Percentage used to update the length of the nodelist numpy array

    for z in range(len(zcoords)):
        crntz = zcoords[z]              # Current z
        print('Generating elements for slice ', crntz)
        
        # Set the height (z direction) of the elements of the currently analized slice
        if z != len(zcoords) - 1:
            elh = zcoords[z+1] - crntz  # Elements height
        else:
            elh = crntz - zcoords[z-1]  # Height of the elements of the last slice
        
        
        z_elconnect = []  # Initialize connectivity for the current slice
        
        for elem in elemlist[zcoords[z]]:
            
            tempel = [elID]  # To be filled: temporary row of the connectivity matrix
            
            for node in range(8):  # Element node number 0 -> 7
            
                #  Nodes numbering of the eight nodes brick element: top view
                #
                # 3 ______ 2      7 ______ 6
                #  |      |        |      |
                #  |bottom|        | top  |
                #  |______|        |______|
                # 0        1      4        5
                #
                if node == 0:
                    tempn = [nodeID, xngrid[elem[0]], yngrid[elem[1]], crntz]  # Temporary row of the list of nodes
                elif node == 1:
                    tempn = [nodeID, xngrid[elem[0] + 1], yngrid[elem[1]], crntz]  # Temporary row of the list of nodes
                elif node == 2:
                    tempn = [nodeID, xngrid[elem[0] + 1], yngrid[elem[1] + 1], crntz]  # Temporary row of the list of nodes
                elif node == 3:
                    tempn = [nodeID, xngrid[elem[0]], yngrid[elem[1] + 1], crntz]  # ....
                elif node == 4:
                    tempn = [nodeID, xngrid[elem[0]], yngrid[elem[1]], crntz + elh]  # ...
                elif node == 5:
                    tempn = [nodeID, xngrid[elem[0] + 1], yngrid[elem[1]], crntz + elh]
                elif node == 6:
                    tempn = [nodeID, xngrid[elem[0] + 1], yngrid[elem[1] + 1], crntz + elh]
                elif node == 7:
                    tempn = [nodeID, xngrid[elem[0]], yngrid[elem[1] + 1], crntz + elh]

                if elID != 1:
                    # Check if the temporary node tempn has already been generated.
                    # If True, len(nexists)=1 and nexists[0]=index of the existing
                    # node in nodelist that has to be appended to tempel instead of tempn
                    
                    if z > 2:
                        ignoring = 1  # Comparing only with the nodes in the slice below
                        nexistsxy = np.logical_and(tempn[1] == nodelist[ignore[z-2]:nodeID, 1], tempn[2] == nodelist[ignore[z-2]:nodeID, 2])
                        nexists = np.where(np.logical_and(nexistsxy == True, tempn[3] == nodelist[ignore[z-2]:nodeID, 3]))[0]
                    elif z <= 2:
                        ignoring = 0
                        nexistsxy = np.logical_and(tempn[1] == nodelist[:nodeID, 1], tempn[2] == nodelist[:nodeID, 2])
                        nexists = np.where(np.logical_and(nexistsxy == True, tempn[3] == nodelist[:nodeID, 3]))[0]
                        
                    if len(nexists) == 1:
                        if ignoring == 1:
                            small_nodelist = nodelist[ignore[z - 2]:nodeID]
                            tempel.append(small_nodelist[nexists, 0][0])
                        elif ignoring == 0:
                            tempel.append(nodelist[nexists, 0][0])
                    else:
                        try:
                            nodelist[nodeID - 1] = tempn
                        except IndexError:  # If the length of nodelist is not enough, add to it another piece with nan values
                            nodelist = np.vstack((nodelist, np.array([[None, None, None, None]] * int(tot_elements * arr_dim)).astype(np.float32, copy=False)))
                            nodelist[nodeID - 1] = tempn
                            
                        tempel.append(nodeID)
                        nodeID += 1
                        zignore += 1

                elif elID == 1:
                    # The lines of code below are used only for the first defined element
                    if nodeID == 1:
                        nodelist = np.array([[None, None, None, None]] * int(tot_elements * arr_dim)).astype(np.float32, copy=False)
                        nodelist[nodeID - 1] = tempn
                        
                        tempel.append(nodeID)         # Add the nodeID to the temporary row of the connectivity matrix
                        nodeID += 1
                        zignore += 1
                    else:
                        nodelist[nodeID - 1] = tempn
                        
                        tempel.append(nodeID)         # Add the nodeID to the temporary row of the connectivity matrix    
                        nodeID += 1
                        zignore += 1

            # Add new elements to z_elconnect
            z_elconnect.append(tempel)
            elID += 1

        # Add z_elconnect to the list that contains all the elements
        elconnect += z_elconnect
        ignore.append(zignore)
    
    nodelist = nodelist[~np.isnan(nodelist[:, 0])]
    elconnect = np.array(elconnect)
    t1 = time.time()
    t = t1 - t0
    print('Connectivity generation, elapsed time: ', str(t))
    print('Mesh Generated')
    
    return elemlist, nodelist, elconnect





def export_mesh(meshpath, nodelist, elconnect):
    f = open(meshpath, "w")
    
    f.write("*Heading\n")
    f.write("** Generated by: Python Cloud2FEM\n")
    #f.write("*Preprint, echo=NO, model=NO, history=NO, contact=NO\n")
    f.write("**\n** PARTS\n**\n*Part, name=PART-1\n")
    
    f.write("*Node\n")
    zBC_min = 100
    zBC_max = 0
    for node in nodelist:
        nid = str(int(node[0]))
        nx = str("%.8f" % node[1])
        ny = str("%.8f" % node[2])
        nz = str("%.8f" % node[3])
        f.write("      " + nid + ",   " + nx + ",   " + ny + ",   " + nz + "\n")
        if node[3] <  zBC_min:
             zBC_min = node[3]
        
        if node[3] >  zBC_max:
             zBC_max = node[3]

    
    f.write("*Element, type=C3D8\n")
    num_rows, num_cols = elconnect.shape
    for elem in elconnect:
        eid = str(int(elem[0]))
        n1 = str(int(elem[1]))
        n2 = str(int(elem[2]))
        n3 = str(int(elem[3]))
        n4 = str(int(elem[4]))
        n5 = str(int(elem[5]))
        n6 = str(int(elem[6]))
        n7 = str(int(elem[7]))
        n8 = str(int(elem[8]))
        f.write(eid + ", " + n1 + ", " + n2 + ", " + n3 + ", "
                + n4 + ", " + n5 + ", " + n6 + ", " + n7 + ", " + n8 + "\n")
    
    #f.write("*End Part\n")
    # f.write("**\n**\n** ASSEMBLY\n**\n*Assembly, name=Assembly\n")
    # f.write("**\n*Instance, name=WHOLE_MODEL, part=PART-1\n*End Instance\n")
    # f.write("**\n*End Assembly\n")

    f.write("*Elset, elset=SET-ALL, generate\n")
    f.write("1,  " + str(num_rows) + ",    1\n")
    f.write("** Section: SECTION-1\n")
    f.write("*Solid Section, elset=SET-ALL, material=MATERIAL-1\n")
    f.write(",\n")
    f.write("*End Part\n")
    f.write("** \n")  
    f.write("** \n")
    f.write("** ASSEMBLY\n")
    f.write("** \n")
    f.write("*Assembly, name=Assembly\n")
    f.write("** \n")  
    f.write("*Instance, name=WHOLE_MODEL, part=PART-1\n")
    f.write("*End Instance\n")
    f.write("** \n")  
    f.write("*Nset, nset=SET-NODE-AT-BASEMENT, instance=WHOLE_MODEL\n")
    toleranceZ = abs(1e-4 * (zBC_max - zBC_min))
    count = 0
    for node in nodelist:
        nid = str(int(node[0]))
        nz = str("%.8f" % node[3])
        if abs(node[3] -  zBC_min) < toleranceZ:
            f.write(str(int(nid)) + ",  ")
            count = count +1
            if (count % 16) == 0:
                f.write( "\n")
    
    f.write("\n")
    f.write("*End Assembly\n")
    f.write("** \n")
    f.write("** MATERIALS\n")
    f.write("** \n")
    f.write("*Material, name=MATERIAL-1\n")
    f.write("*Density\n")
    f.write("1800.,\n")
    f.write("*Elastic\n")
    f.write("3000000000., 0.2\n")
    f.write("** \n")
    f.write("** BOUNDARY CONDITIONS\n")
    f.write("** \n")
    f.write("** Name: BC-Basement Type: Displacement/Rotation\n")
    f.write("*Boundary\n")
    f.write("SET-NODE-AT-BASEMENT, 1, 1\n")
    f.write("SET-NODE-AT-BASEMENT, 2, 2\n")
    f.write("SET-NODE-AT-BASEMENT, 3, 3\n")
    f.write("** ----------------------------------------------------------------\n")
    f.write("** \n")
    f.write("** STEP: Step-1\n")
    f.write("** \n")
    f.write("*Step, name=Step-1, nlgeom=NO, perturbation\n")
    f.write("*Static\n")
    f.write("** \n")
    f.write("** LOADS\n")
    f.write("** \n")
    f.write("** Name: Load-1   Type: Gravity\n")
    f.write("*Dload\n")
    f.write(", GRAV, 9.81, 0., 0., -1.\n")
    f.write("** \n")
    f.write("** OUTPUT REQUESTS\n")
    f.write("** \n")
    f.write("** \n")
    f.write("** FIELD OUTPUT: F-Output-1\n")
    f.write("** \n")
    f.write("*Output, field, variable=PRESELECT\n")
    f.write("** \n")
    f.write("** HISTORY OUTPUT: H-Output-1\n")
    f.write("** \n")
    f.write("*Output, history, variable=PRESELECT\n")
    f.write("*End Step\n")
    # f.write("** ----------------------------------------------------------------\n")
    # f.write("** \n")
    # f.write("** STEP: Step-2\n")
    # f.write("** \n")
    # f.write("*Step, name=Step-2, nlgeom=NO, perturbation\n")
    # f.write("Frequency, eigensolver=Lanczos, acoustic coupling=on, normalization=displacement\n")
    # f.write("20, , , , , \n")
    # f.write("** \n")
    # f.write("** OUTPUT REQUESTS\n")
    # f.write("** \n")
    # #f.write("*Restart, write, frequency=0\n")
    # f.write("** \n")
    # f.write("** FIELD OUTPUT: F-Output-2\n")
    # f.write("** \n")
    # f.write("*Output, field, variable=PRESELECT\n")
    # f.write("*End Step\n")
    
    f.close()















































####################################################################################################
############ 
############    TEST: EXPORT MESH AFTER CONVERSION TO TET ELEMENTS
############    TO BE ADJUSTED
############    NEEDS FEMFUNCTIONS MODULE

# def exp_mesh_func():
#     try:
#         fd = QFileDialog()
#         meshpath = fd.getSaveFileName(parent=None, caption="Export DXF", directory="", filter="Abaqus Input File (*.inp)")[0]
#         f = open(meshpath, "w")
#
#         f.write("*Node\n")
#         for node in mct.nodelist:
#             nid = str(int(node[0]))
#             nx = str("%.8f" % node[1])
#             ny = str("%.8f" % node[2])
#             nz = str("%.8f" % node[3])
#             f.write("      " + nid + ",   " + nx + ",   " + ny + ",   " + nz + "\n")
#
#         f.write("*Element, type=C3D4\n")
#         T4_LCO = ff.H8_to_T4_elements(mct.elconnect[:, 1:], 1)
#         for i in range(T4_LCO.shape[0]):
#             eid = str(i+1)
#             n1 = str(int(T4_LCO[i, 0]))
#             n2 = str(int(T4_LCO[i, 1]))
#             n3 = str(int(T4_LCO[i, 2]))
#             n4 = str(int(T4_LCO[i, 3]))
#             f.write(eid + ", " + n1 + ", " + n2 + ", " + n3 + ", "
#                     + n4 + "\n")
#         f.close()
#
#         msg_dxfok = QMessageBox()
#         msg_dxfok.setWindowTitle('Mesh Export')
#         msg_dxfok.setText('File saved in: \n' + meshpath + '                       ')
#         x = msg_dxfok.exec_()
#
#     except (ValueError, TypeError, FileNotFoundError):
#         print('No .inp name specified')
#########################################################################################
#########################################################################################





