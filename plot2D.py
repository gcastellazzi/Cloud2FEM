###############################################################################
# This module contains the functions needed to plot in pyqtgraph and
# to interact with the plotted entities
#
# WORK IN PROGRESS!!!!
###############################################################################

import numpy as np
import pyqtgraph as pg



def plot_grid(PlotItem, xdim, ydim, xmin, xmax, ymin, ymax):
    """
    Plots a grid whose space between lines is given by xdim and ydim,
    the other quantities define the extension of the grid.
    An example of PlotItem is:
    a = GraphicsLayoutWidget (from pyqtgraph)
    PlotItem = a.addPlot()
    """
    xngrid = np.arange(xmin - xdim, xmax + 2 * xdim, xdim)
    yngrid = np.arange(ymin - ydim, ymax + 2 * ydim, ydim)
    penna = pg.mkPen(color=(220, 220, 220, 255), width=1.5)
    for x in xngrid:
        PlotItem.plot((x, x), (min(yngrid), max(yngrid)), pen=penna)
    for y in yngrid:
        PlotItem.plot((min(xngrid), max(xngrid)), (y, y), pen=penna)
        


def plot_scatter(PlotItem, points, sz=5, clr=(0, 0, 0, 255)):
    """
    points : np.array([[x1, y1], [x2, y2], ..., [xn, yn]])
    sz     : size of the points
    clr    : color (r, g, b, alpha)
    Plot points on the PlotItem.
    """
    scatter2d = pg.ScatterPlotItem(pos=points, size=sz, brush=pg.mkBrush(clr))
    PlotItem.addItem(scatter2d)



def plot_polylines(PlotItem, polylines, wd=3, clr=(50, 50, 50, 255), rainbow=False, points=False):
    """
    wd         : width of the points
    clr        : color (r, g, b, alpha)
    polylines  : list [poly1, poly2,...., ]  
                 where polyn=np.array([[x1, y1], [x2, y2], ...,[xn, yn]])
    Plot list of polylines on the PlotItem
    """
    for poly in polylines:
        if rainbow == False:
            PlotItem.plot(poly[:, : 2], pen=pg.mkPen(color=clr, width=wd))
        elif rainbow == True:
            colr = np.random.randint(50, 255)
            colg = np.random.randint(50, 255)
            colb = np.random.randint(50, 255)
            PlotItem.plot(poly[:, : 2], pen=pg.mkPen(color=(colr, colg, colb, 255), width=wd))
        if points == True:
            pts = pg.ScatterPlotItem(pos=poly[:, : 2], size=9, brush=pg.mkBrush(255, 0, 0, 255), symbol='s')
            PlotItem.addItem(pts)



class RemovePointsClick:
    """
    Class that handles data and signals to remove points by clicking on them.
    See example 1 at the bottom of this module.
    """
    def __init__(self, pts_b, PlotItem, verbose=False):
        self.pts_b = pts_b       # np array of points before (_b) the click event
        self.PlotItem = PlotItem # pyqtgraph plot item
        self.verbose = verbose   # If True, plots the emptying pts_b at every click
        
    def remove_points(self, plot, points, ev):
        """
        plot, points and ev are automatically assigned when the function is 
        called from a signal_connect like sigClicked.connect(remove_points)
        points       : list of points that have been clicked
        This function removes the clicked points from a given array pts_b
        """
        for p in points:
            x_p = tuple(p.pos())[0]  # x coord of the clicked point
            y_p = tuple(p.pos())[1]  # y coord of the clicked point
            self.pts_b = np.delete(self.pts_b, np.where(np.logical_and(x_p == self.pts_b[:, 0], y_p == self.pts_b[:, 1])), 0)
            if self.verbose:
                print("Remaining points:\n", self.pts_b)
        self.ScatterItem.clear()
        self.ScatterItem.addPoints(self.pts_b[:, 0], self.pts_b[:, 1])
        
    def start(self):
        """
        When called, this function first creates a ScatterItem with the points
        at the initial state, then adds the ScatterItem to the PlotItem and
        finally connects the "signal emitted when a point is clicked" to the
        function remove_points()
        """
        self.ScatterItem = pg.ScatterPlotItem(
            pxMode=True,
            size=20,
            hoverable=True,
            hoverPen=pg.mkPen('g', width=3),
            hoverSize=30)
        self.ScatterItem.addPoints(self.pts_b[:, 0], self.pts_b[:, 1])
        self.PlotItem.addItem(self.ScatterItem)
        self.ScatterItem.sigClicked.connect(self.remove_points)
    
    def stop(self):
        """ If called, this function disables the removal of points"""
        self.ScatterItem.sigClicked.disconnect(self.remove_points)
    
    

##############################################################################
##################################################################### EXAMPLES
##############################################################################    
if __name__ == "__main__":
    # Choose which mouse interaction example you want to see!
    # 1: Remove points with a click or with a rectangular selection
    # 2: To do...
    # 3: To do...
    # 4: To do...
    # 5: To do...
    example = 1
    
    from pyqtgraph.Qt import QtGui

    app = QtGui.QApplication([])
    view = pg.GraphicsLayoutWidget(show=True)
    view.setBackground((50, 50, 50))
    plot = view.addPlot()
    plot.setAspectLocked(True)
    
    points = np.array([[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [2, 2]]) * 10
    
    if example == 1:       
        ciao = RemovePointsClick(points, plot, verbose=True)
        ciao.start()
        
    elif example == 2:
        pass
    elif example == 3:
        pass
    elif example == 4:
        pass
    elif example == 5:
        pass
    
    
    QtGui.QApplication.instance().exec_()
    
    
    
    
    
    
    
    
    
    
    
    