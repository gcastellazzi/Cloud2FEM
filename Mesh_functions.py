#
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 08:13:29 2021

@author: giovanni.castellazzi
"""

import numpy as np
from matplotlib import pyplot

import mpl_toolkits.mplot3d as a3
import matplotlib.colors as colors
import pylab as pl
import multiprocessing
from itertools import permutations
import time

###############################################################################

# def index_elements(LCO,xyz):
#         for i in range(len(LCO)):
#             index_node_names = [LCO[i][idx]-1 for idx in [0, 1, 2, 3, 4, 5, 6, 7]]
#             zm = [np.mean(xyz[index_node_names,0])]


def find_pixel(LCO, xyz, zcoords):
    start_time = time.time()                
    tol = 1e-4
    sorted_faces = []
    for coord in zcoords:
        potential_faces = []
        for i in range(len(LCO)):
            index_node_names = [LCO[i][idx]-1 for idx in [0, 1, 2, 3]]
            vzm = [np.mean(xyz[index_node_names,:],0)]
            if abs(vzm[0][3] - coord)< tol:
                potential_faces.append((vzm[0][3], i, index_node_names))
        sorted_faces.extend(potential_faces)
    sorted_faces = sorted(sorted_faces, key=lambda x: x[0])
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time Pixel function: {elapsed_time:.2f} seconds")
    return sorted_faces

def find_pixel_xy(LCO, xyz, xy_coords_pairs):
    # Remember:
    # faces = {
    #     1: [0, 1, 2, 3],
    #     2: [0, 1, 5, 4],
    #     3: [1, 2, 6, 5],
    #     4: [2, 3, 7, 6],
    #     5: [3, 0, 4, 7],
    #     6: [5, 6, 7, 4]
    # }
    start_time = time.time()                
    tol = 1e-4
    sorted_faces_x = []
    sorted_faces_y = []
    for coord_x, coord_y in zip(xy_coords_pairs[0], xy_coords_pairs[1]):
        potential_faces_x = []
        potential_faces_y = []
        for i in range(len(LCO)):
            index_node_names_x = [LCO[i][idx]-1 for idx in [3, 0, 4, 7]] # face n.5
            index_node_names_y = [LCO[i][idx]-1 for idx in [0, 1, 5, 4]] # face n.2
            vxm = [np.mean(xyz[index_node_names_x,:],0)]
            vym = [np.mean(xyz[index_node_names_y,:],0)]
            if abs(vxm[0][1] - coord_x)< tol:
                potential_faces_x.append((vxm[0][1], i, index_node_names_x))
            if abs(vym[0][2] - coord_y)< tol:
                potential_faces_y.append((vym[0][2], i, index_node_names_y))
        sorted_faces_x.extend(potential_faces_x)
        sorted_faces_y.extend(potential_faces_y)
    # boundary faces:
    coord_x = xy_coords_pairs[0][-1]
    coord_y = xy_coords_pairs[1][-1]
    for i in range(len(LCO)):
        index_node_names_x = [LCO[i][idx]-1 for idx in [1, 2, 6, 5]] # face n.3
        index_node_names_y = [LCO[i][idx]-1 for idx in [2, 3, 7, 6]] # face n.4
        vxm = [np.mean(xyz[index_node_names_x,:],0)]
        vym = [np.mean(xyz[index_node_names_y,:],0)]
        if abs(vxm[0][1] - coord_x)< tol:
            potential_faces_x.append((vxm[0][1], i, index_node_names_x))
        if abs(vym[0][2] - coord_y)< tol:
            potential_faces_y.append((vym[0][2], i, index_node_names_y))
    sorted_faces_x.extend(potential_faces_x)
    sorted_faces_y.extend(potential_faces_y)

    sorted_faces_x = sorted(sorted_faces_x, key=lambda x: x[0])
    sorted_faces_y = sorted(sorted_faces_y, key=lambda x: x[0])
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time Pixel xy function: {elapsed_time:.2f} seconds")
    return sorted_faces_x, sorted_faces_y


def find_internal_faces(LCO_matrix, xyz):
    try:
        if LCO_matrix.shape[0] < 2:
            raise ValueError("At least two elements are required in the LCO matrix.")
    except:
        ValueError("At least two elements are required in the LCO matrix.")
        internal_faces = []
    
    # Define the faces using the specified indices
    faces = {
        1: [0, 1, 2, 3],
        2: [0, 1, 5, 4],
        3: [1, 2, 6, 5],
        4: [2, 3, 7, 6],
        5: [3, 0, 4, 7],
        6: [4, 5, 6, 7]
    }
    
    # Find internal faces between all pairs of elements
    internal_faces = []
    internal_faces_average_x = []
    internal_faces_average_y = []
    internal_faces_average_z = []
    for i in range(len(LCO_matrix)):
        for j in range(i + 1, len(LCO_matrix)):
            # Find the indices within the lines in the LCO matrix that are common to both rows
            common_indices = [idx for idx, val in enumerate(LCO_matrix[i]) if val in LCO_matrix[j]]
            
            # Check if there are exactly 4 common indices, and if they form one of the defined faces
            if len(common_indices) == 4:
                potential_faces = []
                potential_faces_average_x = []
                potential_faces_average_y = []
                potential_faces_average_z = []
                for face, indices in faces.items():
                    if set(indices) == set(common_indices):
                        # Extract the names of the common nodes
                        node_names = [LCO_matrix[i][idx] for idx in indices]
                        index_node_names = [LCO_matrix[i][idx-1] for idx in indices]
                        potential_faces.append((i+1, j+1, face, node_names))
    #                    potential_faces_average_x.append([np.mean(xyz[index_node_names,0]), node_names])
    #                    potential_faces_average_y.append([np.mean(xyz[index_node_names,1]), node_names])
    #                    potential_faces_average_z.append([np.mean(xyz[index_node_names,2]), node_names])
                internal_faces.extend(potential_faces)
    #            internal_faces_average_x.extend(potential_faces_average_x)
    #            internal_faces_average_y.extend(potential_faces_average_y)
    #            internal_faces_average_z.extend(potential_faces_average_z)
    #internal_faces_average_x = sorted(internal_faces_average_x, key=lambda x: x[0])
    #internal_faces_average_y = sorted(internal_faces_average_y, key=lambda x: x[0])
    #internal_faces_average_z = sorted(internal_faces_average_z, key=lambda x: x[0])
    #print ("Combination ", str(i), " done!")
    return internal_faces #, internal_faces_average_x, internal_faces_average_y, internal_faces_average_z






def find_external_faces(LCO_matrix):
    num_elements = len(LCO_matrix)
    
    # Define the faces using the specified indices
    faces = {
        1: [0, 1, 2, 3],
        2: [0, 1, 5, 4],
        3: [1, 2, 6, 5],
        4: [2, 3, 7, 6],
        5: [3, 0, 4, 7],
        6: [5, 6, 7, 4]
    }
    face_list = []
    all_faces = set()  # Initialize an empty set
    for j in range(len(LCO_matrix)):
        #
        for face in faces.values():
            count = 0
            face_permutations = list(permutations(LCO_matrix[j, face]))
            for perm in face_permutations:
                if list(perm) not in face_list:
                    if count == 0:
                        face_list.append(list(perm))
                        all_faces.add(tuple(perm))
                        count = 1
    
    # Find internal faces
    face_list = []
    items_to_remove = set()
    internal_face_database = find_internal_faces(LCO_matrix)
    for i in range(len(internal_face_database)):
        face_list.append(tuple(internal_face_database[i][3]))
    internal_faces  = set(face_list)
    
    # Calculate external faces by subtracting internal faces from all faces
    # external_faces = all_faces - internal_faces
    for face in all_faces:
        count = 0
        face_permutations = list(permutations(face))
        for perm in face_permutations:
            if set({perm}).issubset(internal_faces):
                for perm2 in face_permutations:
                    if count == 0:
                        items_to_remove.add(perm2)
                        count = 1
    external_faces = all_faces
    external_faces.difference_update(items_to_remove)
    return external_faces
###############################################################################


def compare_rows(i, row_sets, connectivity_matrix, result, lock):
    shared_count = 0
    for j in range(i + 1, len(connectivity_matrix)):
        common_elements = row_sets[i] & row_sets[j]
        if len(common_elements) >= 3:
            shared_count += 1
    if shared_count < 3:
        with lock:
            result.append(i)

def connectivity_check_consitency_parallel(connectivity_matrix):
    result = []
    row_sets = [set(row) for row in connectivity_matrix]
    lock = multiprocessing.Lock()
    
    processes = []
    for i in range(len(connectivity_matrix)):
        process = multiprocessing.Process(target=compare_rows, args=(i, row_sets, connectivity_matrix, result, lock))
        processes.append(process)
        process.start()
    
    for process in processes:
        process.join()
    
    return result

def connectivity_check_consitency_parallel_ncores(connectivity_matrix, num_cores):
    result = []
    row_sets = [set(row) for row in connectivity_matrix]
    
    with multiprocessing.Pool(processes=num_cores) as pool:
        pool.starmap(compare_rows, [(i, row_sets, connectivity_matrix, result) for i in range(len(connectivity_matrix))])
    
    return result

def connectivity_check_consitency(connectivity_matrix):
    result = []
    row_sets = [set(row) for row in connectivity_matrix]
    
    for i in range(len(connectivity_matrix)):
        shared_count = 0
        for j in range(i + 1, len(connectivity_matrix)):
            common_elements = row_sets[i] & row_sets[j]
            if len(common_elements) >= 3:
                shared_count += 1
        if shared_count < 3:
            result.append(i)
    
    return result

def connectivity_check_consitency_OLD(LCO):
    # return a list of elements that are not well connected with other elements
    # if a H8 element is connected with less than 3 nodes then it would lead
    # to a not consistent mesh
    #
    # first implementation brute force - to be optimized
    nodes = np.unique(LCO)
    count = np.zeros(len(nodes))
    problematic_elements = []
    LCOc = LCO*0
    try: 
        for k in np.arange(len(nodes)):
            for i in np.arange(LCO.shape[0]):
                for j in np.arange(LCO.shape[1]):
                    if nodes[k] == LCO[i][j]:
                        count[k] = count[k]+1
        for elem in np.arange(LCO.shape[0]):
            LCOc[elem]= count[LCO[elem]-1]
            a, repetitions = np.unique(LCOc[elem], return_counts=True)
            if LCO.shape[1]==8:
                if repetitions[0]>5:
                    print('## WARNING: element N.', elem+1, 'is badly connected')
                    problematic_elements.append(elem+1)
            elif LCO.shape[1]==4:
                if repetitions[0]>1:
                    print('##WARNING: element N.', elem+1, 'is badly connected')
                    problematic_elements.append(elem+1)
    except TypeError:
        print('some problems in connectivity_check_consitency function')
    return problematic_elements

###############################################################################

def H8_to_T4_elements(H8_LCO, scheme):
    # xyz is the coordinate matrix, the line number is the node number
    # H8_LCO is the connectivity matrix, the line number is the Element number
    # two possible definitions of T4 connectivity are possible using the scheme option
    if scheme == 0:
        t4i = np.array([[1, 2, 5, 8],
                         [1, 2, 4, 8],
                         [2, 3, 4, 8 ],
                         [3, 7, 8, 2],
                         [8, 6, 7, 2],
                         [5, 6, 8, 2]]) # first
    elif scheme == 1:
        t4i = np.array([[8, 4, 7, 5],
                         [6, 7, 2, 5],
                         [3, 4, 2, 7],
                         [1, 2, 4, 5],
                         [7, 4, 2, 5]]) # first
    elif scheme == 2:
        t4i = np.array([[7, 3, 6, 8],
                         [5, 8, 6, 1],
                         [2, 3, 1, 6],
                         [4, 1, 3, 8],
                         [6, 3, 1, 8]]) # second (reversed)
        print('[reversed scheme]')
    #
    ncells = np.size(H8_LCO, 0)
    #    print('total number of H8 elements: ', ncells)
    T4_LCO = np.zeros(ncells*t4i.shape[0]*t4i.shape[1]).reshape(ncells*t4i.shape[0],t4i.shape[1])
    for ne in np.arange(ncells):
        for j in np.arange(t4i.shape[0]):
            T4_LCO[t4i.shape[0]*(ne)+j]= H8_LCO[ne][t4i[j]-1]
    T4_LCO = T4_LCO.astype(int)
    print(ncells, 'H8 elements succesfuly transformed into', T4_LCO.shape[0], 'T4 elements!' )
    return T4_LCO

################################################################################

    
def plot_simple_mesh(xyz, LCO, nfig, ax, color, options):
    H8_faces = np.array([[1, 2, 3, 4],
                      [1, 2, 6, 5],
                      [2, 3, 7, 6],
                      [3, 4, 8, 7],
                      [4, 1, 5, 8],
                      [5, 6, 7, 8]])
    T4_faces = np.array([[1, 2, 3],
                         [1, 2, 4],
                         [2, 3, 4],
                         [3, 1, 4]])
    #ax = a3.Axes3D(pl.figure(nfig))
    #ax.gca().set_aspect('equal')
    #ax.set_aspect('equal')
    for i in np.arange(LCO.shape[0]):
        if LCO.shape[1] == 8:
            faces = H8_faces
        elif LCO.shape[1]==4:
            faces = T4_faces
        LCOi = LCO.astype(int)    
        for j in np.arange(faces.shape[0]):
            #print(i, j)
            vtx = xyz[LCOi[i,faces[j,:]-1]-1,:]
            #print(vtx)
            tri = a3.art3d.Poly3DCollection([vtx])
            tri.set_alpha(0.5)
            tri.set_color(colors.rgb2hex([.8, .8, .8]))
            tri.set_edgecolor(color)
            
            ax.add_collection3d(tri)
    ax.set_xlim(min(xyz[:,0]), max(xyz[:,0]))
    ax.set_ylim(min(xyz[:,1]), max(xyz[:,1]))
    ax.set_zlim(min(xyz[:,2]), max(xyz[:,2]))
    if options:
        for i, txt in enumerate(xyz[:,1]):
            ax.text(xyz[i,0], xyz[i,1], xyz[i,2], '%s' % (str(i+1)), size=10, zorder=1, color='k')
    #
    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_zlabel('Z axis')
    #pl.show()
    
    return ax

##############################################################################
    
    
def plot_boundary_mesh(xyz, element_faces, boundary_faces, nfig, ax):

    #ax.gca().set_aspect('equal')
    #ax.set_aspect('equal')
    for i in np.arange(len(element_faces)):
        #print(i, j)
        vtx = xyz[element_faces[i]-1,:]
        #print(vtx)
        tri = a3.art3d.Poly3DCollection([vtx])
        tri.set_alpha(0.5)
        if boundary_faces[i]==1:
            tri.set_color(colors.rgb2hex([.8, .2, .2]))
        elif boundary_faces[i]==0:
            tri.set_color(colors.rgb2hex([.2, .8, .2]))
        tri.set_edgecolor('r')
        ax.add_collection3d(tri)
        
           

    #
    #pl.show()
    return ax
    

##############################################################################
    
def get_boundary_faces(LCO, xyz):
    # return a list of elements that are not well connected with other elements
    # if a H8 element is connected with less than 3 nodes then it would lead
    # to a not consistent mesh
    #
    # first implementation brute force - to be optimized
    # faces connectivity definition
    H8_faces = np.array([[1, 2, 3, 4],
                      [1, 2, 6, 5],
                      [2, 3, 7, 6],
                      [3, 4, 8, 7],
                      [4, 1, 5, 8],
                      [5, 6, 7, 8]])
    T4_faces = np.array([[1, 2, 3],
                         [1, 2, 4],
                         [2, 3, 4],
                         [3, 1, 4]])
    #
    nodes = np.unique(LCO)
    count = np.zeros(len(nodes))
    boundary_faces = []
    repetitions = []
    nfa = 0
    nba = 0
    belongs_to_element = []
    normals = []
    if LCO.shape[1] == 8:
        faces = H8_faces
    elif LCO.shape[1]==4:
        faces = T4_faces
        
    elements_faces = faces[0,:]
    #LCOf = np.zeros(LCO.shape[0]*faces.shape[0]*faces.shape[1])
    #LCOf = LCOf.reshape(LCO.shape[0]*faces.shape[0],faces.shape[1])
    LCOf = []
    # check how many times the node is shared by elements
    for k in np.arange(len(nodes)):
        for i in np.arange(LCO.shape[0]):
            for j in np.arange(LCO.shape[1]):
                if nodes[k] == LCO[i][j]:
                    count[k] = count[k]+1
                    
    LCOi = LCO.astype(int)
    for elem in np.arange(LCO.shape[0]):
        centroid = np.array([np.mean(xyz[LCOi[elem]-1,0]), np.mean(xyz[LCOi[elem]-1,1]), np.mean(xyz[LCOi[elem]-1,2])])
        for nface in np.arange(faces.shape[0]):
            #print('elemento: ', elem+1, ' faccia :', nface+1, ' nodi faccia: ', LCO[elem, faces[nface]-1])            
            #LCOf[elem]= count[LCO[elem, faces[nface]-1]-1]
            LCOf.append(count[LCOi[elem, faces[nface]-1]-1])
#            elements_faces.append(LCO[elem, faces[nface]-1])
            face = LCOi[elem, faces[nface]-1]
#            print('size element face: ', elements_faces.shape[1])
            if nfa == 0:
                elements_faces = face
                repetitions = face
#                print('first ', elements_faces)
            elif nfa > 0:
                elements_faces = np.vstack([elements_faces, face])
#                print(' more: ', elements_faces)
            
            #
            belongs_to_element.append(elem+1)
#            print('xyz index ', face-1)
            face_centroid = np.array([np.mean(xyz[face-1,0]), np.mean(xyz[face-1,1]), np.mean(xyz[face-1,2])])
            versus = np.sign(face_centroid - centroid)
#            print('versus', versus)
            normal = np.multiply(compute_face_normal(xyz, face, LCO[elem]),versus)
#           
            
#            print('n dopo ' , normals[-1])
            boundary_faces.append(0)
#            print('ripetizioni per nodo: ', LCOf[-1])
            a, repetition = np.unique(LCOf[nfa], return_counts=True)
            #print(a, repetitions)
            #print(faces.shape[1])
            if (max(repetition) < faces.shape[1] or np.unique(a)==1 or (max(repetition) == faces.shape[1] and np.unique(a)==2)):
                boundary_faces[nfa] = 1
                nba += 1
#            print(repetition)
#            print('normal ', normal)
            if nfa == 0:
                normals = normal
                repetitions = LCOf[nfa]
#                print('first ', elements_faces)
            elif nfa > 0:
                normals = np.vstack([normals, normal])
                repetitions = np.vstack([repetitions, LCOf[nfa]])
#                print(' more: ', elements_faces)
                
            #elif (max(repetitions) == faces.shape[1] and np.unique(a)==2):
            #    boundary_faces[-1] = 1
            nfa = nfa + 1
#            print('naface ' , nface)
            #
#    print('element faces ', elements_faces)
    for nf1 in np.arange(len(boundary_faces)-1):
        for nf2 in np.arange(len(boundary_faces)-1):
#            print('is ', np.unique(elements_faces[nf1]), ' equal to ', np.unique(elements_faces[nf2]), '?')
            if (np.array_equal(np.unique(elements_faces[nf1]), np.unique(elements_faces[nf2])) and nf1!=nf2):
                boundary_faces[nf1] = 0
                nba -= 1
                #print(' value changed to 0')
#    nm = np.zeros(shape=(len(normals),len(normals[0])))
    #nm = nm.reshape(len(normals),len(normals[0]))
    
#    for nf in np.arange(len(normals)-1):
#        print(nf)
#        print(normals[nf-1][0])
#        nm[nf,:] = normals[nf-1][0]    
    print('The mesh possesses', nba, 'boundary faces')
    return boundary_faces, elements_faces, normals, belongs_to_element, repetitions
##############################################################################
   
#
def compute_face_normal(xyz, face, LCO):
#    print(face_connectivity)
#    faces = np.zeros(shape=(len(face_connectivity),len(face_connectivity[0])))
    #faces = np.zeros(len(face_connectivity)*len(face_connectivity[0]))
    #faces = faces.reshape(len(face_connectivity),len(face_connectivity[0]))
       
#        
#    for j in np.arange(len(face_connectivity)):
        # print(j)
        #        print(face_connectivity[j])
#        faces[j] = face_connectivity[j]
    xyz = xyz.astype(np.float)
    #norm = np.zeros( xyz.shape, dtype=xyz.dtype )
    #Create an indexed view into the vertex array using the array of three indices for triangles
#    print('faces ', faces[::,0:3])
    face = face.astype(np.int)
#    print('face', face)
    tris = xyz[face[[0, 1, 2]]-1]
#    print('tris', tris)
#    print('tris comp', tris[:,1], tris[:,0], tris[:,1]-tris[:,0])
#    print('tris ', tris)
    #Calculate the normal for all the triangles, by taking the cross product of the vectors v1-v0, and v2-v0 in each triangle             
#    print(tris)
#    print(tris[0,2 ]-tris[0,0])
#    n = np.cross( tris[::,1 ] - tris[::,0]  , tris[::,2 ] - tris[::,0] )
    n = np.cross( tris[1, : ] - tris[0, :]  , tris[2, : ] - tris[0, :] )
#    print('n ', n)
    # n is now an array of normals per triangle. The length of each normal is dependent the vertices, 
    # we need to normalize these, so that our next step weights each normal equally.
    normals = normalize_v3_1D(n)
#    print('normals 1 ' ,normals)
#    # now we have a normalized array of normals, one per triangle, i.e., per triangle normals.
#    # But instead of one per triangle (i.e., flat shading), we add to each vertex in that triangle, 
#    # the triangles' normal. Multiple triangles would then contribute to every vertex, so we need to normalize again afterwards.
#    # The cool part, we can actually add the normals through an indexed view of our (zeroed) per vertex normal array
#    
#    norm[ faces[:,0]-1 ] += n
#    norm[ faces[:,1]-1 ] += n
#    norm[ faces[:,-1]-1 ] += n
#    
#    normals = normalize_v3(norm)
    #       
    return normals     
#############################################################################  
def normalize_v3_nD(arr):
#    print(arr)
    ''' Normalize a numpy array of 3 component vectors shape=(n,3) '''
    lens = np.sqrt( arr[:,0]**2 + arr[:,1]**2 + arr[:,2]**2 )
#    print('lens', lens)
#    print('arr ', arr)
    arr[:,0] /= lens
    arr[:,1] /= lens
    arr[:,2] /= lens                
    return arr
#############################################################################
def normalize_v3_1D(arr):
#    print(arr)
    ''' Normalize a numpy array of 3 component vectors shape=(n,3) '''
    lens = np.sqrt( arr[0]**2 + arr[1]**2 + arr[2]**2 )
#    print(arr[0], '/',lens)
#    print('lens', lens)
#    print('arr ', arr)
    if lens > 0:
        arr[0] = arr[0]/lens
        arr[1] = arr[1]/lens
        arr[2] = arr[2]/lens               
    
    return arr
#############################################################################
def adjust_voxelized_mesh(xyz, LCO, normals, boundary_faces, element_faces, belongs_to_element, repetitions, nfig, ax):
#    print(normals)
#    print(element_faces)
#    print(len(boundary_faces))
#    print(repetitions)
    t4ij =np.array([[0,0,0,0]])
    it4 = 0
    for j in np.arange(len(boundary_faces)):
        if normals[j,2] == 1:# or normals[j,2] == -1 :
#                print('Face ', j+1, ' is Z+', '(element: ', belongs_to_element[j], ')' )
#                print(np.where(normals[:,0]!=0), np.where(normals[:,1]!=0))
#                print(element_faces[j])
#                
#                print(element_faces[j,[0,1]])
#                print(element_faces[j,[1,2]])
#                print(element_faces[j,[2,3]])
#                print(element_faces[j,[3,0]])
#                #plot_boundary_mesh(xyz, element_faces[j-1], boundary_faces[j-1], nfig, ax)
#                print(LCO[belongs_to_element[j]-1])
                # cerco la faccia con normale X+ o X- o Y- o Y+
            for k in np.arange(len(boundary_faces)):
                if belongs_to_element[j]!= belongs_to_element[k] and boundary_faces[j] == 1 and boundary_faces[k] == 1:
                    p = [0, 1, 2, 3, 0]
                    for d in np.arange(len(element_faces[j])-1):
                        
                        #for dk in np.arange(len(element_faces[j])-1):
                        if (normals[k,0] == 1 or normals[k,0] == -1) and (element_faces[j,[p[d]]] in element_faces[k])  and (element_faces[j,[p[d+1]]] in element_faces[k]) :#
                            print('1')
                            print(element_faces[j,[p[d],p[d+1]]],j+1, k+1)
                            print(element_faces[j])
                            print(np.where(element_faces[j]== element_faces[j,[p[d]]]))
                            print(np.where(element_faces[j]== element_faces[j,[p[d+1]]]))
                            print(element_faces[k])
                            print(np.where(element_faces[k]== element_faces[j,[p[d]]]))
                            print(np.where(element_faces[k]== element_faces[j,[p[d+1]]]))
#                            print('differenza', np.setdiff1d(element_faces[k],element_faces[j,[p[d],p[d+1]]]))
                            LCOt = np.concatenate((element_faces[j], np.setdiff1d(element_faces[k],element_faces[j,[p[d],p[d+1]]]) ))
#                            print('aggiunta', np.concatenate((element_faces[j], np.setdiff1d(element_faces[k],element_faces[j,[p[d],p[d+1]]]) )))
#                            print(pippo)
                            indicator = np.where(element_faces[j] == element_faces[j,[p[d]]])
#                            print(indicator[0][0])
                            if indicator[0][0] == 1:
                                per = [1,2,3,4,5,6]
                            elif indicator[0][0] == 2:
                                per = [4,1,2,3,5,6]
                            elif indicator[0][0] == 3:
                                per = [3,4,1,2,5,6]
                            elif indicator[0][0] == 0:
                                per = [2,3,4,1,5,6]
                            T4conn = np.array([[1, 2, 3, 5],
                                              [1,3,4,5],
                                              [3,4,5,6]])
                            for jj in np.arange(T4conn.shape[0]):
#                                print(t4ij)
                                ieT4 = LCOt[T4conn[jj]-1]
#                                print(it4)
                                if it4 == 0:
                                    t4ij= ieT4
                                elif it4 > 0:
                                    t4ij = np.vstack([t4ij,ieT4])
#                                print(t4ij)
                                it4 += 1
#                                print(t4ij)
#                            print(element_faces[k,[p[d],p[d+1]]],k+1)
#                            print(element_faces[j],j+1)
#                            print(element_faces[k],k+1)
#                        elif (normals[k,0] == 1 or normals[k,0] == -1) and (element_faces[j,[p[d+1]]] in element_faces[k])  :#
#                            print('2')
#                            print(element_faces[j,[p[d],p[d+1]]],j+1, k+1)
#                            print(element_faces[k,[p[d],p[d+1]]],k+1)
#                            print(element_faces[j],j+1)
#                            print(element_faces[k],k+1)
    #newLCO     

    return t4ij     
############################################################################### 
#############################################################################
 
## EXAMPLE
##################################################################     EXAMPLE
##########################################################################################################################################
##########################################################################################################################################
##########################################################################################################################################

if __name__ == "__main__":
    
    import matplotlib.pyplot as plt
    
    xyz = np.array([[0,0,0],
             [1,0,0],
             [1,1,0],
             [0,1,0],
             [0,0,1],
             [1,0,1],
             [1,1,1],
             [0,1,1],
             [2,0,0],
             [2,1,0],
             [2,0,1],
             [2,1,1],#
             [3,0,1],
             [3,1,1],
             [2,0,2],
             [3,0,2],
             [3,1,2],
             [2,1,2],
             [-1, 0, 1],
             [-1, 1, 1],
             [0, 0, 2],
             [0, 1, 2],
             [-1, 1, 2],
             [-1, 0, 2] ])
    H8_LCO = np.array([[1, 2, 3, 4, 5, 6, 7, 8],
                    [2, 9,10, 3, 6,11,12, 7],
                    [11, 13, 14, 12, 15, 16, 17, 18],
                    [5, 8, 20, 19, 21, 22, 23, 24]])
    
    ## Transform a H8 connectivity - method 1
    T4_LCO = H8_to_T4_elements( H8_LCO, 0)
    # T4_LCO = H8_to_T4_elements( H8_LCO, 2) # method 2
    #print('old connctivity based on H8: ', H8_LCO)
    #print('new connctivity based on T4: ', T4_LCO)
    #
    # problematic_elements_H8 = connectivity_check_consitency(H8_LCO)
    # if len(problematic_elements_H8)>0:
    #     print('problemi H8', problematic_elements_H8)
    # #
    # problematic_elements_T4 = connectivity_check_consitency(T4_LCO)
    # if len(problematic_elements_T4)>0:
    #     print('problemi T4', problematic_elements_T4)

    # nfig = 1
    # color = 'k'
    # ax = a3.Axes3D(pl.figure(nfig))
    # ax = plot_simple_mesh(xyz, H8_LCO, nfig, ax, color)
    # boundary_faces, element_faces, normals, belongs_to_element, repetitions = get_boundary_faces(H8_LCO)

    # print(boundary_faces)
    # element_faces
    # ax = plot_boundary_mesh(xyz, element_faces, boundary_faces, nfig, ax)
    # pl.show()

    # nfig = 2
    # plot_simple_mesh(xyz, T4_LCO, nfig, ax, color)
    # boundary_faces, element_faces, normals, belongs_to_element, repetitions = get_boundary_faces(T4_LCO)
    # #print(boundary_faces)
    # #element_faces
    # plot_boundary_mesh(xyz, element_faces, boundary_faces, nfig, ax)

    # #normals = compute_face_normal(xyz, element_faces, H8_LCO)
    # newLCOv = adjust_voxelized_mesh(xyz, H8_LCO, normals, boundary_faces, element_faces, belongs_to_element, repetitions, nfig, ax)
    # #print(newLCOv)
    # color = 'r'
    # ax = plot_simple_mesh(xyz, newLCOv, nfig, ax, color)
    
    # # Plot everything in 3D
    # fig = plt.figure()
    # fig.subplots_adjust(wspace=0.2, hspace=0.2)   
    # fig.suptitle('From a Point cloud to MultiPolygons')
    # axs = [fig.add_subplot(2, 3, n, projection='3d') for n in range(1, 7)]
    
    # axs[0].set_title('Point Cloud \n(commented code)')
    # axs[1].set_title('Point Cloud Slices')
    # axs[2].set_title('Centroids')
    # axs[3].set_title('Raw Polylines ')
    # axs[4].set_title('Clean Polylines')
    # axs[5].set_title('MultiPolygons')
    
    # for ax in axs:
    #     ax.set_xlabel('x')
    #     ax.set_ylabel('y')
    #     ax.set_zlabel('z')
    
    # # axs[0].scatter(pcl3d[:, 0], pcl3d[:, 1], pcl3d[:, 2], s=0.3, c='grey')
    
    # i = 0
    # clr = ['red', 'blue', 'green', 'black', 'orange']
    
    # for z in zcoords:
    #     axs[1].scatter(slices[z][:, 0], slices[z][:, 1], slices[z][:, 2], s=0.5, marker=".")
    
    #     axs[2].scatter(centroids[z][:, 0], centroids[z][:, 1], z*np.ones(centroids[z].shape[0]), s=2, marker=".")
    
    #     for polyline in rawpolylines[z]:
    #         axs[3].plot3D(polyline[:, 0], polyline[:, 1], z*np.ones(polyline.shape[0]), linewidth=1.5)
    
    #     for polyline in cleanpolylines[z]:
    #         axs[4].plot3D(polyline[:, 0], polyline[:, 1], z*np.ones(polyline.shape[0]), linewidth=1.5)
         
    #     pgn = polygons[z]
    #     try:
    #         if len(pgn) > 1:
    #             for geom in pgn:
    #                 ext_x, ext_y = geom.exterior.xy
    #                 axs[5].plot(ext_x, ext_y, z*np.ones(len(ext_x)), linewidth=3, c=clr[i])
    #     except TypeError:
    #         ext_x, ext_y = pgn.exterior.xy
    #         axs[5].plot(ext_x, ext_y, z*np.ones(len(ext_x)), linewidth=3, c=clr[i])
    #         if len(pgn.interiors) > 0:
    #             for hole in pgn.interiors:
    #                 int_x, int_y = hole.xy
    #                 plt.plot(int_x, int_y, z*np.ones(len(int_x)), linewidth=3, c=clr[i])
    #     if i == 4:
    #         i = 0
    #     else:
    #         i += 1
  
    # plt.show()
            
            
            



