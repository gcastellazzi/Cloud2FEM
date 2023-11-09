import shelve
import pickle
import pysos
import numpy as np
from pyntcloud import PyntCloud
import shapely.geometry as sg
from shapely import wkt
import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QProcess, QObject, QEventLoop, pyqtSignal, QPointF
from PyQt5.QtGui import QBrush, QColor, QTextCursor
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QDialog, QTextEdit, QVBoxLayout, QPushButton, QProgressBar, QWidget

from PyQt5.uic import loadUi
import pyqtgraph as pg
from pyqtgraph import PlotWidget, PlotItem
# import pyqtgraph.opengl as gl     # serve per il plot pyqtgraph 3D che non sto usando

from Vispy3DViewer import Visp3dplot
from vispy.scene.visuals import Text
import Cloud2Polygons as cp
import Polygons2FEM as pf
import plot2D as ptd
import refresh_database as rd
import Mesh_functions as mf
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import mpl_toolkits.mplot3d as a3
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from vispy import app, gloo
from vispy.visuals.transforms import STTransform

import threading
import os
import subprocess
import time
from datetime import datetime
from sys import platform
from pathlib import Path
#import tkinter as tk
from screeninfo import get_monitors
# from mayavi import mlab


# import ezdxf
# from ezdxf.addons.geo import GeoProxy
#import FEM_functions as ff


##### PASSO PER TEST SU NUVOLA IDEALE
# MEDIO: from 0.3 to 6.5, n°slices 13, slice thickness 0.01
# GREZZO: from 0.3 to 4.3, n°slices 7,  slice thickness 0.01
# git updaate test
# git update test 2
#############

# class Logger:
#     def __init__(self, log_file):
#         self.log_file = log_file

#     def write(self, text):
#         with open(self.log_file, 'a') as f:
#             f.write(text)

#     def switch_to_terminal(self):
#         sys.stdout = sys.__stdout__  # Revert to the original stdout
#         # Redirect stdout and stderr to QTextEdit
#         #sys.stdout = StreamToTextEdit(self.plainText_terminal, sys.stdout)
#         #sys.stderr = StreamToTextEdit(self.plainText_terminal, sys.stderr)

#     def switch_to_file(self):
#         sys.stdout = self


class MainContainer:
    def __init__(self, filepath=None, pcl=None, npts=None, zmin=None, zmax=None,
                 xmin=None, xmax=None, ymin=None, ymax=None, zcoords=None, minwthick=None, slice_thick=None,
                 slices=None, netpcl=None, ctrds=None, polys=None, cleanpolys=None,
                 polygs=None, xngrid=None, xelgrid=None, yngrid=None, yelgrid=None,
                 elemlist=None, nodelist=None, elconnect=None, temp_points=None,
                 temp_scatter=None, temp_polylines=None, temp_roi_plot=None,
                 editmode=None, roiIndex=None, sorted_faces=None, sorted_faces_x=None, sorted_faces_y=None, filepath_cloud=None):
        self.filepath = filepath
        self.pcl = pcl              # Whole PCl as a 3-columns xyz numpy array
        self.npts = npts            # the above 'pcl' number of points
        self.zmin = zmin
        self.zmax = zmax
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.minwthick = minwthick
        self.slice_thick = slice_thick
        self.zcoords = zcoords      # 1D Numpy array of z coordinates utilized to create the slices below
        self.slices = slices        # Dictionary where key(i)=zcoords(i) and value(i)=np_array_xy(i)
        self.netpcl = netpcl        # pcl with empty spaces at slices position (for 3D visualization purposes)
        self.ctrds = ctrds          # Dictionary ordered as done for dict "slices"
        self.polys = polys          # Dict key(i) = zcoords(i), value(i) = [[np.arr.poly1],[np.a.poly2],[..],[np.polyn]]
        self.cleanpolys = cleanpolys  # Polylines cleaned by the shapely simplify function
        self.polygs = polygs        # Dict key(i) = zcoords(i), value(i) = shapely MultiPolygon
        self.xngrid = xngrid
        self.xelgrid = xelgrid
        self.yngrid = yngrid
        self.yelgrid = yelgrid
        self.elemlist = elemlist    # Dict key(i) = zcoords(i), value(i) = [[x1, y1], [x2, y2], ..., [xn, yn]]
        self.nodelist = nodelist    # Np array, row[i] = [nodeID, x, y, z]
        self.elconnect = elconnect  # Np array, row[i] = [edelmID, nID1, nID2, nID3, nID4, nID5, nID6, nID7, nID8]
        self.sorted_faces = sorted_faces # databse of voxel faces (internal faces)
        self.sorted_faces_x = sorted_faces_x # databse of x voxel faces (internal faces)
        self.sorted_faces_y = sorted_faces_y # databse of y voxel faces (internal faces)
        self.filepath_cloud = filepath_cloud
        #





mct = MainContainer()  # All the main variables are stored here


def save_project_shelve():
    try:
        fd = QFileDialog()
        filepath = fd.getSaveFileName(parent=None, caption="Save Project", directory="",
                                      filter="Cloud2FEM Data (*.cloud2fem)")[0]
        s = shelve.open(filepath)
        mct_dict = mct.__dict__  # Special method: convert instance of a class to a dict
        for k in mct_dict.keys():
            if k in ['filepath', 'pcl', 'netpcl', 'editmode', 'roiIndex', 
                     'temp_roi_plot', 'temp_polylines', 'temp_scatter', 'temp_points']:
                continue
            else:
                s[k] = mct_dict[k]
        s.close()
    except (ValueError, TypeError, FileNotFoundError):
        print('No file name specified')

def save_project_pysos():
    try:
        fd = QFileDialog()
        filepath = fd.getSaveFileName(parent=None, caption="Save Project", directory="",
                                      filter="Cloud2FEM Data (*.cloud2fem)")[0]
        #
        s = pysos.Dict(filepath)
        mct_dict = mct.__dict__  # Special method: convert instance of a class to a dict
        for k in mct_dict.keys():
            if k in ['filepath', 'pcl', 'netpcl', 'editmode', 'roiIndex', 
                     'temp_roi_plot', 'temp_polylines', 'temp_scatter', 'temp_points']:
                continue
            else:
                s[k] = mct_dict[k]
        s.close()
    except (ValueError, TypeError, FileNotFoundError):
        print('No file name specified')
    
def save_project():
    try:
        #
        filepath = mct.filepath
        if filepath :
            with open(filepath, 'wb') as handle:
                pickle.dump(mct, handle, protocol=pickle.HIGHEST_PROTOCOL)
                mct_dict = mct.__dict__  # Special method: convert instance of a class to a dict
            #
            print('Closing handling file: file saved')
            handle.close()
        else:
            fd = QFileDialog()
            filepath = fd.getSaveFileName(parent=None, caption="Save Project", directory="",
                                      filter="Cloud2FEM Data (*.cloud2fem)")[0]
            with open(filepath, 'wb') as handle:
                pickle.dump(mct, handle, protocol=pickle.HIGHEST_PROTOCOL)
                mct_dict = mct.__dict__  # Special method: convert instance of a class to a dict
            #
            print('Closing handling file: file correctly saved')
            handle.close()
        #
    except (ValueError, TypeError, FileNotFoundError):
        print('No file name specified')

def save_project_as():
    try:
        fd = QFileDialog()
        filepath = fd.getSaveFileName(parent=None, caption="Save Project", directory="",
                                      filter="Cloud2FEM Data (*.cloud2fem)")[0]
        #
        with open(filepath, 'wb') as handle:
            pickle.dump(mct, handle, protocol=pickle.HIGHEST_PROTOCOL)
            mct_dict = mct.__dict__  # Special method: convert instance of a class to a dict
            #
        #
        print('Closing handling file')
        handle.close()
    except (ValueError, TypeError, FileNotFoundError):
        print('No file name specified')

def reset_global_variables():
    global mct
    mct = rd.refresh_database(mct)

def new_project():
    msg_dxfok = QMessageBox()
    msg_dxfok.setWindowTitle('New Project')
    msg_dxfok.setText('WARNING: All unsaved data will be lost')

    # Add the "OK" button
    ok_button = msg_dxfok.addButton(QMessageBox.Ok)
    ok_button.setText("OK")

    # Add the "Cancel" button
    cancel_button = msg_dxfok.addButton(QMessageBox.Cancel)
    cancel_button.setText("Cancel")

    # Add the "Save..." button
    save_button = msg_dxfok.addButton("Save...", QMessageBox.AcceptRole)

    # Show the message box
    result = msg_dxfok.exec_()

    # Check the result to determine the user's choice
    if result == QMessageBox.Cancel:
        # User clicked the "Cancel" button
        print("Canceled")
    elif result == 0:  # 0 corresponds to the "Save..." button
        # User clicked the "Save..." button
        print("Save...")
        save_project()
    else:
        # User clicked the "OK" button
        print("OK")
        try:
            reset_global_variables()
            win.combo_slices.clear()
            win.label_zmin_value.setText('')
            win.label_zmax_value.setText('')
            win.btn_3dview.setEnabled(False)
            win.check_pcl_slices.setEnabled(False)
            win.status_slices.setStyleSheet("background-color: rgb(255, 0, 0);")
            win.btn_gen_centr.setEnabled(False)
            win.lineEdit_wall_thick.setEnabled(False)
            win.lineEdit_xeldim.setEnabled(False)
            win.lineEdit_yeldim.setEnabled(False)
            win.check_pcl.setChecked(False)
            win.check_pcl.setEnabled(False)
            win.btn_edit.setEnabled(False)
            win.check_centroids.setEnabled(False)
            win.status_centroids.setStyleSheet("background-color: rgb(255, 0, 0);")
            win.btn_gen_polylines.setEnabled(False)
            win.radioCentroids.setEnabled(False)
            win.check_polylines.setEnabled(False)
            win.status_polylines.setStyleSheet("background-color: rgb(255, 0, 0);")
            win.btn_gen_polygons.setEnabled(False)
            win.radioPolylines.setEnabled(False)
            win.btn_copy_plines.setEnabled(False)
            win.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
            win.btn_gen_mesh.setEnabled(False)
            win.exp_dxf.setEnabled(False)
            win.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
            win.exp_mesh.setEnabled(False)
            win.check_2d_pixel.setEnabled(False)
            win.check_2d_pixel_pm.setEnabled(False)
            win.main2dplot()
            return MainContainer
        
        except ValueError:
            print('No project file selected')

def open_file_in_app(self):
    print('This feature to be implemented. Open file directly from explorer')
    # try:
    #     os.startfile(self.filename)
    # except:
    #     subprocess.Popen(['open', '-t', self.filename])

def open_project():
    try:
        fd = QFileDialog()
        #
        filepath = fd.getOpenFileName(parent=None, caption="Open Project", directory="",
                                        filter="Cloud2FEM Data (*.cloud2fem);;Old Cloud2FEM Data MacOsx (*.cloud2fem.db);;Old Cloud2FEM Windows Data (*.cloud2fem.dat)")[0]
        if filepath:
            try:
                if "cloud2fem.db" in filepath or "cloud2fem.dat" in filepath:
                    s = shelve.open(filepath[: -4])
                    mct.npts = s['npts']
                    mct.zmin = s['zmin']
                    mct.zmax = s['zmax']
                    mct.xmin = s['xmin']
                    mct.xmax = s['xmax']
                    mct.ymin = s['ymin']
                    mct.ymax = s['ymax']
                    try:
                        mct.zcoords = s['zcoords']
                    except KeyError:
                        mct.zcoords = s['zslices']
                    mct.slices = s['slices']
                    mct.ctrds = s['ctrds']
                    mct.polys = s['polys']
                    mct.cleanpolys = s['cleanpolys']
                    mct.polygs = s['polygs']
                    mct.xngrid = s['xngrid']
                    mct.xelgrid = s['xelgrid']
                    mct.yngrid = s['yngrid']
                    mct.yelgrid = s['yelgrid']
                    mct.elemlist = s['elemlist']
                    mct.nodelist = s['nodelist']
                    mct.elconnect = s['elconnect']
                    s.close()
                else:
                    #
                    with open(filepath, "rb") as f:
                        s = pickle.load(f)
                    #
                    mct.filepath =  s.filepath
                    mct.pcl = s.pcl
                    mct.netpcl = s.netpcl
                    #G
                    mct.npts = s.npts
                    mct.zmin = s.zmin
                    mct.zmax = s.zmax
                    mct.xmin = s.xmin
                    mct.xmax = s.xmax
                    mct.ymin = s.ymin
                    mct.ymax = s.ymax
                    try:
                        mct.zcoords = s.zcoords
                    except KeyError:
                        mct.zcoords = s.zslices
                    mct.slices = s.slices
                    mct.ctrds = s.ctrds
                    mct.polys = s.polys
                    mct.cleanpolys = s.cleanpolys
                    mct.polygs = s.polygs
                    mct.xngrid = s.xngrid
                    mct.xelgrid = s.xelgrid
                    mct.yngrid = s.yngrid
                    mct.yelgrid = s.yelgrid
                    mct.elemlist = s.elemlist
                    mct.nodelist = s.nodelist
                    mct.elconnect = s.elconnect
                    #mct.sorted_faces = s.sorted_faces
                    # Check if the attribute 'minwthick' exists before accessing it
                    if hasattr(s, 'minwthick'):
                        mct.minwthick = s.minwthick
                    else:
                        mct.minwthick = '0.0'
                    # Check if the attribute 'sorted_faces' exists before accessing it
                    if hasattr(s, 'sorted_faces'):
                        mct.sorted_faces = s.sorted_faces
                    else:
                        mct.sorted_faces = None
                    if hasattr(s, 'sorted_faces_x'):
                        mct.sorted_faces_x = s.sorted_faces_x
                    else:
                        mct.sorted_faces_x = None
                    if hasattr(s, 'sorted_faces_y'):
                        mct.sorted_faces_y = s.sorted_faces_y
                    else:
                        mct.sorted_faces_y = None
                    mct.clicked_x = None
                    mct.clicked = None
                    f.close()
                win.combo_slices.clear()
                for z in mct.zcoords:
                    win.combo_slices.addItem(str('%.3f' % z))
                win.main2dplot()

                win.label_zmin_value.setText(str(mct.zmin))
                win.label_zmax_value.setText(str(mct.zmax))
                #
                win.lineEdit_from.setText(str(mct.zcoords[0])) 
                win.lineEdit_to.setText(str(mct.zcoords[-1])) 
                tentative_number_of_slices = len(mct.zcoords)
                win.lineEdit_steporN.setText(str(tentative_number_of_slices))
                tentative_slice_thickness = mct.slice_thick
                win.lineEdit_thick.setText(str(tentative_slice_thickness))
                print('Warning: the limits for slicing the cloud are tentatively set using the following parameters:')
                print(f'Z min = {round(mct.zmin)}')
                print(f'Z max = {round(mct.zmax)}')
                print('Slicing approach: Fixed number of slices')
                print(f'Tentative number of slices N = {tentative_number_of_slices}')
                print(f'Slice thickness = {tentative_slice_thickness}')
                #
                win.lineEdit_wall_thick.setText(str(mct.minwthick))
                win.lineEdit_thick.setText(str(mct.slice_thick))
                win.btn_3dview.setEnabled(True)
                win.check_pcl_slices.setEnabled(True)
                win.status_slices.setStyleSheet("background-color: rgb(0, 255, 0);")
                win.btn_gen_centr.setEnabled(True)
                win.lineEdit_wall_thick.setEnabled(True)
                win.lineEdit_xeldim.setEnabled(True)
                win.lineEdit_yeldim.setEnabled(True)
                win.check_pcl.setChecked(True)
                win.check_pcl.setEnabled(True)
                win.btn_edit.setEnabled(True)

                if mct.ctrds != None:
                    win.check_centroids.setEnabled(True)
                    win.status_centroids.setStyleSheet("background-color: rgb(0, 255, 0);")
                    win.btn_gen_polylines.setEnabled(True)
                    win.radioCentroids.setEnabled(True)
                if mct.cleanpolys != None:
                    win.check_polylines.setEnabled(True)
                    win.status_polylines.setStyleSheet("background-color: rgb(0, 255, 0);")
                    win.btn_gen_polygons.setEnabled(True)
                    win.radioPolylines.setEnabled(True)
                    win.btn_copy_plines.setEnabled(True)
                if mct.polygs != None:
                    win.status_polygons.setStyleSheet("background-color: rgb(0, 255, 0);")
                    win.btn_gen_mesh.setEnabled(True)
                    win.exp_dxf.setEnabled(True)
                if mct.elemlist != None:
                    win.status_mesh.setStyleSheet("background-color: rgb(0, 255, 0);")
                    win.exp_mesh.setEnabled(True)
            except FileNotFoundError:
                print(f"File not found: {filepath}")
        else:
            print("File dialog was canceled or escaped.")
    except ValueError:
        print('No project file selected')



def loadpcl():
    """ Opens a FileDialog to choose the PCl and stores the
    values for filepath, pcl, npts, zmin and zmax. Then sets up the gui.
    """
    try:
        fd = QFileDialog()
        getfile = fd.getOpenFileName(parent=None, caption="Load Point Cloud", directory="",
                                     filter="Point Cloud Data (*.pcd);; Polygon File Format (*.ply)")
        mct.filepath_cloud = getfile[0]
        wholepcl = PyntCloud.from_file(mct.filepath_cloud)
        mct.npts = wholepcl.points.shape[0]          # Point Cloud number of points

        # Defines a 3-columns xyz numpy array
        mct.pcl = np.hstack((
            np.array(wholepcl.points['x']).reshape(mct.npts, 1),
            np.array(wholepcl.points['y']).reshape(mct.npts, 1),
            np.array(wholepcl.points['z']).reshape(mct.npts, 1)
        ))
        mct.zmin = mct.pcl[:, 2].min()
        win.label_zmin_value.setText(str(mct.zmin))
        mct.zmax = mct.pcl[:, 2].max()
        win.label_zmax_value.setText(str(mct.zmax))
        mct.xmin = mct.pcl[:, 0].min()
        mct.xmax = mct.pcl[:, 0].max()
        mct.ymin = mct.pcl[:, 1].min()
        mct.ymax = mct.pcl[:, 1].max()
        print("\nPoint Cloud of " + str(mct.pcl.shape[0]) + " points loaded, file path: " + mct.filepath_cloud)
        print("First three points:\n" + str(mct.pcl[:3]))
        print("Last three points:\n" + str(mct.pcl[-3:]))
        #
        win.lineEdit_from.setText(str(round(mct.zmin)))
        win.lineEdit_to.setText(str(round(mct.zmax)))
        tentative_number_of_slices = 6
        win.lineEdit_steporN.setText(str(tentative_number_of_slices))
        tentative_slice_thickness = abs(round(mct.zmax)-round(mct.zmin))/100
        win.lineEdit_thick.setText(str(tentative_slice_thickness))
        print('Warning: the limits for slicing the cloud are tentatively set using the following parameters:')
        print(f'Z min = {round(mct.zmin)}')
        print(f'Z max = {round(mct.zmax)}')
        print('Slicing approach: Fixed number of slices')
        print(f'Tentative number of slices N = {tentative_number_of_slices}')
        print(f'Slice thickness = {tentative_slice_thickness}')
        #
        if len(mct.filepath_cloud) < 65:
            win.loaded_file.setText("Loaded Point Cloud: " + mct.filepath_cloud + "   ")
        else:
            slashfound = 0
            head_reverse = ''
            for char in mct.filepath_cloud[:30][::-1]:
                if char == '/' and slashfound == 0:
                    slashfound += 1
                elif slashfound == 0:
                    continue
                else:
                    head_reverse += char
            path_head = head_reverse[::-1]

            slashfound = 0
            path_tail = ''
            for char in mct.filepath_cloud[30:]:
                if char == '/' and slashfound == 0:
                    slashfound += 1
                elif slashfound == 0:
                    continue
                else:
                    path_tail += char
            win.loaded_file.setText("Loaded Point Cloud: " + path_head + '/...../' + path_tail + "   ")
            win.status_slices.setStyleSheet("background-color: rgb(255, 0, 0);")
            win.status_centroids.setStyleSheet("background-color: rgb(255, 0, 0);")
            win.status_polylines.setStyleSheet("background-color: rgb(255, 0, 0);")
            win.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
            win.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")

        # Enable gui widgets
        win.btn_3dview.setEnabled(True)
        win.rbtn_fixnum.setEnabled(True)
        win.rbtn_fixstep.setEnabled(True)
        win.rbtn_custom_slices.setEnabled(True)
        win.lineEdit_from.setEnabled(True)
        win.lineEdit_to.setEnabled(True)
        win.lineEdit_steporN.setEnabled(True)
        win.lineEdit_thick.setEnabled(True)
        win.btn_gen_slices.setEnabled(True)
    except ValueError:
        print('No Point Cloud selected')



def test_plotpolygons():
    """ #############################################################
    Metodo temporaneo per plottare i MultiPolygons generati
    #############################################################"""
    import matplotlib.pyplot as plt

    slidx = mct.zcoords[int(win.lineEdit_test.text())]
    polyslice = mct.polygs[slidx]
    try:
        if len(polyslice) > 1:
            for geom in polyslice:
                plt.plot(*geom.exterior.xy)
                # plt.plot(*geom.interiors.xy)
    except TypeError:
        plt.plot(*polyslice.exterior.xy)
        if len(polyslice.interiors) > 0:
            for hole in polyslice.interiors:
                plt.plot(*hole.xy)
    plt.show()



class ClickHandler(QObject):
    click_signal = pyqtSignal(float, float)

    def __init__(self, plot2d):
        super(ClickHandler, self).__init__()
        self.plot2d = plot2d
        self.connected = False  # Track the connection status

    def start(self):
        if not self.connected:
            self.plot2d.scene().sigMouseClicked.connect(self.on_plot_clicked)
            self.connected = True

    def stop(self):
        if self.connected:
            self.plot2d.scene().sigMouseClicked.disconnect(self.on_plot_clicked)
            self.connected = False

    def on_plot_clicked(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.scenePos()
            x = pos.x()
            y = pos.y()
            self.click_signal.emit(x, y)
            #self.stop()  # Disconnect the signal after the first left-click event
        elif event.button() == Qt.RightButton:
            # Disconnect the mouse click event to stop the function
            self.plot2d.scene().sigMouseClicked.disconnect(self.on_plot_clicked)
            self.is_active = False  # Function is no longer active
            self.signal_connected = False
            


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        loadUi("gui_main.ui", self)
        self.setWindowTitle('Cloud2FEM')
        self.graphlayout.setBackground((255, 255, 255))
        self.plot2d = self.graphlayout.addPlot()
        self.plot2d.setAspectLocked(lock=True)
        self.plot2d.setTitle('')
        # self.plot2d.enableAutoRange(enable=False)  # Da sistemare, mantiene gli assi bloccati quando aggiorno il plot?
        #
        # Checking if tem folder is present
        home_folder = Path.home()
        temp_folder_path = os.path.join(home_folder, "Cloud2FEM_temp_files" )
        temp_folder_exist = os.path.isdir(temp_folder_path)
        if not temp_folder_exist:
            os.makedirs(temp_folder_path) 

        
        Time_now = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
        temp_filename = 'debug_log_' + Time_now + '.txt'
        self.filename = os.path.join(temp_folder_path, temp_filename )
        # Redirect stdout and stderr to QTextEdit
        sys.stdout = StreamToTextEdit(self.plainText_terminal, sys.stdout, self.filename)
        sys.stderr = StreamToTextEdit(self.plainText_terminal, sys.stderr, self.filename)
        #
        self.Load_PC.triggered.connect(loadpcl)
        self.save_project.triggered.connect(save_project)
        #
        
        self.actionOpen_Log_File.triggered.connect(open_file_in_app)
        #self.actionVerbose_Terminal.triggered.connect(logger.switch_to_terminal)
        #
        #self.actionVerbose_Log_File.triggered.connect(logger.switch_to_file)
        #
        self.open_project.triggered.connect(open_project)
        self.new_project.triggered.connect(new_project)
        self.exp_dxf.triggered.connect(self.exp_dxf_clicked)
        self.exp_mesh.triggered.connect(self.exp_mesh_clicked)
        self.btn_3dview.clicked.connect(self.open3dview)

        self.rbtn_fixnum.toggled.connect(self.fixnum_toggled)
        self.rbtn_fixstep.toggled.connect(self.fixstep_toggled)
        self.rbtn_custom_slices.toggled.connect(self.customstep_toggled)

        self.btn_gen_slices.clicked.connect(self.genslices_clicked)
        self.btn_gen_centr.clicked.connect(self.gencentr_clicked)
        self.btn_gen_polylines.clicked.connect(self.genpolylines_clicked)
        self.btn_gen_polygons.clicked.connect(self.genpolygons_clicked)
        self.btn_gen_mesh.clicked.connect(self.genmesh_clicked)
        self.combo_slices.currentIndexChanged.connect(self.main2dplot)
        self.check_2d_slice.toggled.connect(self.main2dplot)
        self.check_2d_grid.toggled.connect(self.main2dplot)
        self.check_2d_centr.toggled.connect(self.main2dplot)
        self.check_2d_polylines.toggled.connect(self.main2dplot)
        self.check_2d_polylines_clean.toggled.connect(self.main2dplot)
        #
        self.check_2d_slice_pm.toggled.connect(self.main2dplot)
        self.check_2d_centr_pm.toggled.connect(self.main2dplot)
        self.check_2d_polylines_pm.toggled.connect(self.main2dplot)
        self.check_2d_polylines_clean_pm.toggled.connect(self.main2dplot)
        self.check_2d_pixel.toggled.connect(self.main2dplot)
        self.check_2d_pixel_pm.toggled.connect(self.main2dplot)
        #
        self.check_2d_polygons.toggled.connect(self.main2dplot)
        self.lineEdit_xeldim.editingFinished.connect(self.main2dplot)
        self.lineEdit_yeldim.editingFinished.connect(self.main2dplot)
        # Connect edit signals
        self.btn_edit.clicked.connect(self.editMode)
        self.lineEdit_off.textEdited.connect(self.updateOffDistance)
        self.btn_edit_discard.clicked.connect(self.discard_changes)
        self.btn_edit_finalize.clicked.connect(self.save_changes)
        self.btn_copy_plines.clicked.connect(self.copy_polylines)
        # 
        self.pushButton_add_slice.clicked.connect(self.gen_one_slices_clicked)
        self.pushButton_sort_zcoords.clicked.connect(self.sort_zcoords_clicked)
        self.pushButton_del_curr_slice.clicked.connect(self.del_zcoords_clicked)
        self.btn_unlock_slices.clicked.connect(self.unlock_slices_menu)
        self.btn_lock_slices.clicked.connect(self.lock_slices_menu)
        self.btn_slice_down.clicked.connect(self.slice_down)
        self.btn_slice_up.clicked.connect(self.slice_up)
        #
        self.btn_plot_mesh.clicked.connect(self.plot_mesh)
        #
        # Set some default values
        self.emode = None  # Edit mode status
        self.staticPlotItems = []  # List of non editable plotted items
        #
        # Initialize class-level variables to store coordinates and a flag to check if the function is active
        self.clicked_x = None
        self.clicked_y = None
        self.abs_min_x = None
        self.abs_min_y = None
        self.abs_max_x = None
        self.abs_max_y = None
        self.clicked_point = None
        self.btn_plot_xy_sections.clicked.connect(self.get_pixel_xy)
        self.click_handler = ClickHandler(self.plot2d)
        self.signal_connected = False
        #
        # manual version
        self.btn_plot_xy_section_manual.clicked.connect(self.plot_pixel_xy_m)
        self.figure_section = None
        self.axes_section = None

        # TEST plot poligoni #################################
        self.pushtest.clicked.connect(test_plotpolygons)
        ######################################################
        print('##########################################################################')
        print('Console and error messages are saved in the logfile, which is located at:')
        print( self.filename)
        print('##########################################################################')
    
    def plot_mesh(self):
        xyz = mct.nodelist
        LCO = mct.elconnect
        check_consistency = False
        do_parallel_computing = False # Problems with the GUI
        csize = LCO.shape[1]
        if check_consistency:
            if do_parallel_computing:
                start_time = time.time()
                problematic_elements = mf.connectivity_check_consitency_parallel_ncores(LCO[:,1:csize], 4)
                end_time = time.time()
                elapsed_time = end_time - start_time
                print(f"Elapsed time 4 cores: {elapsed_time:.2f} seconds")
            else:
                problematic_elements = mf.connectivity_check_consitency(LCO[:,1:csize])
            if len(problematic_elements)>0:
                print('Some problems were found for the following elements:', problematic_elements)

        
        nfig = 33
        options = False
        color = 'k'
        # Create a figure
        # fig = plt.figure(nfig)
        # Create a 3D axes with auto_add_to_figure=False
        # ax = Axes3D(fig, auto_add_to_figure=False)
        # Add the 3D axes to the figure
        # fig.add_axes(ax)
        #ax = mf.plot_simple_mesh(xyz[:,1:4], LCO[:,1:csize], nfig, ax, color, options)
        # plt.show()
        #boundary_faces, element_faces, normals, belongs_to_element, repetitions = mf.get_boundary_faces(LCO[:,1:csize],xyz[:,1:4])
        boundary_faces = mf.find_external_faces(LCO[:,1:csize].astype(int))
        # print(boundary_faces)
        #element_faces
        #ax = mf.plot_boundary_mesh(xyz[:,1:4], element_faces, boundary_faces, nfig, ax)
        # Create a figure and axis for 3D plotting
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        # Plot the faces
       # Plot the boundary_faces
        for face in boundary_faces:
            poly3d = [xyz[i-1,1:4] for i in face]
            ax.add_collection3d(Poly3DCollection([poly3d], facecolors='gray', linewidths=1, edgecolors='k', alpha=1.0))

        # Extract the coordinates from the xyz array
        data = boundary_faces

        # Convert the set of tuples into a flat list
        flat_list = [item for sublist in data for item in sublist]

        # Find unique values in the flat list
        unique_values = set(flat_list)

        # If you want the unique values as a list, you can convert the set back to a list
        unique_values_list = list(unique_values)
        # Subtract 1 from every value in unique_values_list
        unique_values_list = [value - 1 for value in unique_values_list]


        x_values = xyz[unique_values_list, 1]
        y_values = xyz[unique_values_list, 2]
        z_values = xyz[unique_values_list, 3]

        # Calculate the min and max values for each axis
        x_min = np.min(x_values)
        x_max = np.max(x_values)
        # Find the index of the maximum value
        max_index = np.argmax(x_values)
        value_to_find = max_index

        # Find the groups of values containing the specified value
        matching_groups = [group for group in boundary_faces if value_to_find in group]

        y_min = np.min(y_values)
        y_max = np.max(y_values)

        z_min = np.min(z_values)
        z_max = np.max(z_values)
        # Set axis labels
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        # Set the limits using the extracted values
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_zlim(z_min, z_max)
        # ax.set_xlim(0, 6)
        # ax.set_ylim(0, 6)
        # ax.set_zlim(0, 12)
        # Set the camera position and target to have the full picture
        ax.view_init(elev=20, azim=30)  # You can adjust the elevation (elev) and azimuth (azim) angles

        # Automatically set the limits based on data
        ax.autoscale_view()

        # Set equal aspect ratio for all axes
        ax.set_box_aspect([1, 1, 1])
        plt.show()


    def unlock_slices_menu(self):
        # Enable gui widgets
        win.btn_3dview.setEnabled(True)
        win.rbtn_fixnum.setEnabled(True)
        win.rbtn_fixstep.setEnabled(True)
        win.rbtn_custom_slices.setEnabled(True)
        win.lineEdit_from.setEnabled(True)
        win.lineEdit_to.setEnabled(True)
        win.lineEdit_steporN.setEnabled(True)
        win.lineEdit_thick.setEnabled(True)
        win.btn_gen_slices.setEnabled(True)
    
    def lock_slices_menu(self):
        # Disable gui widgets
        win.btn_3dview.setEnabled(False)
        win.rbtn_fixnum.setEnabled(False)
        win.rbtn_fixstep.setEnabled(False)
        win.rbtn_custom_slices.setEnabled(False)
        win.lineEdit_from.setEnabled(False)
        win.lineEdit_to.setEnabled(False)
        win.lineEdit_steporN.setEnabled(False)
        win.lineEdit_thick.setEnabled(False)
        win.btn_gen_slices.setEnabled(False)
        
    def gen_one_slices_clicked(self):
        self.plot2d.vb.enableAutoRange()
        new_z = self.lineEdit_new_z_slice.text()
        c = 1
        d = self.lineEdit_new_thick.text()
        a = float(new_z) - float(d)/2
        b = float(new_z) + float(d)/2
        try:
            if float(new_z) > mct.zmax or float(new_z) < mct.zmin:
                msg_slices = QMessageBox()
                msg_slices.setWindowTitle('Slicing configuration')
                msg_slices.setText('\nSlice z is out of range            '
                                   '\n                                            ')
                msg_slices.setIcon(QMessageBox.Warning)
                x = msg_slices.exec_()
            
            if float(new_z) in mct.zcoords:
                msg_slices = QMessageBox()
                msg_slices.setWindowTitle('Slicing configuration')
                msg_slices.setText('\nSlice at this z is already present!            '
                                   '\n                                            ')
                msg_slices.setIcon(QMessageBox.Warning)
                x = msg_slices.exec_()
            
            if len(new_z) == 0 or len(d) == 0:
                msg_slices = QMessageBox()
                msg_slices.setWindowTitle('Slicing configuration')
                msg_slices.setText('\nIncomplete slicing configuration            '
                                   '\n                                            ')
                msg_slices.setIcon(QMessageBox.Warning)
                x = msg_slices.exec_()
            else:
                
                mct.slices, mct.netpcl, mct.zcoords = cp.add_slices(float(new_z), mct.pcl, float(d), mct.npts, mct.slices, mct.zcoords)
                self.combo_slices.clear()
                for z in mct.zcoords:
                    self.combo_slices.addItem(str('%.3f' % z))  # Populates the gui slices combobox
                
                print('Slices updated to: ', len(mct.slices.keys()), ' slices')
                # print(len(mct.slices.{1}), ' slices generated')
                self.lineEdit_wall_thick.setEnabled(True)
                self.btn_gen_centr.setEnabled(True)
                self.btn_edit.setEnabled(True)
                self.check_pcl_slices.setEnabled(True)
                self.lineEdit_xeldim.setEnabled(True)
                self.lineEdit_yeldim.setEnabled(True)
                self.status_slices.setStyleSheet("background-color: rgb(0, 255, 0);")
                self.status_centroids.setStyleSheet("background-color: rgb(255, 0, 0);")
                self.status_polylines.setStyleSheet("background-color: rgb(255, 0, 0);")
                self.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
                self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
                msg_slicesok = QMessageBox()
                msg_slicesok.setWindowTitle('Slicing completed')
                msg_slicesok.setText(str(len(mct.slices.keys())) + ' slices generated    '
                                                                   '                     ')
                x = msg_slicesok.exec_()
        except ValueError:
            msg_slices2 = QMessageBox()
            msg_slices2.setWindowTitle('Slicing configuration')
            msg_slices2.setText('ValueError')
            msg_slices2.setInformativeText("Only the following input types are allowed:\n\n"
                                           "From:\n"
                                           "        integer or float\n"
                                           "to:\n"
                                           "        integer or float\n"
                                           "n° of slices:\n"
                                           "        integer\n"
                                           "step height:\n"
                                           "        integer or float")
            msg_slices2.setIcon(QMessageBox.Warning)
            x = msg_slices2.exec_()   

    def sort_zcoords_clicked(self):
        mct.zcoords = cp.sort_zcoords(mct.zcoords)
        self.combo_slices.clear()
        for z in mct.zcoords:
            self.combo_slices.addItem(str('%.3f' % z))  # Populates the gui slices combobox
    
    def del_zcoords_clicked(self):
        mct.slices, mct.zcoords = cp.del_zcoords(mct.slices, mct.zcoords, self.combo_slices.currentIndex())
        new_Index = self.combo_slices.currentIndex()
        self.combo_slices.clear()
        for z in mct.zcoords:
            self.combo_slices.addItem(str('%.3f' % z))  # Populates the gui slices combobox
        
        if new_Index > len(mct.zcoords)-1:
            new_Index = len(mct.zcoords)-1
        
        self.combo_slices.setCurrentIndex(new_Index)
    
    def slice_down(self):
        
        new_Index = self.combo_slices.currentIndex()
        new_Index = new_Index -1
                
        if new_Index < 0 :
            new_Index = len(mct.zcoords)+1
        
        self.combo_slices.setCurrentIndex(new_Index)
    
    def slice_up(self):
    
        new_Index = self.combo_slices.currentIndex()
        new_Index = new_Index + 1 

        if new_Index > len(mct.zcoords)-1:
            new_Index = len(mct.zcoords)-1
        
        self.combo_slices.setCurrentIndex(new_Index)
    
    def genslices_clicked(self):
        self.plot2d.vb.enableAutoRange()
        a = self.lineEdit_from.text()
        b = self.lineEdit_to.text()
        c = self.lineEdit_steporN.text()
        d = self.lineEdit_thick.text()
        try:
            if len(a) == 0 or len(b) == 0 or len(c) == 0 or len(d) == 0:
                msg_slices = QMessageBox()
                msg_slices.setWindowTitle('Slicing configuration')
                msg_slices.setText('\nIncomplete slicing configuration            '
                                   '\n                                            ')
                msg_slices.setIcon(QMessageBox.Warning)
                x = msg_slices.exec_()
            else:
                if self.rbtn_fixnum.isChecked():
                    mct.zcoords = cp.make_zcoords(a, b, c, 1)
                elif self.rbtn_fixstep.isChecked():
                    mct.zcoords = cp.make_zcoords(a, b, c, 2)
                else:
                    pass # Custom slicing to be implemented
                    
                mct.slices, mct.netpcl = cp.make_slices(mct.zcoords, mct.pcl, float(d), mct.npts)
                self.combo_slices.clear()
                for z in mct.zcoords:
                    self.combo_slices.addItem(str('%.3f' % z))  # Populates the gui slices combobox
                
                print(len(mct.slices.keys()), ' slices generated')
                self.lineEdit_wall_thick.setEnabled(True)
                self.btn_gen_centr.setEnabled(True)
                self.btn_edit.setEnabled(True)
                self.check_pcl_slices.setEnabled(True)
                self.lineEdit_xeldim.setEnabled(True)
                self.lineEdit_yeldim.setEnabled(True)
                self.status_slices.setStyleSheet("background-color: rgb(0, 255, 0);")
                self.status_centroids.setStyleSheet("background-color: rgb(255, 0, 0);")
                self.status_polylines.setStyleSheet("background-color: rgb(255, 0, 0);")
                self.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
                self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
                #
                self.check_2d_centr.setEnabled(False)
                self.check_2d_centr_pm.setEnabled(False)
                #
                self.check_2d_polylines.setEnabled(False)
                self.check_2d_polylines_pm.setEnabled(False)
                #
                self.check_2d_polylines_clean.setEnabled(False)
                self.check_2d_polylines_clean_pm.setEnabled(False)
                #
                self.check_2d_pixel.setEnabled(False)
                self.check_2d_pixel_pm.setEnabled(False)
                #
                self.check_2d_polygons.setEnabled(False)
                #
                msg_slicesok = QMessageBox()
                msg_slicesok.setWindowTitle('Slicing completed')
                msg_slicesok.setText(str(len(mct.slices.keys())) + ' slices generated    '
                                                                   '                     ')
                x = msg_slicesok.exec_()
        except ValueError:
            msg_slices2 = QMessageBox()
            msg_slices2.setWindowTitle('Slicing configuration')
            msg_slices2.setText('ValueError')
            msg_slices2.setInformativeText("Only the following input types are allowed:\n\n"
                                           "From:\n"
                                           "        integer or float\n"
                                           "to:\n"
                                           "        integer or float\n"
                                           "n° of slices:\n"
                                           "        integer\n"
                                           "step height:\n"
                                           "        integer or float")
            msg_slices2.setIcon(QMessageBox.Warning)
            x = msg_slices2.exec_()

    def gencentr_clicked(self):
        self.plot2d.vb.enableAutoRange()
        try:
            mct.minwthick = float(self.lineEdit_wall_thick.text())
            
            mct.ctrds = cp.find_centroids(mct.minwthick, mct.zcoords, mct.slices)
            
            self.check_centroids.setEnabled(True)
            self.radioCentroids.setEnabled(True)
            self.btn_gen_polylines.setEnabled(True)
            self.status_centroids.setStyleSheet("background-color: rgb(0, 255, 0);")
            self.status_polylines.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
            #
            self.check_2d_centr.setEnabled(True)
            self.check_2d_centr_pm.setEnabled(True)
            self.main2dplot()
            msg_centrok = QMessageBox()
            msg_centrok.setWindowTitle('Generate Centroids')
            msg_centrok.setText('\nCentroids generation completed           '
                                '\n                                         ')
            x = msg_centrok.exec_()
        except ValueError:
            msg_centr = QMessageBox()
            msg_centr.setWindowTitle('Generate Centroids')
            msg_centr.setText('\nWrong input in "Minimum wall thickness"       '
                               '\n                                            ')
            msg_centr.setIcon(QMessageBox.Warning)
            x = msg_centr.exec_()

    def genpolylines_clicked(self):
        self.plot2d.vb.enableAutoRange()
        mct.minwthick = float(self.lineEdit_wall_thick.text())
        # Convert Shapely coordinates to a numpy array
        try:
            ctrds_np = np.array([list(geom.coords) for geom in mct.ctrds])
        except:
            coordinates_list = []
            for key, value in mct.ctrds.items():
                # Access the coordinates from the NumPy array
                coords = value[0]  # Assuming each value is a 2D array of coordinates
                coordinates_list.append(coords)

            # Convert the list of coordinates to a NumPy array
            ctrds_np = np.array(coordinates_list)

        try:
            mct.polys, mct.cleanpolys = cp.make_polylines(mct.minwthick, mct.zcoords, ctrds_np)
        except:
            mct.polys, mct.cleanpolys = cp.make_polylines(mct.minwthick, mct.zcoords, mct.ctrds)
        #mct.polys, mct.cleanpolys = cp.make_polylines(mct.minwthick, mct.zcoords, mct.ctrds)
        
        self.check_polylines.setEnabled(True)
        self.btn_gen_polygons.setEnabled(True)
        self.radioPolylines.setEnabled(True)
        self.btn_copy_plines.setEnabled(True)
        self.status_polylines.setStyleSheet("background-color: rgb(0, 255, 0);")
        self.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
        self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
        #
        self.check_2d_polylines.setEnabled(True)
        self.check_2d_polylines_pm.setEnabled(True)
        #
        self.check_2d_polylines_clean.setEnabled(True)
        self.check_2d_polylines_clean_pm.setEnabled(True)
        self.main2dplot()
        msg_polysok = QMessageBox()
        msg_polysok.setWindowTitle('Generate Polylines')
        msg_polysok.setText('\nPolylines generation completed           '
                            '\n                                         ')
        x = msg_polysok.exec_()

    def genpolygons_clicked(self):
        self.plot2d.vb.enableAutoRange()
        mct.minwthick = float(self.lineEdit_wall_thick.text())
        
        mct.polygs, invalidpolygons = cp.make_polygons(mct.minwthick, mct.zcoords, mct.cleanpolys)
        
        if len(invalidpolygons) != 0:
            msg_invpoligons = QMessageBox()
            msg_invpoligons.setWindowTitle('Generate Polygons')
            invalidlist = ''
            for z in invalidpolygons:
                invalidlist += str('\n' + "%.3f" % z)
            msg_invpoligons.setText("\nInvalid Polygons in slices: " + invalidlist)
            msg_invpoligons.setIcon(QMessageBox.Warning)
            x = msg_invpoligons.exec_()
        
        self.btn_gen_mesh.setEnabled(True)
        self.exp_dxf.setEnabled(True)
        self.status_polygons.setStyleSheet("background-color: rgb(0, 255, 0);")
        self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
        #
        self.check_2d_polygons.setEnabled(True)
        self.main2dplot()
        msg_polygsok = QMessageBox()
        msg_polygsok.setWindowTitle('Generate Polygons')
        msg_polygsok.setText('\nPolygons generation completed           '
                            '\n                                         ')
        x = msg_polygsok.exec_()
        
    def exp_dxf_clicked(self):
        try:
            fd = QFileDialog()
            filepath = fd.getSaveFileName(parent=None, caption="Export DXF", directory="", filter="DXF (*.dxf)")[0]
            cp.export_dxf(mct.zcoords, mct.polygs, filepath)
            msg_dxfok = QMessageBox()
            msg_dxfok.setWindowTitle('DXF Export')
            msg_dxfok.setText('File saved in: \n' + filepath + '                       ')
            x = msg_dxfok.exec_()
        except (ValueError, TypeError, FileNotFoundError):
            print('No dxf name specified')
        
    def genmesh_clicked(self):
        xeldim = float(self.lineEdit_xeldim.text())
        yeldim = float(self.lineEdit_yeldim.text())

        mct.elemlist, mct.nodelist, mct.elconnect = pf.make_mesh(
            xeldim, yeldim, mct.xmin, mct.ymin, mct.xmax, mct.ymax, mct.zcoords, mct.polygs)
        #
        mct.sorted_faces = None
        mct.sorted_faces_x = None
        mct.sorted_faces_y = None
        #
        self.check_mesh.setEnabled(True)
        self.check_2d_pixel.setEnabled(True)
        self.check_2d_pixel_pm.setEnabled(True)
        self.main2dplot()
        self.exp_mesh.setEnabled(True)
        self.status_mesh.setStyleSheet("background-color: rgb(0, 255, 0);")
        msg_meshok = QMessageBox()
        msg_meshok.setWindowTitle('Generate Mesh')
        msg_meshok.setText('\nMesh generation completed                 '
                            '\n                                         ')
        x = msg_meshok.exec_()
    
    def exp_mesh_clicked(self):
        try:
            fd = QFileDialog()
            meshpath = fd.getSaveFileName(parent=None, caption="Export DXF", directory="", filter="Abaqus Input File (*.inp)")[0]
            pf.export_mesh(meshpath, mct.nodelist, mct.elconnect)
            msg_dxfok = QMessageBox()
            msg_dxfok.setWindowTitle('Mesh Export')
            msg_dxfok.setText('File saved in: \n' + meshpath + '                       ')
            x = msg_dxfok.exec_()
        except (ValueError, TypeError, FileNotFoundError):
            print('No .inp name specified')

    def srule_status(self, torf):
        self.lineEdit_from.setEnabled(torf)
        self.lineEdit_to.setEnabled(torf)
        self.lineEdit_steporN.setEnabled(torf)

    def fixnum_toggled(self):
        self.lineEdit_customslices.setEnabled(False)
        self.srule_status(True)
        self.label_steporN.setText('n° of slices:')

    def fixstep_toggled(self):
        self.lineEdit_customslices.setEnabled(False)
        self.srule_status(True)
        self.label_steporN.setText('step height:')

    def customstep_toggled(self):
        self.srule_status(False)
        self.lineEdit_customslices.setEnabled(True)

    def open3dview(self):
        chkpcl = self.check_pcl.isChecked()
        chksli = self.check_pcl_slices.isChecked()
        chkctr = self.check_centroids.isChecked()
        chkply = self.check_polylines.isChecked()
        chkmesh = self.check_mesh.isChecked()
        if self.rbtn_100.isChecked():
            p3d = Visp3dplot(1)
        elif self.rbtn_50.isChecked():
            p3d = Visp3dplot(0.5)
        else:
            p3d = Visp3dplot(0.1)
        if chkctr:
            p3d.print_centr(mct)
        if chksli:
            p3d.print_slices(mct)
        if chkply:
            p3d.print_polylines(mct)
        if chkmesh:
            p3d.print_mesh2(mct)
        if chkpcl and (chksli or chkctr or chkply or chkmesh):
            p3d.print_cloud(mct.netpcl, 0.5)   ############################################ default alpha = 0.75
        elif chkpcl:
            p3d.print_cloud(mct.pcl, 1)
        
        # Create a VisPy Text visual for instructions
        #instruction_text = Text("Drag to move the camera\nRight-click to change the camera", pos=(10, 10), color='red')
        # Add the text visual to the Visp3dplot scene
        #p3d.add(instruction_text)

        p3d.final3dsetup()
    
    def plot_grid(self):
        xeldim = float(self.lineEdit_xeldim.text())
        yeldim = float(self.lineEdit_yeldim.text())
        xngrid = np.arange(mct.xmin - xeldim, mct.xmax + 2 * xeldim, xeldim)
        yngrid = np.arange(mct.ymin - yeldim, mct.ymax + 2 * yeldim, yeldim)
        for x in xngrid:
            xitem = pg.PlotCurveItem(pen=pg.mkPen(color=(220, 220, 220, 255), width=1.5))
            xitem.setData(np.array([x, x]), np.array([min(yngrid), max(yngrid)]))
            self.plot2d.addItem(xitem)
            self.staticPlotItems.append(xitem)
        for y in yngrid:
            yitem = pg.PlotCurveItem(pen=pg.mkPen(color=(220, 220, 220, 255), width=1.5))
            yitem.setData(np.array([min(xngrid), max(xngrid)]), np.array([y, y]))
            self.plot2d.addItem(yitem)
            self.staticPlotItems.append(yitem)

    def plot_slice(self):
        slm2dplt = mct.slices[mct.zcoords[self.combo_slices.currentIndex()]][:, [0, 1]]
        scatter2d = pg.ScatterPlotItem(pos=slm2dplt, size=3, brush=pg.mkBrush(0, 0, 0, 255), pen=pg.mkPen(color=(0, 0, 0)))    #### default size = 5
        self.plot2d.addItem(scatter2d)
        self.staticPlotItems.append(scatter2d)
        chk2dsli_pm = self.check_2d_slice_pm.isChecked()
        if chk2dsli_pm :
            self.plot2d.setTitle("<span style=\"color:red;font-size:12pt\">... Upper Slice hint</span><BR><span style=\"color:black;font-size:12pt\">... Current Slice</span><BR><span style=\"color:green;font-size:12pt\">... Lower Slice hint</span>")
            slice_n = self.combo_slices.currentIndex()
            if slice_n < len(mct.zcoords)-1 :
                slm2dplt = mct.slices[mct.zcoords[slice_n+1]][:, [0, 1]]
                scatter2d = pg.ScatterPlotItem(pos=slm2dplt, size=2, brush=pg.mkBrush(255, 0, 0, 100), pen=pg.mkPen(color=(255, 0, 0,100)))    #### default size = 5
                self.plot2d.addItem(scatter2d)
                self.staticPlotItems.append(scatter2d)
            if slice_n > 0 :
                slm2dplt = mct.slices[mct.zcoords[slice_n-1]][:, [0, 1]]
                scatter2d = pg.ScatterPlotItem(pos=slm2dplt, size=2, brush=pg.mkBrush(0, 255, 0, 100), pen=pg.mkPen(color=(0, 255, 0,100)))    #### default size = 5
                self.plot2d.addItem(scatter2d)
                self.staticPlotItems.append(scatter2d)

    def plot_centroids(self):
        ctrsm2dplt = mct.ctrds[mct.zcoords[self.combo_slices.currentIndex()]][:, [0, 1]]
        ctrsscatter2d = pg.ScatterPlotItem(pos=ctrsm2dplt, size=7, brush=pg.mkBrush(255, 0, 0, 255), pen=pg.mkPen(color=(0, 0, 0))) ######### default size = 13
        self.plot2d.addItem(ctrsscatter2d)
        self.staticPlotItems.append(ctrsscatter2d)
        chk2centr_pm = self.check_2d_centr_pm.isChecked()
        if chk2centr_pm :
            self.plot2d.setTitle("<span style=\"color:green;font-size:12pt\">ooo Upper Slice hint</span><BR><span style=\"color:red;font-size:12pt\">ooo Current Slice</span><BR><span style=\"color:blue;font-size:12pt\">ooo Lower Slice hint</span>")
            slice_n = self.combo_slices.currentIndex()
            if slice_n < len(mct.zcoords)-1 :
                ctrsm2dplt = mct.ctrds[mct.zcoords[slice_n+1]][:, [0, 1]]
                ctrsscatter2d = pg.ScatterPlotItem(pos=ctrsm2dplt, size=4, brush=pg.mkBrush(0, 255, 0, 100), pen=pg.mkPen(color=(0, 255, 0, 100))) ######### default size = 13
                self.plot2d.addItem(ctrsscatter2d)
                self.staticPlotItems.append(ctrsscatter2d)
            if slice_n > 0 :
                ctrsm2dplt = mct.ctrds[mct.zcoords[slice_n-1]][:, [0, 1]]
                ctrsscatter2d = pg.ScatterPlotItem(pos=ctrsm2dplt, size=4, brush=pg.mkBrush(0, 0, 255, 100), pen=pg.mkPen(color=(0, 0, 255, 100))) ######### default size = 13
                self.plot2d.addItem(ctrsscatter2d)
                self.staticPlotItems.append(ctrsscatter2d)
    
    #
    def on_clicked(self, x, y):
        print(f"Clicked at ({x}, {y})")
        #self.click_handler.stop()  # Disconnect the signal here
        view_pos = self.plot2d.getViewBox().mapSceneToView(QPointF(x, y))
        self.clicked_x, self.clicked_y = view_pos.x(), view_pos.y()
        self.plot_pixel_xy_m()
        print(f"Clicked at (scene coordinates: {x}, {y}), (graph coordinates: {self.clicked_x}, {self.clicked_y})")
        # Disconnect the signal only if it was connected in this function
        # if self.signal_connected:
        #     self.click_handler.stop()
        #     self.signal_connected = False
    #
    def get_pixel_xy(self):
        #
        self.plot2d.setTitle("<span style=\"color:black;font-size:12pt\">Mouse Left Click: select section location (x,y)</span><BR><span style=\"color:red;font-size:12pt\">Mouse Right Click: stop selection</span>")
        # DA COMMENTARE? inizio
        # if self.signal_connected:
        #     try: self.click_handler.stop()  # Disconnect the signal if it was previously connected
        #     except Exception: 
        #         pass
        #         self.connected = False
        # DA COMMENTARE? fine

        self.click_handler.start()
        loop = QEventLoop()
        self.signal_connected = True
        self.click_handler.click_signal.connect(self.on_clicked)
        loop.exec_()
        #
    def plot_pixel_xy(self, xcoord, ycoord):
        if self.clicked_point is not None:
            print('self.clicked_point is defined')

    # Function to create the figure and subplots
    def create_figure_section(self):
        # Check if fig is None (first time)
        if self.figure_section is None or not plt.fignum_exists(self.figure_section.number):
            # Get the screen size
            # Get the screen dimensions
            screen_info = get_monitors()
            screen_width = screen_info[0].width
            screen_height = screen_info[0].height

            # Calculate the dimensions for the new figure (one quarter of the screen size)
            figure_width = screen_width / 2
            figure_height = screen_height / 2
            int_figure_width = int(figure_width)
            int_figure_height = int(figure_height)  

            # Create a new figure with the specified dimensions and position
            self.figure_section = plt.figure(figsize=(int_figure_width, int_figure_height))
            manager = plt.get_current_fig_manager()
            manager.window.setGeometry(0, 0, int_figure_width, int_figure_height)
            # Add two subplots side by side
            self.axes_section = self.figure_section.subplots(1, 2)
        return self.figure_section, self.axes_section


    def plot_pixel_xy_m(self):
        if self.signal_connected:
            xcoord = self.clicked_x
            ycoord = self.clicked_y
        else:
            xcoord = float(self.lineEdit_xpixel.text())
            ycoord = float(self.lineEdit_ypixel.text())
        
        if self.abs_min_x == None or self.abs_min_y:
            self.abs_min_x = min(mct.nodelist[:,1])
            self.abs_max_x = max(mct.nodelist[:,1])
            self.abs_min_y = min(mct.nodelist[:,2])
            self.abs_max_y = max(mct.nodelist[:,2])

        # Create the infinite lines
        x_line = pg.InfiniteLine(pos=ycoord, angle=0, pen=pg.mkPen('r', width=4))
        y_line = pg.InfiniteLine(pos=xcoord, angle=90, pen=pg.mkPen('g', width=4))
        # Add the lines to the plot
        self.plot2d.addItem(x_line)
        self.plot2d.addItem(y_line)
        self.staticPlotItems.append(x_line)
        self.staticPlotItems.append(y_line)
        # Calculate the intersection point
        intersection_x = xcoord
        intersection_y = ycoord

        # Create the arrows with positions at the intersection point
        arrow_x = pg.ArrowItem(angle=-90, tipAngle=30, baseAngle=20, headLen=20, tailLen=20, tailWidth=0, pos=(intersection_x, intersection_y), pen=pg.mkPen('r', width=2))
        arrow_y = pg.ArrowItem(angle=0, tipAngle=30, baseAngle=20, headLen=20, tailLen=20, tailWidth=0, pos=(intersection_x, intersection_y), pen=pg.mkPen('g', width=2))

        self.plot2d.addItem(arrow_x)
        self.plot2d.addItem(arrow_y)
        self.staticPlotItems.append(arrow_x)
        self.staticPlotItems.append(arrow_y)
        #chk2dpixel_pm = self.check_2d_pixel_pm.isChecked()
        LCO_matrix = mct.elconnect[:,1:9]
        LCO = LCO_matrix.astype(int)
        xyz = mct.nodelist
        xy_pairs = (np.unique(xyz[:,1]),np.unique(xyz[:,2]))
        if mct.sorted_faces_x == None :
            mct.sorted_faces_x, mct.sorted_faces_y  = mf.find_pixel_xy(LCO, xyz, xy_pairs)
            sorted_faces_x = mct.sorted_faces_x
            sorted_faces_y = mct.sorted_faces_y
        else:
            sorted_faces_x = mct.sorted_faces_x
            sorted_faces_y = mct.sorted_faces_y
        
        # You are expecting to find element within the dimension of the grid
        toll_xeldim = float(self.lineEdit_xeldim.text())/2
        toll_yeldim = float(self.lineEdit_yeldim.text())/2

        # Convert sorted_faces to a Numpy array with object dtype
        sorted_faces_x_array = np.array(sorted_faces_x, dtype=object)
        sorted_faces_y_array = np.array(sorted_faces_y, dtype=object)

        # Find matching rows efficiently
        matching_rows_x = np.where(np.abs(sorted_faces_x_array[:, 0] - xcoord) < toll_xeldim)[0]
        matching_rows_y = np.where(np.abs(sorted_faces_y_array[:, 0] - ycoord) < toll_yeldim)[0]
        
        start_time = time.time()
        # Create a figure with two subplots
        self.figure_section, self.axes_section = self.create_figure_section()
        # Clear the existing plots on the subplots (optional)
        #plt.clf()
        for ax in self.figure_section.axes:
            ax.cla()

        for index in matching_rows_x:
            face = sorted_faces_x_array[index]

            coords = [(xyz[face[2][0], 2], xyz[face[2][0], 3]),
                    (xyz[face[2][1], 2], xyz[face[2][1], 3]),
                    (xyz[face[2][2], 2], xyz[face[2][2], 3]),
                    (xyz[face[2][3], 2], xyz[face[2][3], 3])]
            #
            # Plot rectangles with green filling on the left subplot
            self.figure_section.axes[0].set_aspect('equal')
            polygon = Polygon(coords, closed=True, facecolor='green', edgecolor='black',  alpha=0.3)
            self.figure_section.axes[0].add_patch(polygon)
        margin_tolerance = 0.05*self.abs_max_y
        if abs(self.abs_min_y) < margin_tolerance:
            self.abs_min_y = - margin_tolerance
        
        if self.abs_min_y < 0:
            coeff = 1.05
        else:
            coeff = 0.95
        if self.abs_max_y < 0:
            coeffm = .95
        else:
            coeffm = 1.05
        self.figure_section.axes[0].hlines(y=mct.zcoords[self.combo_slices.currentIndex()], xmin=coeff*self.abs_min_y, xmax=coeffm*self.abs_max_y, colors='k', linewidth=3)  # Horizontal line
        self.figure_section.axes[0].vlines(x=ycoord, ymin=0.5*min(mct.zcoords[:]), ymax=1.5*max(mct.zcoords[:]), colors='r', linewidth=3)  # Vertical line
        self.figure_section.axes[0].set_title('X section ')        
        self.figure_section.axes[0].set_xlim(coeff*self.abs_min_y, coeffm*self.abs_max_y)
        self.figure_section.axes[0].set_ylim(0.95*min(mct.zcoords[:]), 1.3*max(mct.zcoords[:]))
        self.figure_section.axes[0].set_aspect('equal', 'box')
        #
        for index in matching_rows_y:
            face = sorted_faces_y_array[index]

            coords = [(xyz[face[2][0], 1], xyz[face[2][0], 3]),
                    (xyz[face[2][1], 1], xyz[face[2][1], 3]),
                    (xyz[face[2][2], 1], xyz[face[2][2], 3]),
                    (xyz[face[2][3], 1], xyz[face[2][3], 3])]

            # Plot rectangles with red filling on the right subplot
            self.figure_section.axes[1].set_aspect('equal')
            polygon = Polygon(coords, closed=True, facecolor='red', edgecolor='black',  alpha=0.3)
            self.figure_section.axes[1].add_patch(polygon)

        margin_tolerance = 0.05*self.abs_max_x
        if abs(self.abs_min_x) < margin_tolerance:
            self.abs_min_x = - margin_tolerance
        
        if self.abs_min_x < 0:
            coeff = 1.05
        else:
            coeff = 0.95
        if self.abs_max_x < 0:
            coeffm = 0.95
        else:
            coeffm = 1.05
        
        self.figure_section.axes[1].hlines(y=mct.zcoords[self.combo_slices.currentIndex()], xmin=coeff*self.abs_min_x, xmax= coeffm*self.abs_max_x, colors='k', linewidth=3)  # Horizontal line
        self.figure_section.axes[1].vlines(x=xcoord, ymin=0.5*min(mct.zcoords[:]), ymax=1.5*max(mct.zcoords[:]), colors='g', linewidth=3)  # Vertical line
        self.figure_section.axes[1].set_title('Y Section')
        self.figure_section.axes[1].set_xlim(coeff*self.abs_min_x, coeffm*self.abs_max_x)
        self.figure_section.axes[1].set_ylim(0.95*min(mct.zcoords[:]), 1.3*max(mct.zcoords[:]))
        self.figure_section.axes[1].set_aspect('equal', 'box')

        #plt.tight_layout()  # Adjust spacing between subplots
        plt.show()

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Elapsed time plot_pixel_xy function: {elapsed_time:.2f} seconds (excluding pixel_find)")

        # Store the polygon items if needed
        # self.staticPlotItems.extend(polygon_items)


    def plot_pixel(self):
        chk2dpixel_pm = self.check_2d_pixel_pm.isChecked()
        LCO_matrix = mct.elconnect[:,1:9]
        LCO = LCO_matrix.astype(int)
        xyz = mct.nodelist
        if mct.sorted_faces == None :
            mct.sorted_faces = mf.find_pixel(LCO, xyz, mct.zcoords)
            sorted_faces = mct.sorted_faces
        else:
            sorted_faces = mct.sorted_faces
        
        # Retrieve relevant data
        zcord = mct.zcoords[self.combo_slices.currentIndex()]
        tole = 1e-4

        # Convert sorted_faces to a Numpy array with object dtype
        sorted_faces_z_array = np.array(sorted_faces, dtype=object)

        # Find matching rows efficiently
        matching_rows = np.where(np.abs(sorted_faces_z_array[:, 0] - zcord) < tole)[0]
        
        start_time = time.time()
        polygon_items = []

        for index in matching_rows:
            face = sorted_faces_z_array[index]

            coords = [(xyz[face[2][0], 1], xyz[face[2][0], 2]),
                    (xyz[face[2][1], 1], xyz[face[2][1], 2]),
                    (xyz[face[2][2], 1], xyz[face[2][2], 2]),
                    (xyz[face[2][3], 1], xyz[face[2][3], 2])]

            # Create a list of coordinates for the exterior
            exterior_coords = list(sg.Polygon(coords).exterior.coords)
            polygon_item = pg.PlotDataItem(*zip(*exterior_coords), fillLevel=0,
                                        brush=QBrush(QColor(65, 105, 225, 100)),
                                        pen=pg.mkPen(color=(0, 0, 0, 0), width=2))
            self.plot2d.addItem(polygon_item)
            polygon_items.append(polygon_item)

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Elapsed time plot_pixel function: {elapsed_time:.2f} seconds (excluding pixel_find)")

        # Store the polygon items if needed
        self.staticPlotItems.extend(polygon_items)
    
    def plot_pixel_old(self):
        chk2dpixel_pm = self.check_2d_pixel_pm.isChecked()
        LCO_matrix = mct.elconnect[:,1:9]
        LCO = LCO_matrix.astype(int)
        xyz = mct.nodelist
        if mct.sorted_faces == None :
            mct.sorted_faces = mf.find_pixel(LCO, xyz, mct.zcoords)
            sorted_faces = mct.sorted_faces
        else:
            sorted_faces = mct.sorted_faces
        
        # This part must be improved
        start_time = time.time()  
        zcord = mct.zcoords[self.combo_slices.currentIndex()]
        # Convert tuples in sorted_faces to lists and ensure each row has the same length
        max_row_length = max(len(row) for row in sorted_faces)
        sorted_faces_fixed = np.array([list(row) + [0] * (max_row_length - len(row)) for row in sorted_faces], dtype=object)

        # Now, you can use sorted_faces_fixed in the rest of your code
        sorted_faces_z_array = sorted_faces_fixed

        #sorted_faces_z_array = np.array(sorted_faces)
        tole =1e-4
        matching_rows = np.where(abs(sorted_faces_z_array[:, 0] - zcord)<tole)
        for index in matching_rows[0]:
            face = sorted_faces_z_array[index]
            coords = [(xyz[face[2][0],1], xyz[face[2][0],2]), (xyz[face[2][1],1], xyz[face[2][1],2]), (xyz[face[2][2],1], xyz[face[2][2],2]), (xyz[face[2][3],1], xyz[face[2][3],2])]
            polygs = sg.Polygon(coords)
            try:
                if len(polygs) > 1:
                    for geom in polygs:
                        ext_x, ext_y = geom.exterior.xy
                        polygon_item = pg.PlotDataItem(ext_x, ext_y, fillLevel=0, brush=QBrush(QColor(65, 105, 225, 100)), pen=pg.mkPen(color=(0, 0, 0, 0), width=2))
                        self.plot2d.addItem(polygon_item)
                        self.staticPlotItems.append(polygon_item)
                        #print('plotting face ', str(face), '- a' )
            except TypeError:
                ext_x, ext_y = polygs.exterior.xy
                polygon_item = pg.PlotDataItem(ext_x, ext_y, fillLevel=0, brush=QBrush(QColor(65, 105, 225, 100)), pen=pg.mkPen(color=(0, 0, 0, 0), width=2))
                self.plot2d.addItem(polygon_item)
                self.staticPlotItems.append(polygon_item)
                #print('plotting face ', str(face), '- b' )
                if len(polygs.interiors) > 0:
                    for hole in polygs.interiors:
                        int_x, int_y = hole.xy
                        polygon_item = pg.PlotDataItem(int_x, int_y, fillLevel=0, brush=QBrush(QColor(255, 255, 255, 255)), pen=pg.mkPen(color=(0, 0, 0, 0), width=2))
                        self.plot2d.addItem(polygon_item)
                        self.staticPlotItems.append(polygon_item)
                        #print('plotting face ', str(face), '- c' )
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Elapsed time plot_pixel function: {elapsed_time:.2f} seconds (excluding pixel_find)")
    
    def plot_polylines(self):
        for poly in mct.polys[mct.zcoords[self.combo_slices.currentIndex()]]:
            item = pg.PlotCurveItem(pen=pg.mkPen(color=(0, 0, 255, 255), width=3))
            item.setData(poly[:, 0], poly[:, 1])
            self.plot2d.addItem(item)
            self.staticPlotItems.append(item)
        chk2dplines_pm = self.check_2d_polylines_pm.isChecked()
        if chk2dplines_pm :
            self.plot2d.setTitle("<span style=\"color:red;font-size:12pt\">-- Upper Slice hint</span><BR><span style=\"color:blue;font-size:12pt\">-- Current Slice</span><BR><span style=\"color:green;font-size:12pt\">-- Lower Slice hint</span>")
            slice_n = self.combo_slices.currentIndex()
            if slice_n < len(mct.zcoords)-1 :
                for poly in mct.polys[mct.zcoords[slice_n+1]]:
                    item = pg.PlotCurveItem(pen=pg.mkPen(color=(255, 0, 0, 100), width=3, style=Qt.DashLine))
                    item.setData(poly[:, 0], poly[:, 1])
                    self.plot2d.addItem(item)
                    self.staticPlotItems.append(item)
            if slice_n > 0 :
                for poly in mct.polys[mct.zcoords[slice_n-1]]:
                    item = pg.PlotCurveItem(pen=pg.mkPen(color=(0, 255, 0, 100), width=3, style=Qt.DashLine))
                    item.setData(poly[:, 0], poly[:, 1])
                    self.plot2d.addItem(item)
                    self.staticPlotItems.append(item)
    
    def plot_polys_clean(self):
        for poly in mct.cleanpolys[mct.zcoords[self.combo_slices.currentIndex()]]:
            item = pg.PlotCurveItem(pen=pg.mkPen(color=(0, 0, 0, 255), width=5))
            item.setData(poly[:, 0], poly[:, 1])
            #item.setBrush(pg.mkBrush(color=(255, 0, 0, 255)))
            self.plot2d.addItem(item)
            self.staticPlotItems.append(item)
            pts = pg.ScatterPlotItem(pos=poly[:, : 2], size=9, brush=pg.mkBrush(255, 0, 0, 255), symbol='s')
            self.plot2d.addItem(pts)
            self.staticPlotItems.append(pts)
        chk2dplclean_pm = self.check_2d_polylines_clean_pm.isChecked()
        if chk2dplclean_pm :
            self.plot2d.setTitle("<span style=\"color:red;font-size:12pt\">-- Upper Slice hint</span><BR><span style=\"color:black;font-size:12pt\">-- Current Slice</span><BR><span style=\"color:green;font-size:12pt\">-- Lower Slice hint</span>")
            slice_n = self.combo_slices.currentIndex()
            if slice_n < len(mct.zcoords)-1 :
                for poly in mct.cleanpolys[mct.zcoords[slice_n+1]]:
                    item = pg.PlotCurveItem(pen=pg.mkPen(color=(255, 0, 0, 100), width=3, style=Qt.DashLine))
                    item.setData(poly[:, 0], poly[:, 1])
                    self.plot2d.addItem(item)
                    self.staticPlotItems.append(item)
                    pts = pg.ScatterPlotItem(pos=poly[:, : 2], size=6, brush=pg.mkBrush(255, 0, 0, 100), symbol='o')
                    self.plot2d.addItem(pts)
                    self.staticPlotItems.append(pts)
            if slice_n > 0 :
                for poly in mct.cleanpolys[mct.zcoords[slice_n-1]]:
                    item = pg.PlotCurveItem(pen=pg.mkPen(color=(0, 255, 0, 100), width=3, style=Qt.DashLine))
                    item.setData(poly[:, 0], poly[:, 1])
                    self.plot2d.addItem(item)
                    self.staticPlotItems.append(item)
                    pts = pg.ScatterPlotItem(pos=poly[:, : 2], size=6, brush=pg.mkBrush(0, 255, 0, 100), symbol='t')
                    self.plot2d.addItem(pts)
                    self.staticPlotItems.append(pts)
    
    def plot_polygs_clean_old(self):
        # This part must be improved
        polygs = mct.polygs[mct.zcoords[self.combo_slices.currentIndex()]]

        try:
            if len(polygs) > 1:
                for geom in polygs:
                    ext_x, ext_y = geom.exterior.xy
                    polygon_item = pg.PlotDataItem(ext_x, ext_y, fillLevel=0, brush=QBrush(QColor(100, 100, 100, 100)), pen=pg.mkPen(color=(0, 0, 0, 0), width=2))
                    self.plot2d.addItem(polygon_item)
                    self.staticPlotItems.append(polygon_item)
        except TypeError:
            ext_x, ext_y = polygs.exterior.xy
            polygon_item = pg.PlotDataItem(ext_x, ext_y, fillLevel=0, brush=QBrush(QColor(100, 100, 100, 100)), pen=pg.mkPen(color=(0, 0, 0, 0), width=2))
            self.plot2d.addItem(polygon_item)
            self.staticPlotItems.append(polygon_item)
            if len(polygs.interiors) > 0:
                for hole in polygs.interiors:
                    int_x, int_y = hole.xy
                    polygon_item = pg.PlotDataItem(int_x, int_y, fillLevel=0, brush=QBrush(QColor(255, 255, 255, 255)), pen=pg.mkPen(color=(0, 0, 0, 0), width=2))
                    self.plot2d.addItem(polygon_item)
                    self.staticPlotItems.append(polygon_item)
    
    def plot_polygs_clean(self):
        #
        polygs = mct.polygs[mct.zcoords[self.combo_slices.currentIndex()]]

        if isinstance(polygs, sg.MultiPolygon):
            for geom in polygs.geoms:
                ext_x, ext_y = geom.exterior.xy
                polygon_item = pg.PlotDataItem(ext_x, ext_y, fillLevel=0, brush=QBrush(QColor(100, 100, 100, 100)), pen=pg.mkPen(color=(0, 0, 0, 0), width=2))
                self.plot2d.addItem(polygon_item)
                self.staticPlotItems.append(polygon_item)
        elif isinstance(polygs, sg.Polygon):
            ext_x, ext_y = polygs.exterior.xy
            polygon_item = pg.PlotDataItem(ext_x, ext_y, fillLevel=0, brush=QBrush(QColor(100, 100, 100, 100)), pen=pg.mkPen(color=(0, 0, 0, 0), width=2))
            self.plot2d.addItem(polygon_item)
            self.staticPlotItems.append(polygon_item)
            
            if polygs.interiors:
                for hole in polygs.interiors:
                    int_x, int_y = hole.xy
                    polygon_item = pg.PlotDataItem(int_x, int_y, fillLevel=0, brush=QBrush(QColor(255, 255, 255, 255)), pen=pg.mkPen(color=(0, 0, 0, 0), width=2))
                    self.plot2d.addItem(polygon_item)
                    self.staticPlotItems.append(polygon_item)


            

    def main2dplot(self):
        chk2dsli = self.check_2d_slice.isChecked()
        chk2centr = self.check_2d_centr.isChecked()
        chk2dplines = self.check_2d_polylines.isChecked()
        chk2dplclean = self.check_2d_polylines_clean.isChecked()
        chk2dpixel = self.check_2d_pixel.isChecked()
        #
        self.plot2d.setTitle('')
        #
        chk2dgrid = self.check_2d_grid.isChecked()
        chk2dpolygons = self.check_2d_polygons.isChecked() # Polygons
        # self.plot2d.clear()
        for item in self.staticPlotItems:
            self.plot2d.removeItem(item)
        self.staticPlotItems = []
        try:
            try:
                if chk2dgrid:
                    self.plot_grid()
            except:
                pass
            if chk2dpolygons and mct.polygs is not None:
                self.plot_polygs_clean()
            if chk2dplines and mct.polys is not None:
                self.plot_polylines()
            if chk2dplclean and mct.cleanpolys is not None:
                self.plot_polys_clean()
            if chk2dsli and mct.slices is not None:
                self.plot_slice()
            if chk2centr and mct.ctrds is not None:
                self.plot_centroids()
            if chk2dpixel and mct.elconnect is not None:
                self.plot_pixel()
            # if mct.temp_scatter is not None:
            #     self.plot2d.addItem(mct.temp_scatter)
        except KeyError:
            print('Error in func main2dplot')
            # pass  # KeyError is raised when re-slicing. It shouldn't cause any problem

    
    def updateOffDistance(self):
        """ This method is needed to update the offset distance when
        a new value is set in the lineEdit widget.
        """
        try:
            self.editInstance[0].offset = float(self.lineEdit_off.text())
        except ValueError:
            pass
    
    def keyPressEvent(self, event):
        ''' This method already exists in the inherited QMainWindow class.
            Here it is overwritten to adapt key events to this app.
        '''
        if self.emode is not None:
            self.lineEdit_off.setEnabled(False)
            self.plot2d.clear()
            self.main2dplot()
            if self.emode == 'polylines':
                self.tempPolylines = []
                for edI in self.editInstance:
                    edI.stop()
                    if self.polylinesTool in ['addponline', 'movepoint']:
                        self.tempPolylines.append(edI.pll)
                    elif self.polylinesTool in ['removepoint']:
                        if edI.pts_b.shape[0] != 0:  # Remove empty array when a polyline is completely deleted removing its points
                            self.tempPolylines.append(edI.pts_b)
                    else:
                        self.tempPolylines = edI.plls
                if event.key() == Qt.Key_D:
                    self.plot2d.setTitle('<strong><u><big><mark>D draw</strong>, J join, R remove polyline, A add point, M move point, P remove points, O offset')
                    self.polylinesTool = 'draw'
                    self.editInstance = [ptd.DrawPolyline(self.tempPolylines, self.plot2d, 10)]
                elif event.key() == Qt.Key_J:
                    self.plot2d.setTitle('D draw, <strong><u><big><mark>J join</strong>, R remove polyline, A add point, M move point, P remove points, O offset')
                    self.polylinesTool = 'join'
                    self.editInstance = [ptd.JoinPolylines(self.tempPolylines, self.plot2d, 10)]
                elif event.key() == Qt.Key_R:
                    self.plot2d.setTitle('D draw, J join, <strong><u><big><mark>R remove polyline</strong>, A add point, M move point, P remove points, O offset')
                    self.polylinesTool = 'rempoly'
                    self.editInstance = [ptd.RemovePolyline(self.tempPolylines, self.plot2d, 10)]
                elif event.key() == Qt.Key_A:
                    self.plot2d.setTitle('D draw, J join, R remove polyline, <strong><u><big><mark>A add point</strong>, M move point, P remove points, O offset')
                    self.polylinesTool = 'addponline'
                    self.editInstance = [ptd.AddPointOnLine(pll, self.plot2d, 10) for pll in self.tempPolylines]
                elif event.key() == Qt.Key_M:
                    self.plot2d.setTitle('D draw, J join, R remove polyline, A add point, <strong><u><big><mark>M move point</strong>, P remove points, O offset')
                    self.polylinesTool = 'movepoint'
                    self.editInstance = [ptd.MovePoint(pll, self.plot2d, 10, addline=True) for pll in self.tempPolylines]
                elif event.key() == Qt.Key_P:
                    self.plot2d.setTitle('D draw, J join, R remove polyline, A add point, M move point, <strong><u><big><mark>P remove points</strong>, O offset')
                    self.polylinesTool = 'removepoint'
                    self.editInstance = [ptd.RemovePointsRect(pll,self.plot2d, 10, addline=True) for pll in self.tempPolylines]
                elif event.key() == Qt.Key_O:
                    self.plot2d.setTitle('D draw, J join, R remove polyline, A add point, M move point, P remove points, <strong><u><big><mark>O offset</strong>')
                    self.polylinesTool = 'offset'
                    self.lineEdit_off.setEnabled(True)
                    self.editInstance = [ptd.OffsetPolyline(self.tempPolylines,self.plot2d, 10, float(self.lineEdit_off.text()))]
            elif self.emode == 'points':
                self.plot2d.clear()
                self.tempPoints = self.editInstance[0].pts_b
                if event.key() == Qt.Key_R:
                    self.plot2d.setTitle('<strong><u><big><mark>R remove points (click)</strong>, P remove points (rect selection)')
                    self.pointsTool = 'remove'
                    self.editInstance = [ptd.RemovePointsClick(self.tempPoints, self.plot2d, 10)]
                elif event.key() == Qt.Key_P:
                    self.plot2d.setTitle('R remove points (click), <strong><u><big><mark>P remove points (rect selection)</strong>')
                    self.pointsTool = 'removerect'
                    self.editInstance = [ptd.RemovePointsRect(self.tempPoints, self.plot2d, 10)]
            elif self.emode == 'centroids':
                self.plot2d.clear()
                self.tempCentroids = self.editInstance[0].pts_b
                if event.key() == Qt.Key_R:
                    self.plot2d.setTitle('<strong><u><big><mark>R remove points (click)</strong>, P remove points (rect selection)')
                    self.pointsTool = 'remove'
                    self.editInstance = [ptd.RemovePointsClick(self.tempCentroids, self.plot2d, 10)]
                elif event.key() == Qt.Key_P:
                    self.plot2d.setTitle('R remove points (click), <strong><u><big><mark>P remove points (rect selection)</strong>')
                    self.pointsTool = 'removerect'
                    self.editInstance = [ptd.RemovePointsRect(self.tempCentroids, self.plot2d, 10)]
      
            for edI in self.editInstance:
                edI.start()

    
    def editMode(self):
        """ This method initializes the edit mode with a default tool
        """
        self.combo_slices.setEnabled(False)
        self.btn_edit.setEnabled(False)
        self.btn_edit_finalize.setEnabled(True)
        self.btn_edit_discard.setEnabled(True)
        self.gui_edit_status(False)
        if self.radioPoints.isChecked():
            self.plot2d.setTitle('R remove points (click), <strong><u><big><mark>P remove points (rect selection)</strong>')
            self.emode = 'points'
            self.pointsTool = 'removerect'
            self.tempPoints = mct.slices[mct.zcoords[self.combo_slices.currentIndex()]].copy()
            self.editInstance = [ptd.RemovePointsRect(self.tempPoints, self.plot2d, 10)]
            self.editInstance[0].start()
        elif self.radioCentroids.isChecked():
            self.plot2d.setTitle('R remove points (click), <strong><u><big><mark>P remove points (rect selection)</strong>')
            self.emode = 'centroids'
            self.pointsTool = 'removerect'
            self.tempCentroids = mct.ctrds[mct.zcoords[self.combo_slices.currentIndex()]].copy()
            self.editInstance = [ptd.RemovePointsRect(self.tempCentroids, self.plot2d, 10)]
            self.editInstance[0].start()
        elif self.radioPolylines.isChecked():
            self.plot2d.setTitle('<strong><u><big><mark>D draw</strong>, J join, R remove polyline, A add point, M move point, P remove points, O offset')
            self.emode = 'polylines'
            self.polylinesTool = 'draw'
            self.tempPolylines = mct.cleanpolys[mct.zcoords[self.combo_slices.currentIndex()]].copy()
            self.editInstance = [ptd.DrawPolyline(self.tempPolylines, self.plot2d, 10)]
            self.editInstance[0].start()

    
    def save_changes(self):
        """ This method exits the edit mode and updates data.
        """
        if self.emode == 'polylines':
            self.tempPolylines = []
            for edI in self.editInstance:
                edI.stop()
                if self.polylinesTool in ['addponline', 'movepoint']:
                    self.tempPolylines.append(edI.pll)
                elif self.polylinesTool in ['removepoint']:
                    if edI.pts_b.shape[0] != 0:  # Remove empty array when a polyline is completely deleted removing its points
                        self.tempPolylines.append(edI.pts_b)
                else:
                    self.tempPolylines = edI.plls      
            mct.cleanpolys[mct.zcoords[self.combo_slices.currentIndex()]] = self.tempPolylines
            self.polylinesTool = 'draw'
            self.emode = None
            self.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
            
        elif self.emode == 'points':
            for edI in self.editInstance:
                edI.stop()
            mct.slices[mct.zcoords[self.combo_slices.currentIndex()]] = self.editInstance[0].pts_b
            self.pointsTool = 'remove'
            self.emode = None
            self.status_centroids.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_polylines.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")

        elif self.emode == 'centroids':
            for edI in self.editInstance:
                edI.stop()
            mct.ctrds[mct.zcoords[self.combo_slices.currentIndex()]] = self.editInstance[0].pts_b
            self.pointsTool = 'remove'
            self.emode = None
            self.status_polylines.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
    
        self.combo_slices.setEnabled(True)
        self.btn_edit.setEnabled(True)
        self.btn_edit_finalize.setEnabled(False)
        self.btn_edit_discard.setEnabled(False)
        self.gui_edit_status(True)
        self.lineEdit_off.setEnabled(False)
        self.plot2d.setTitle('')
        self.plot2d.clear()
        self.main2dplot()
    

    def discard_changes(self):
        """ This method exits the edit mode without
        altering the original data.
        """
        if self.emode == 'polylines':
            for edI in self.editInstance:
                edI.stop()
            self.polylinesTool = 'draw'
            # self.plotStaticData()
            self.emode = None
            self.tempPolylines = None
        elif self.emode == 'points' or self.emode == 'centroids':
            for edI in self.editInstance:
                edI.stop()
            self.emode = None
            self.tempPoints = None
            self.tempCentroids = None
        
        self.combo_slices.setEnabled(True)
        self.btn_edit.setEnabled(True)
        self.btn_edit_finalize.setEnabled(False)
        self.btn_edit_discard.setEnabled(False)
        self.gui_edit_status(True)
        self.lineEdit_off.setEnabled(False)
        self.plot2d.setTitle('')
        self.plot2d.clear()
        self.main2dplot()
    

    def gui_edit_status(self, torf):
        self.btn_gen_slices.setEnabled(torf)
        self.btn_gen_centr.setEnabled(torf)
        self.rbtn_fixnum.setEnabled(torf)
        self.rbtn_fixstep.setEnabled(torf)
        self.rbtn_custom_slices.setEnabled(torf)
        self.lineEdit_from.setEnabled(torf)
        self.lineEdit_to.setEnabled(torf)
        self.lineEdit_steporN.setEnabled(torf)
        self.lineEdit_thick.setEnabled(torf)
        self.menubar.setEnabled(torf)
        if mct.slices is not None:
            self.lineEdit_wall_thick.setEnabled(torf)
        if mct.ctrds is not None:
            self.btn_gen_polylines.setEnabled(torf)
        if mct.cleanpolys is not None:
            self.btn_gen_polygons.setEnabled(torf)
        if mct.polygs is not None:
            self.btn_gen_mesh.setEnabled(torf)


    def copy_polylines(self):
        copydialog = loadUi("gui_copypolylines_dialog.ui")
        copydialog.setWindowTitle("Copy slice's polylines")
        copydialog.combo_copy_pl.clear()

        for z in mct.zcoords:
            copydialog.combo_copy_pl.addItem(str('%.3f' % z))

        paste_slice = []
        for z in mct.zcoords:
            slice_index = np.where(z == mct.zcoords[:])[0][0]
            paste_slice += [QtWidgets.QCheckBox()]
            paste_slice[slice_index].setText(str('%.3f' % z))
            copydialog.scrollArea_lay.layout().addWidget(paste_slice[slice_index])

        def sel_all():
            for checkbox in paste_slice:
                checkbox.setChecked(True)

        def desel_all():
            for checkbox in paste_slice:
                checkbox.setChecked(False)

        def cancel():
            copydialog.close()

        def copy_ok():
            tocopy = mct.cleanpolys[mct.zcoords[copydialog.combo_copy_pl.currentIndex()]]
            for i in range(len(paste_slice)):
                if paste_slice[i].isChecked():
                    mct.cleanpolys[mct.zcoords[i]] = tocopy
            win.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
            win.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
            copydialog.close()

        copydialog.btn_sel_all.clicked.connect(sel_all)
        copydialog.btn_desel_all.clicked.connect(desel_all)
        copydialog.btn_cancel.clicked.connect(cancel)
        copydialog.btn_ok.clicked.connect(copy_ok)
        copydialog.exec_()

class StreamToTextEdit:
    def __init__(self, text_edit, stream, filename):
        self.text_edit = text_edit
        self.stream = stream
        self.log_file = filename

    def write(self, text):
        self.stream.write(text)
        self.text_edit.moveCursor(QTextCursor.End)
        self.text_edit.insertPlainText(text)
        self.writef(text)
    
    def writef(self, text):        
        with open(self.log_file, 'a') as f:
            f.write(text)

app = QApplication(sys.argv)
#
# Create an instance of the Logger class and redirect stdout

#
win = Window()
win.show()
sys.exit(app.exec_())
# app.exec_() ## good alternative to sys.exit(app.exec_())
