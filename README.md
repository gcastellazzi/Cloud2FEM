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

![Alt Main Window](https://github.com/gcastellazzi/Cloud2FEM/blob/main/docs/src/figure01.png "main window")

The right panel (III) contains, starting from the top, the extreme z coordinates of the loaded point cloud, a section to specify the slicing modality, buttons to perform all the steps needed to generate a FE model. Red and green indicators beside each button denote if a certain step still needs to be performed or not, respectively. Most of the data generated through the steps in the right panel can be visualized in the central plot area (IV), which occupies most of the space of the interface. The 2D Viewer section on the left (V) can be utilized to choose the data to be shown, for any slice. 
The edit button on the top bar (VI) allows to enter the edit mode for the current slice and for the selected data type. An example of slice processing is shown in Fig. 2.

![Alt Main Window](https://github.com/gcastellazzi/Cloud2FEM/blob/main/docs/src/figure02a.png "main window")      ![Alt Main Window](https://github.com/gcastellazzi/Cloud2FEM/blob/main/docs/src/figure02b.png "main window")      ![Alt Main Window](https://github.com/gcastellazzi/Cloud2FEM/blob/main/docs/src/figure02c.png "main window")

On each slice, local modifications can be performed with the help of various suitable ad-hoc tools (for both points and polylines, e.g. draw, join, remove, add, move, offset, etc.), that can be activated via keyboard shortcuts. The top bar (VI) contains also buttons to save or discard the changes made in the edit mode, as well as a copy button that opens a separated window used to copy data from one slice to others. Finally, the button “Generate mesh” positioned at the bottom of the right panel (III) generates the matrix of nodal coordinates and the connectivity matrix of the FEs, i.e. the FE mesh, which can be exported from the file menu (I). In this particular case, the mesh is exported into the .inp format ([Simulia Abaqus]), which can be visualized also by open-source software packages, see e.g. FreeCAD. Anyway, the matrix of nodal coordinates and the connectivity matrix of the FEs can be found unencrypted in the .inp file (text format), and so they can be used in any available FE software.

