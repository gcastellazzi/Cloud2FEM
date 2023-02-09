# Cloud2FEM
A finite element mesh generator based on point clouds of existing/histociral structures.

## Prerequisites
[Python 3](https://python.org) installed on your machine.  
  
Use the Python package manager pip to install the following packages:  
[PyQt5](https://pypi.org/project/PyQt5/), [PyQtGraph](https://pypi.org/project/pyqtgraph/), 
[ViSpy](https://pypi.org/project/vispy/), [NumPy](https://pypi.org/project/numpy/),
[pyntcloud](https://pypi.org/project/pyntcloud/),[Shapely](https://pypi.org/project/Shapely/),
[ezdxf](https://pypi.org/project/ezdxf/).

```
- PyQt5: pip install PyQt5==5.12.3                                                
- PyQtGraph: pip install pyqtgraph==0.11.1
- VisPy: pip install vispy==0.6.6                                          
- NumPy: pip install numpy==1.21.2                                                
- pyntcloud: pip install pyntcloud==0.1.5
- Shapely: pip install Shapely==1.7.1                                             
- ezdxf: pip install ezdxf==0.15.2
```

## Usage
The main graphical user interface of the software `Cloud2FEM` is shown in Fig. 1. On the top (I), the file menu contains buttons to load point clouds (the input data of this software), save a project, load a previously saved project, and export data to be used into CAD environments (i.e. .dxf slices) or FE simulations (i.e. FE solid mesh). On the left (II), the 3D Viewer section contains buttons to open a separated window where the selected quantities can be explored in 3D. 

|![Alt Main Window](https://github.com/gcastellazzi/Cloud2FEM/blob/main/docs/src/figure01.png "main window")|
|:--:|
| <b>Fig. 1 – Cloud2FEM main graphical user interface: (I) file menu, (II) 3D Viewer panel, (III) cloud/mesh processing panel, (IV) plot area, (V) 2D Viewer panel, (VI) editing bar.</b>|


The right panel (III) contains, starting from the top, the extreme z coordinates of the loaded point cloud, a section to specify the slicing modality, buttons to perform all the steps needed to generate a FE model. Red and green indicators beside each button denote if a certain step still needs to be performed or not, respectively. Most of the data generated through the steps in the right panel can be visualized in the central plot area (IV), which occupies most of the space of the interface. The 2D Viewer section on the left (V) can be utilized to choose the data to be shown, for any slice. 
The edit button on the top bar (VI) allows to enter the edit mode for the current slice and for the selected data type. An example of slice processing is shown in Fig. 2.

|![Alt Main Window](https://github.com/gcastellazzi/Cloud2FEM/blob/main/docs/src/figure02a.png "main window")      ![Alt Main Window](https://github.com/gcastellazzi/Cloud2FEM/blob/main/docs/src/figure02b.png "main window")      ![Alt Main Window](https://github.com/gcastellazzi/Cloud2FEM/blob/main/docs/src/figure02c.png "main window")|
|:--:|
| <b>Fig. 2 – Example of slice processing through Cloud2FEM: (a) slice of the raw point cloud, (b) derived centroids and polylines before simplification, (c) final clean geometry ready to be used in the mesh generation step.</b>|

On each slice, local modifications can be performed with the help of various suitable ad-hoc tools (for both points and polylines, e.g. draw, join, remove, add, move, offset, etc.), that can be activated via keyboard shortcuts. The top bar (VI) contains also buttons to save or discard the changes made in the edit mode, as well as a copy button that opens a separated window used to copy data from one slice to others. Finally, the button “Generate mesh” positioned at the bottom of the right panel (III) generates the matrix of nodal coordinates and the connectivity matrix of the FEs, i.e. the FE mesh, which can be exported from the file menu (I). In this particular case, the mesh is exported into the .inp format ([Simulia Abaqus](https://www.3ds.com/products-services/simulia/products/structure-simulation/)), which can be visualized also by open-source software packages, see e.g. [FreeCAD](https://www.freecad.org) . Anyway, the matrix of nodal coordinates and the connectivity matrix of the FEs can be found unencrypted in the .inp file (text format), and so they can be used in any available FE software.

## Software functionalities
The main functionalities of Cloud2FEM are here listed:
- Loading a point cloud in .pcd or .ply formats and visualizing it with the 3D viewer. Since the 3D visualization of a large point cloud can be computationally demanding, the software  uses a graphical accelerated tool to support real large dataset visualization. Nevertheless, the user can choose between three possible predefined resolutions (10, 50 and 100%) to get a smoother interaction.
- Visualizing the extreme [Z_min,Z_max] coordinates of the loaded point cloud.
- Slicing of the point cloud. The user can choose between two slicing rules, i.e. fixed number of slices or fixed step height. The function activated by the “Generate slices” button extracts slices from the loaded point cloud, according to the specified slicing parameters. Every slice, named by its Z coordinate, can be selected from the drop-down list on the left panel and visualized in the 2D viewer. The whole set of slices can be visualized in the 3D viewer by checking the corresponding checkbox on the left panel.
- Simplifying and ordering the slices. Every slice, consisting of an unordered array of points, is processed through the algorithm called by the “Generate Centroids” button to get a new smaller array of ordered points that can be used to efficiently describe the geometry of the slice. The centroids can be visualized in the 2D viewer by checking the corresponding checkbox in the left panel.
- Generating polylines. The centroids data generated by the software in a previous step is utilized to get a set of raw polylines. These are automatically simplified to get a cleaner and lightweight geometric representation. Both the raw and the clean polylines can be visualized in the 2D viewer by checking the corresponding checkbox in the left panel.
- Generating polygons. A more descriptive data type is automatically derived from the polylines obtained in a previous step. Each slice is described by means of polygons, made of inner and outer bounds. This geometric representation can be exported in the .dxf file format.
- Generating the mesh. A FE mesh is automatically generated from the polygons data. The X and Y dimensions of the voxels are set according to the grid visible in the 2D viewer, while the Z dimension depends on the adopted slicing parameters. The output can be exported in a text file format organized according to the Abaqus notation (.inp) [9].
- Saving and opening a project. The data handled by the software can be stored and retrieved to allow discontinuous work sessions. Furthermore, since the data is stored using the built-in Python shelve module, advanced users can easily exploit the data in other Python-based software.
- Editing of points and centroids. To eliminate criticalities in the slices, points and centroids can be removed individually or in bulk with graphic tools in the 2D viewer.
- Editing of polylines. A set of tools in the 2D viewer allows for an advanced graphic editing of the polylines. Vertices can be added, removed or moved, polylines can be joined, removed or drawn from scratch if geometric data is missing from the original point cloud.
- Copy of the polylines of a slice. The polylines of a slice can be copied to other to speed up the editing process.

|![Alt Output](https://github.com/gcastellazzi/Cloud2FEM/blob/main/docs/src/figure03.png "puotput")|
|:--:|
| <b>Fig. 4 – Example of generation of a FE mesh based on a point cloud of a benchmark structure by means of the Cloud2FEM software: (a) point cloud used as input visualized at 100% resolution, (b) slicing of the point cloud, (c) slice example with local modification, (d) FE mesh (output).</b>|

