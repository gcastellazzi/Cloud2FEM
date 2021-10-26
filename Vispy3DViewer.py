import numpy as np
import vispy.app
import vispy.scene
from vispy.scene import visuals

class Visp3dplot():
    """ Class that handles all the 3DViewer graphics.
    The view is defined into the __init__ method, while
    other ad-hoc methods are used to add items to it.
    """
    def __init__(self, resolution):
        self.resolution = resolution
        self.canvas = vispy.scene.SceneCanvas(title='3D Viewer', keys='interactive', show=True, bgcolor='white')
        self.view3d = self.canvas.central_widget.add_view()

    def print_cloud(self, plotdata, alpha):
        """ :param plotdata: 3-columns np array (mct.pcl or mct.netpcl)
        """
        self.scatter = visuals.Markers()
        if self.resolution == 1:
            self.pcl3dplotdata = plotdata
        else:
            self.npts_sub = int(round(self.resolution * plotdata.shape[0]))
            self.randpts = np.random.choice(plotdata.shape[0], size=self.npts_sub, replace=False)
            self.pcl3dplotdata = plotdata[self.randpts]
        self.scatter.set_data(self.pcl3dplotdata, symbol='disc',
                              face_color=(255 / 255, 255 / 255, 255 / 255, alpha), size=1.0)   ################### default size = 2.7
        self.view3d.add(self.scatter)

    def print_slices(self, mct):
        try:
            self.slices = visuals.Markers()
            self.sliceplot = mct.slices[mct.zslices[0]]
            for i in mct.zslices[1:]:
                self.sliceplot = np.vstack((self.sliceplot, mct.slices[i]))
            self.slices.set_data(self.sliceplot, symbol='disc',
                                 face_color=(0 / 255, 0 / 255, 255 / 255, 1), size=4.3)
            self.view3d.add(self.slices)
        except TypeError:
            print("Error in Visp3dplot.print_slices(): generate the slices first")

    def print_centr(self, mct):
        self.centroids = visuals.Markers()
        self.centrplot = mct.ctrds[mct.zslices[0]]
        for i in mct.zslices[1:]:
            self.centrplot = np.vstack((self.centrplot, mct.ctrds[i]))
        self.centroids.set_data(self.centrplot, symbol='disc',
                             face_color=(255 / 255, 0 / 255, 0 / 255, 1), size=7)
        self.view3d.add(self.centroids)

    def print_polylines(self, mct):
        xyzplines = []
        for z in mct.zslices:
            for poly in mct.cleanpolys[z]:
                zcolumn = np.zeros((poly.shape[0], 1)) + z
                xyzplines += [np.hstack((poly, zcolumn))]

        plotitems = []
        for i in range(len(xyzplines)):
            plotitems += [visuals.Line()]
            plotitems[i].set_data(xyzplines[i], color=(0.05, 0.05, 1, 1), width=1)
            self.view3d.add(plotitems[i])

        vertices = xyzplines[0]
        for poly in xyzplines[1:]:
            vertices = np.vstack((vertices, poly))
        self.vertices = visuals.Markers()
        self.vertices.set_data(vertices, symbol='square',
                                face_color=(220 / 255, 30 / 255, 30 / 255, 1), size=2.7)
        self.view3d.add(self.vertices)


    def print_mesh(self, mct):  # Metodo provvisiorio
        # mct.nodelist,  row[i] = [nodeID, x, y, z]
        # mct.elconnect, row[i] = [edelmID, nID1, nID2, nID3, nID4, nID5, nID6, nID7, nID8]

        faces = []
        for i in range(len(mct.elconnect)):
            n1 = mct.nodelist[np.where(mct.elconnect[i, 1] == mct.nodelist[:, 0])][0][1:]
            n2 = mct.nodelist[np.where(mct.elconnect[i, 2] == mct.nodelist[:, 0])][0][1:].tolist()
            n3 = mct.nodelist[np.where(mct.elconnect[i, 3] == mct.nodelist[:, 0])][0][1:].tolist()
            n4 = mct.nodelist[np.where(mct.elconnect[i, 4] == mct.nodelist[:, 0])][0][1:].tolist()
            n5 = mct.nodelist[np.where(mct.elconnect[i, 5] == mct.nodelist[:, 0])][0][1:].tolist()
            n6 = mct.nodelist[np.where(mct.elconnect[i, 6] == mct.nodelist[:, 0])][0][1:].tolist()
            n7 = mct.nodelist[np.where(mct.elconnect[i, 7] == mct.nodelist[:, 0])][0][1:].tolist()
            n8 = mct.nodelist[np.where(mct.elconnect[i, 8] == mct.nodelist[:, 0])][0][1:].tolist()


            faces += [np.array([n1, n2, n3, n4])]
            faces += [np.array([n5, n6, n7, n8])]
            faces += [np.array([n5, n1, n2, n6])]
            faces += [np.array([n6, n2, n3, n7])]
            faces += [np.array([n7, n3, n4, n8])]
            faces += [np.array([n8, n4, n1, n5])]

        #     if i == 1:
        #         print(faces)
        # #
        # face1 = np.array([[1, 0., 0], [2, 0, 0], [3, 4., 0], [1, 4, 0]])
        # face2 = face1 * 3
        # face3 = face1 * 6
        # faces = [face1, face2, face3]
        # print('face inventata shape: ', faces[1].shape)

        # # print('faces: ', faces)
        # print('len faces: ', len(faces))
        # print('face1:', faces[1])
        # print('type face 1[0]:', type(faces[1][0][0]))
        #
        # faceplot = []
        # for j in range(len(faces)):
        #     faceplot += [visuals.Polygon(color=(1, 1, 1, 1))]
        #
        # for j in range(len(faceplot)):
        #     faceplot[j].pos = faces[j]
        #     self.view3d.add(faceplot[j])
        #
        #
        # # GENERAZIONE ARRAY DI NODI
        nodes = np.array([0, 0, 0]) # Riga in più da togliere
        for face in faces:
            for node in face:
                nodes = np.vstack((nodes, node))

        # LINEE STACCATE
        # plotitems = []
        # for i in range(int(len(faces))):
        #     if i < 5200:
        #         continue
        #     plotitems += [visuals.Line()]
        #     plotitems[i].set_data(faces[i], color=(0.05, 0.05, 1, 1), width=1)
        #     self.view3d.add(plotitems[i])



        # LINEE ATTACCATE
        self.lines = visuals.Line()
        self.lines.set_data(nodes[1:], color=(0.1, 0.3, 0.7, 1), width=1)
        self.view3d.add(self.lines)

        # PUNTI
        self.nodes = visuals.Markers()
        self.nodes.set_data(nodes, symbol='square',
                               face_color=(220 / 255, 30 / 255, 30 / 255, 1), size=3.5)
        self.view3d.add(self.nodes)



        # SINGOLO POLIGONO FUNZIONA
        # faceplot = visuals.Polygon(pos=faces[1], color=(1, 1, 1, 1))
        # self.view3d.add(faceplot)

        # SINGOLO POLIGONO TEST
        # polyg1 = np.array([[1, 0, 0], [2, 0, 0], [3, 4, 0], [1, 4, 0]])
        # plotpolyg = visuals.Polygon(pos=polyg1, color=(1, 1, 1, 1))
        # view.add(plotpolyg)

    def final3dsetup(self):
        self.view3d.camera = 'turntable'  # 'turntable'  # or 'arcball'
        axis = visuals.XYZAxis(parent=self.view3d.scene)
        # vispy.app.run()
        

