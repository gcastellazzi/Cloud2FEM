import shelve
import numpy as np
from pyntcloud import PyntCloud
import shapely.geometry as sg
import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QDialog
from PyQt5.uic import loadUi
import pyqtgraph as pg
from pyqtgraph import PlotWidget
# import pyqtgraph.opengl as gl     # serve per il plot pyqtgraph 3D che non sto usando

from Vispy3DViewer import Visp3dplot
import Cloud2Polygons as cp
import Polygons2FEM as pf


# import ezdxf
# from ezdxf.addons.geo import GeoProxy
#import FEM_functions as ff


##### PASSO PER TEST SU NUVOLA IDEALE
# MEDIO: from 0.3 to 6.5, n°slices 13, slice thickness 0.01
# GREZZO: from 0.3 to 4.3, n°slices 7,  slice thickness 0.01
# git updaate test
# git update test 2
#############


class MainContainer:
    def __init__(self, filepath=None, pcl=None, npts=None, zmin=None, zmax=None,
                 xmin=None, xmax=None, ymin=None, ymax=None, zcoords=None,
                 slices=None, netpcl=None, ctrds=None, polys=None, cleanpolys=None,
                 polygs=None, xngrid=None, xelgrid=None, yngrid=None, yelgrid=None,
                 elemlist=None, nodelist=None, elconnect=None, temp_points=None,
                 temp_scatter=None, temp_polylines=None, temp_roi_plot=None,
                 editmode=None, roiIndex=None):
        self.filepath = filepath
        self.pcl = pcl              # Whole PCl as a 3-columns xyz numpy array
        self.npts = npts            # the above 'pcl' number of points
        self.zmin = zmin
        self.zmax = zmax
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
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
        self.temp_points = temp_points  # Modified array of PCloud points or centroids
        self.temp_scatter = temp_scatter  # Modified scatter of PCloud points or centroids
        self.temp_polylines = temp_polylines  # Modified polylines: [[np.arr.poly1], [np.arr.poly2], ...]
        self.temp_roi_plot = temp_roi_plot  # Modified polylines plot
        self.editmode = editmode    # Edit Mode ID: 0=slice, 1=centroids, 2=polylines
        self.roiIndex = roiIndex    # Index of the roiPolyline in the edit mode


mct = MainContainer()  # All the main variables are stored here


def save_project():
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

def open_project():
        try:
            fd = QFileDialog()
            filepath = fd.getOpenFileName(parent=None, caption="Open Project", directory="",
                                         filter="Cloud2FEM Data (*.cloud2fem.dat)")[0]
            s = shelve.open(filepath[: -4])

            mct.npts = s['npts']
            mct.zmin = s['zmin']
            mct.zmax = s['zmax']
            mct.xmin = s['xmin']
            mct.xmax = s['xmax']
            mct.ymin = s['ymin']
            mct.ymax = s['ymax']
            mct.zcoords = s['zcoords']
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

            for z in mct.zcoords:
                win.combo_slices.addItem(str('%.3f' % z))
            win.main2dplot()

            win.label_zmin_value.setText(str(mct.zmin))
            win.label_zmax_value.setText(str(mct.zmax))
            win.btn_3dview.setEnabled(True)
            win.check_pcl_slices.setEnabled(True)
            win.status_slices.setStyleSheet("background-color: rgb(0, 255, 0);")
            win.btn_gen_centr.setEnabled(True)
            win.lineEdit_wall_thick.setEnabled(True)
            win.lineEdit_xeldim.setEnabled(True)
            win.lineEdit_yeldim.setEnabled(True)
            win.btn_edit_slice.setEnabled(True)
            win.check_pcl.setChecked(False)
            win.check_pcl.setEnabled(False)

            if mct.ctrds != None:
                win.check_centroids.setEnabled(True)
                win.status_centroids.setStyleSheet("background-color: rgb(0, 255, 0);")
                win.btn_gen_polylines.setEnabled(True)
                win.btn_edit_centroids.setEnabled(True)
            if mct.cleanpolys != None:
                win.check_polylines.setEnabled(True)
                win.status_polylines.setStyleSheet("background-color: rgb(0, 255, 0);")
                win.btn_gen_polygons.setEnabled(True)
                win.btn_edit_polylines.setEnabled(True)
                win.btn_copy_plines.setEnabled(True)
            if mct.polygs != None:
                win.status_polygons.setStyleSheet("background-color: rgb(0, 255, 0);")
                win.btn_gen_mesh.setEnabled(True)
                win.exp_dxf.setEnabled(True)
            if mct.elemlist != None:
                win.status_mesh.setStyleSheet("background-color: rgb(0, 255, 0);")
                win.exp_mesh.setEnabled(True)

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
        mct.filepath = getfile[0]
        wholepcl = PyntCloud.from_file(mct.filepath)
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
        print("\nPoint Cloud of " + str(mct.pcl.shape[0]) + " points loaded, file path: " + mct.filepath)
        print("First three points:\n" + str(mct.pcl[:3]))
        print("Last three points:\n" + str(mct.pcl[-3:]))
        if len(mct.filepath) < 65:
            win.loaded_file.setText("Loaded Point Cloud: " + mct.filepath + "   ")
        else:
            slashfound = 0
            head_reverse = ''
            for char in mct.filepath[:30][::-1]:
                if char == '/' and slashfound == 0:
                    slashfound += 1
                elif slashfound == 0:
                    continue
                else:
                    head_reverse += char
            path_head = head_reverse[::-1]

            slashfound = 0
            path_tail = ''
            for char in mct.filepath[30:]:
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







class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        loadUi("gui_main.ui", self)
        self.setWindowTitle('Cloud2FEM')
        self.graphlayout.setBackground((255, 255, 255))
        self.plot2d = self.graphlayout.addPlot()
        self.plot2d.setAspectLocked(lock=True)
        # self.plot2d.enableAutoRange(enable=False)  # Da sistemare, mantiene gli assi bloccati quando aggiorno il plot?

        self.Load_PC.triggered.connect(loadpcl)
        self.save_project.triggered.connect(save_project)
        self.open_project.triggered.connect(open_project)
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
        self.check_2d_polygons.toggled.connect(self.main2dplot)
        self.lineEdit_xeldim.editingFinished.connect(self.main2dplot)
        self.lineEdit_yeldim.editingFinished.connect(self.main2dplot)

        self.btn_edit_slice.clicked.connect(self.edit_slice)
        self.btn_edit_centroids.clicked.connect(self.edit_centroids)
        self.btn_edit_polylines.clicked.connect(self.edit_polylines)
        self.btn_add_polyline.clicked.connect(self.add_polyline)
        self.btn_edit_discard.clicked.connect(self.discard_edit)
        self.btn_edit_finalize.clicked.connect(self.finalize_edit)
        self.btn_copy_plines.clicked.connect(self.copy_polylines)




        # TEST plot poligoni #################################
        self.pushtest.clicked.connect(test_plotpolygons)
        ######################################################


    def genslices_clicked(self):
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
                self.btn_edit_slice.setEnabled(True)
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

    def gencentr_clicked(self):
        try:
            minwthick = float(self.lineEdit_wall_thick.text())
            
            mct.ctrds = cp.find_centroids(minwthick, mct.zcoords, mct.slices)
            
            self.check_centroids.setEnabled(True)
            self.btn_edit_centroids.setEnabled(True)
            self.btn_gen_polylines.setEnabled(True)
            self.status_centroids.setStyleSheet("background-color: rgb(0, 255, 0);")
            self.status_polylines.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
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
        minwthick = float(self.lineEdit_wall_thick.text())
        
        mct.polys, mct.cleanpolys = cp.make_polylines(minwthick, mct.zcoords, mct.ctrds)
        
        self.check_polylines.setEnabled(True)
        self.btn_gen_polygons.setEnabled(True)
        self.btn_edit_polylines.setEnabled(True)
        self.btn_copy_plines.setEnabled(True)
        self.status_polylines.setStyleSheet("background-color: rgb(0, 255, 0);")
        self.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
        self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
        self.main2dplot()
        msg_polysok = QMessageBox()
        msg_polysok.setWindowTitle('Generate Polylines')
        msg_polysok.setText('\nPolylines generation completed           '
                            '\n                                         ')
        x = msg_polysok.exec_()

    def genpolygons_clicked(self):
        minwthick = float(self.lineEdit_wall_thick.text())
        
        mct.polygs, invalidpolygons = cp.make_polygons(minwthick, mct.zcoords, mct.cleanpolys)
        
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
        
        self.check_mesh.setEnabled(True)
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
            p3d.print_mesh(mct)
        if chkpcl and (chksli or chkctr or chkply or chkmesh):
            p3d.print_cloud(mct.netpcl, 0.5)   ################################################################################# default alpha = 0.75
        elif chkpcl:
            p3d.print_cloud(mct.pcl, 1)
        p3d.final3dsetup()

    def plot_grid(self):
        xeldim = float(self.lineEdit_xeldim.text())
        yeldim = float(self.lineEdit_yeldim.text())
        xngrid = np.arange(mct.xmin - xeldim, mct.xmax + 2 * xeldim, xeldim)
        yngrid = np.arange(mct.ymin - yeldim, mct.ymax + 2 * yeldim, yeldim)
        for x in xngrid:
            self.plot2d.plot((x, x), (min(yngrid), max(yngrid)), pen=pg.mkPen(color=(220, 220, 220, 255), width=1.5))
        for y in yngrid:
            self.plot2d.plot((min(xngrid), max(xngrid)), (y, y), pen=pg.mkPen(color=(220, 220, 220, 255), width=1.5))

    def plot_slice(self):
        slm2dplt = mct.slices[mct.zcoords[self.combo_slices.currentIndex()]][:, [0, 1]]
        scatter2d = pg.ScatterPlotItem(pos=slm2dplt, size=5, brush=pg.mkBrush(0, 0, 0, 255))    #### default size = 5
        # scatter2d = pg.ScatterPlotItem(pos=slm2dplt, size=2.7, brush=pg.mkBrush(0, 0, 255, 255))
        self.plot2d.addItem(scatter2d)

    def plot_centroids(self):
        ctrsm2dplt = mct.ctrds[mct.zcoords[self.combo_slices.currentIndex()]][:, [0, 1]]
        # ctrsscatter2d = pg.ScatterPlotItem(pos=ctrsm2dplt, size=7, brush=pg.mkBrush(255, 0, 0, 255))
        ctrsscatter2d = pg.ScatterPlotItem(pos=ctrsm2dplt, size=13, brush=pg.mkBrush(255, 0, 0, 255)) ######### default size = 13
        self.plot2d.addItem(ctrsscatter2d)

    def plot_polylines(self):
        for poly in mct.polys[mct.zcoords[self.combo_slices.currentIndex()]]:
            # self.plot2d.plot(poly, pen=pg.mkPen(color='b', width=2))
            # colr = np.random.randint(120, 255)
            # colg = np.random.randint(1, 5)
            # colb = np.random.randint(1, 5)
            # self.plot2d.plot(poly[:, : 2], pen=pg.mkPen(color=(colr, colg, colb, 255), width=3))
            self.plot2d.plot(poly[:, : 2], pen=pg.mkPen(color=(0, 0, 255, 255), width=3))   ################### default width = 3

    def plot_polys_clean(self):
        for poly in mct.cleanpolys[mct.zcoords[self.combo_slices.currentIndex()]]:
            # colr = np.random.randint(1, 5)
            # colg = np.random.randint(1, 5)
            # colb = np.random.randint(120, 255)
            # self.plot2d.plot(poly[:, : 2], pen=pg.mkPen(color=(colr, colg, colb, 255), width=3))
            self.plot2d.plot(poly[:, : 2], pen=pg.mkPen(color=(0, 0, 0, 255), width=5))   ###### default width = 5

    def main2dplot(self):
        chk2dsli = self.check_2d_slice.isChecked()
        chk2centr = self.check_2d_centr.isChecked()
        chk2dplines = self.check_2d_polylines.isChecked()
        chk2dplclean = self.check_2d_polylines_clean.isChecked()
        chk2dgrid = self.check_2d_grid.isChecked()
        self.plot2d.clear()
        try:
            try:
                if chk2dgrid:
                    self.plot_grid()
            except:
                pass
            if chk2dplines and mct.polys is not None:
                self.plot_polylines()
            if chk2dplclean and mct.cleanpolys is not None:
                self.plot_polys_clean()
            if chk2dsli and mct.slices is not None:
                self.plot_slice()
            if chk2centr and mct.ctrds is not None:
                self.plot_centroids()
            if mct.temp_scatter is not None:
                self.plot2d.addItem(mct.temp_scatter)
            if mct.temp_roi_plot is not None:
                for roi in mct.temp_roi_plot:
                    self.plot2d.addItem(roi)
            try:
                self.plot2d.addItem(self.temp_rect)
                self.plot2d.addItem(self.line)
                self.plot2d.addItem(self.fill)
            except:
                pass
        except KeyError:
            print('Error in func main2dplot')
            # pass  # KeyError is raised when re-slicing. It shouldn't cause any problem

    def remove_points(self, plot, points):
        self.status = 1
        for p in points:
            mct.temp_points = np.delete(
                mct.temp_points, np.where(
                    np.logical_and(tuple(p.pos())[0] == mct.temp_points[:, 0],
                                   tuple(p.pos())[1] == mct.temp_points[:, 1])), 0)
            # print("clicked points", tuple(points[0].pos()))
        mct.temp_scatter.clear()
        mct.temp_scatter.addPoints(mct.temp_points[:, 0], mct.temp_points[:, 1])

    def remove_points_rect(self, event):
        ##### Guardare  ### if event.button() == QtCore.Qt.LeftButton:
        if self.status == 1:
            self.status = 0
            return
        elif self.status == 0:
            pos = event.scenePos()
            if self.counter == 0:
                self.first = self.plot2d.vb.mapSceneToView(pos)
                # print('First point: ', (self.first.x(), self.first.y()))
                self.counter = 1
            elif self.counter == 1:
                self.second = self.plot2d.vb.mapSceneToView(pos)
                # print('Second point: ', (self.second.x(), self.second.y()))
                toremove_x = np.logical_and(mct.temp_points[:, 0] >= min(self.first.x(), self.second.x()),
                                            mct.temp_points[:, 0] <= max(self.first.x(), self.second.x()))
                toremove_y = np.logical_and(mct.temp_points[:, 1] >= min(self.first.y(), self.second.y()),
                                            mct.temp_points[:, 1] <= max(self.first.y(), self.second.y()))
                toremove = np.where(np.logical_and(toremove_x, toremove_y))
                mct.temp_points = np.delete(mct.temp_points, toremove, 0)
                mct.temp_scatter.clear()
                mct.temp_scatter.addPoints(mct.temp_points[:, 0], mct.temp_points[:, 1])
                rectx = [mct.xmin, mct.xmin, mct.xmin, mct.xmin]
                recty = [mct.ymin, mct.ymin, mct.ymin, mct.ymin]
                self.temp_rect.setData(rectx, recty)
                linex = [mct.xmin, mct.xmin]
                liney = [mct.ymin, mct.ymin]
                self.line.setData(linex, liney)
                self.counter = 0
                self.first = None

    def draw_temp_rect(self, event):
        if self.first is not None and self.counter == 1:
            pos = event  # La posizione per sigMouseMoved è già in Scene Coordinates
            temp_second = self.plot2d.vb.mapSceneToView(pos)
            rectx = [self.first.x(), temp_second.x(), temp_second.x(), self.first.x()]
            recty = [self.first.y(), self.first.y(), temp_second.y(), temp_second.y()]
            self.temp_rect.setData(rectx, recty)
            linex = [self.first.x(), self.first.x()]
            liney = [self.first.y(), temp_second.y()]
            self.line.setData(linex, liney)

    def scatter_editMode(self, pointdict):
        self.main2dplot()
        z = mct.zcoords[self.combo_slices.currentIndex()]
        self.combo_slices.setEnabled(False)

        mct.temp_points = pointdict[z]

        if str(pointdict) == str(mct.slices):
            pcolor = pg.mkBrush(0, 0, 150, 255)
        elif str(pointdict) == str(mct.ctrds):
            pcolor = pg.mkBrush(150, 0, 0, 255)

        mct.temp_scatter = pg.ScatterPlotItem(
            pxMode=True,  # Set pxMode=False to allow spots to transform with the view
            size=13,
            brush=pcolor,
            hoverable=True,
            hoverPen=pg.mkPen('g', width=3),
            hoverSize=19
        )
        mct.temp_scatter.addPoints(mct.temp_points[:, 0], mct.temp_points[:, 1])
        self.plot2d.addItem(mct.temp_scatter)
        mct.temp_scatter.sigClicked.connect(self.remove_points)

        self.counter = 0
        self.first = None
        self.second = None
        self.status = 0
        self.temp_rect = pg.PlotCurveItem()
        self.line = pg.PlotCurveItem()
        rectx = [mct.xmin, mct.xmin, mct.xmin, mct.xmin]
        recty = [mct.ymin, mct.ymin, mct.ymin, mct.ymin]
        linex = [mct.xmin, mct.xmin]
        liney = [mct.ymin, mct.ymin]
        self.temp_rect.setData(rectx, recty)
        self.temp_rect.setPen((0, 0, 0))
        self.line.setData(linex, liney)
        self.line.setPen((0, 0, 0))
        self.plot2d.addItem(self.temp_rect)
        self.plot2d.addItem(self.line)
        self.fill = pg.FillBetweenItem(self.temp_rect, self.line, brush=pg.mkBrush(20, 200, 20, 50))
        self.plot2d.addItem(self.fill)

        ### # pg.SignalProxy(self.plot2d.scene().sigMouseClicked, rateLimit=0, delay=0.01, slot=self.remove_points_rect)
        ### # pg.SignalProxy(self.plot2d.scene().sigMouseMoved, rateLimit=60, delay=0.01, slot=self.draw_temp_rect)
        self.plot2d.scene().sigMouseClicked.connect(self.remove_points_rect)
        self.plot2d.scene().sigMouseMoved.connect(self.draw_temp_rect)

    def gui_edit_status(self, torf):
        self.btn_edit_slice.setEnabled(torf)
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
        # self.lineEdit_customslices.setEnabled(torf)
        if mct.slices is not None:
            self.lineEdit_wall_thick.setEnabled(torf)
        if mct.ctrds is not None:
            self.btn_edit_centroids.setEnabled(torf)
            self.btn_gen_polylines.setEnabled(torf)
        if mct.cleanpolys is not None:
            self.btn_edit_polylines.setEnabled(torf)
            self.btn_gen_polygons.setEnabled(torf)
        if mct.polygs is not None:
            self.btn_gen_mesh.setEnabled(torf)

    def edit_slice(self):
        self.btn_edit_finalize.setEnabled(True)
        self.btn_edit_discard.setEnabled(True)
        self.gui_edit_status(False)
        mct.editmode = 0
        self.scatter_editMode(mct.slices)

    def edit_centroids(self):
        self.btn_edit_finalize.setEnabled(True)
        self.btn_edit_discard.setEnabled(True)
        self.gui_edit_status(False)
        mct.editmode = 1
        self.scatter_editMode(mct.ctrds)

    def poly_rois(self):
        if mct.temp_roi_plot is not None:
            mct.temp_roi_plot.clear()
        mct.temp_roi_plot = []
        for poly in mct.temp_polylines:
            mct.temp_roi_plot += [pg.PolyLineROI(poly,
                                                 pen=pg.mkPen(color=(120, 120, 120, 255), width=2.5),
                                                 hoverPen=pg.mkPen(color=(30, 190, 255, 255), width=2.7),
                                                 handlePen=pg.mkPen('r'),
                                                 closed=False,
                                                 removable=True)]

    def remove_poly(self, roi):
        self.getRoiIndex(roi)
        roi.clearPoints()
        del mct.temp_polylines[mct.roiIndex]

    def add_polyline(self):
        x1 = mct.xmin - (mct.xmax - mct.xmin) / 10
        x2 = x1 - (mct.xmax - mct.xmin) / 5
        y1 = mct.ymin
        y2 = mct.ymin + (mct.ymax - mct.ymin) / 5
        newpoly = np.array([[x1, y1], [x2, y1], [x2, y2]])
        mct.temp_polylines += [newpoly]
        self.poly_rois()
        for roi in mct.temp_roi_plot:
            roi.sigRegionChangeFinished.connect(self.update_poly)
            roi.sigRemoveRequested.connect(self.remove_poly)
        self.main2dplot()

    def getRoiIndex(self, roi):
        for i in range(len(mct.temp_roi_plot)):
            if roi == mct.temp_roi_plot[i]:
                mct.roiIndex = i

    def update_poly(self, roi):
        try:
            self.getRoiIndex(roi)
            origin = roi.pos()
            handles = roi.getLocalHandlePositions()
            handlelist = []
            for handle in handles:
                try:
                    handlelist += [[handle[1][0] + origin[0], handle[1][1] + origin[1]]]
                except TypeError:  # A modified handle becomes a QPointF -> coords are extracted differently
                    handlelist += [[handle[1].x() + origin[0], handle[1].y() + origin[1]]]
            temp_poly = sg.LineString(handlelist)
            cleanpoly = temp_poly.simplify(0.025, preserve_topology=True)
            mct.temp_polylines[mct.roiIndex] = np.array(cleanpoly)
        except ValueError:  # Error raises when removing a roi through right click
            pass

    def edit_polylines(self):
        mct.editmode = 2
        self.main2dplot()
        self.btn_edit_finalize.setEnabled(True)
        self.btn_edit_discard.setEnabled(True)
        self.btn_add_polyline.setEnabled(True)
        self.combo_slices.setEnabled(False)
        self.gui_edit_status(False)
        z = mct.zcoords[self.combo_slices.currentIndex()]
        mct.temp_polylines = mct.cleanpolys[z].copy()
        self.poly_rois()
        self.main2dplot()
        for roi in mct.temp_roi_plot:
            roi.sigRegionChangeFinished.connect(self.update_poly)
            roi.sigRemoveRequested.connect(self.remove_poly)

    def discard_edit(self):
        if mct.editmode == 0 or mct.editmode == 1:
            self.plot2d.scene().sigMouseClicked.disconnect(self.remove_points_rect)
            self.plot2d.scene().sigMouseMoved.disconnect(self.draw_temp_rect)
        mct.editmode = None
        mct.temp_points = None
        mct.temp_scatter = None
        mct.temp_polylines = None
        mct.temp_roi_plot = None
        mct.roiIndex = None
        self.combo_slices.setEnabled(True)
        self.btn_edit_finalize.setEnabled(False)
        self.btn_edit_discard.setEnabled(False)
        self.btn_add_polyline.setEnabled(False)
        self.gui_edit_status(True)
        self.main2dplot()

    def finalize_edit(self):
        if mct.editmode == 0 or mct.editmode == 1:
            self.plot2d.scene().sigMouseClicked.disconnect(self.remove_points_rect)
            self.plot2d.scene().sigMouseMoved.disconnect(self.draw_temp_rect)
        z = mct.zcoords[self.combo_slices.currentIndex()]
        if mct.editmode == 0:
            mct.slices[z] = mct.temp_points
            self.status_centroids.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_polylines.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
        elif mct.editmode == 1:
            mct.ctrds[z] = mct.temp_points
            self.status_polylines.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
        elif mct.editmode == 2:
            gluetol = 0.03
            changes = 1
            restart = 0
            while changes == 1:
                npolys = len(mct.temp_polylines)
                print('len mct.temp_polylines: ', npolys)
                for i in range(npolys):
                    if restart == 1:
                        restart = 0
                        break
                    first = mct.temp_polylines[i]
                    for j in range(npolys):
                        if j == i:
                            continue
                        second = mct.temp_polylines[j]
                        if abs((first[-1, 0] - second[0, 0])) <= gluetol and abs(
                               (first[-1, 1] - second[0, 1])) <= gluetol:
                            print('testa coda')
                            glued = np.vstack((first, second))
                            updated = []
                            for k in range(npolys):
                                if k not in (i, j):
                                    updated += [mct.temp_polylines[k]]
                            mct.temp_polylines = updated
                            mct.temp_polylines += [glued]
                            restart = 1
                            break
                        elif abs((first[0, 0] - second[0, 0])) <= gluetol and abs(
                                (first[0, 1] - second[0, 1])) <= gluetol:
                            print('testa testa')
                            glued = np.vstack((np.flip(second, 0), first))

                            updated = []
                            for k in range(npolys):
                                if k not in (i, j):
                                    updated += [mct.temp_polylines[k]]
                            mct.temp_polylines = updated
                            mct.temp_polylines += [glued]
                            restart = 1
                            break
                        elif abs((first[-1, 0] - second[-1, 0])) <= gluetol and abs(
                                (first[-1, 1] - second[-1, 1])) <= gluetol:
                            print('coda coda')
                            glued = np.vstack((first, np.flip(second, 0)))
                            updated = []
                            for k in range(npolys):
                                if k not in (i, j):
                                    updated += [mct.temp_polylines[k]]
                            mct.temp_polylines = updated
                            mct.temp_polylines += [glued]
                            restart = 1
                            break
                checklen = len(mct.temp_polylines)
                if npolys == checklen:
                    changes = 0
                    print('finito')

            finalpolys = []
            for poly in mct.temp_polylines:
                rawpoly = sg.LineString(poly)
                cleanpoly = rawpoly.simplify(0.035, preserve_topology=True)
                finalpolys += [np.array(cleanpoly)]
            mct.cleanpolys[z] = finalpolys
            self.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
        mct.editmode = None
        mct.temp_points = None
        mct.temp_scatter = None
        mct.temp_polylines = None
        mct.temp_roi_plot = None
        mct.roiIndex = None
        self.combo_slices.setEnabled(True)
        self.btn_edit_finalize.setEnabled(False)
        self.btn_edit_discard.setEnabled(False)
        self.btn_add_polyline.setEnabled(False)
        self.gui_edit_status(True)
        self.main2dplot()

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


app = QApplication(sys.argv)
win = Window()
win.show()
sys.exit(app.exec_())
# app.exec_() ## altro metodo che sembra funzionare bene come sys.exit(app.exec_())
