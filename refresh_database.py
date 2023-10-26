
def refresh_database(global_mct):
    global_mct.filepath=None  
    global_mct.pcl=None  
    global_mct.npts=None  
    global_mct.zmin=None  
    global_mct.zmax=None 
    global_mct.xmin=None  
    global_mct.xmax=None  
    global_mct.ymin=None  
    global_mct.ymax=None  
    global_mct.zcoords=None 
    global_mct.slices=None  
    global_mct.netpcl=None  
    global_mct.ctrds=None  
    global_mct.polys=None  
    global_mct.cleanpolys=None 
    global_mct.polygs=None  
    global_mct.xngrid=None  
    global_mct.xelgrid=None  
    global_mct.yngrid=None  
    global_mct.yelgrid=None 
    global_mct.elemlist=None  
    global_mct.nodelist=None  
    global_mct.elconnect=None  
    global_mct.temp_points=None 
    global_mct.temp_scatter=None  
    global_mct.temp_polylines=None  
    global_mct.temp_roi_plot=None 
    global_mct.editmode=None  
    global_mct.roiIndex=None
    global_mct.minwthick = None
    global_mct.slice_thick = None
    return global_mct