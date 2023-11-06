import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QOpenGLWidget, QPushButton, QVBoxLayout, QWidget
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *  # Import GLU for perspective calculation
from math import tan, radians

class MyOpenGLWidget(QOpenGLWidget):
    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        self.zoom_factor = 1.0  # Initial zoom factor

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        self.setup_perspective(width, height)
        glMatrixMode(GL_MODELVIEW)

    def setup_perspective(self, width, height):
        aspect_ratio = width / height
        fov = 45.0  # Field of view
        near_clip = 0.1
        far_clip = 100.0

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(fov, aspect_ratio, near_clip, far_clip)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        self.draw_rectangle(1.0, 1.0, 1.0)
        self.draw_scatter_of_points()

    def draw_rectangle(self, width, height, depth):
        glBegin(GL_QUADS)
        glVertex3f(-width / 2, -height / 2, -depth / 2)
        glVertex3f(width / 2, -height / 2, -depth / 2)
        glVertex3f(width / 2, height / 2, -depth / 2)
        glVertex3f(-width / 2, height / 2, -depth / 2)
        glEnd()

    def draw_scatter_of_points(self):
        glColor3f(1.0, 1.0, 1.0)  # Set point color to white
        glPointSize(5.0)  # Set point size

        glBegin(GL_POINTS)
        for x in range(-5, 6):
            for y in range(-5, 6):
                for z in range(-5, 6):
                    glVertex3f(x * 0.2, y * 0.2, z * 0.2)
        glEnd()

    def zoom_in(self):
        self.zoom_factor *= 1.2  # Adjust zoom factor for zooming in
        self.update()  # Trigger a repaint

    def zoom_out(self):
        self.zoom_factor /= 1.2  # Adjust zoom factor for zooming out
        self.update()  # Trigger a repaint

    def fit_to_object(self):
        # Calculate the zoom factor to fit the object on the screen
        # Modify this calculation based on your object's size and position
        object_size = 1.0  # Adjust this value according to the size of your object
        self.zoom_factor = 1.0 / object_size
        self.update()  # Trigger a repaint

def create_3d_window():
    app = QApplication(sys.argv)
    window = QMainWindow()
    gl_widget = MyOpenGLWidget()
    window.setCentralWidget(gl_widget)
    window.setGeometry(100, 100, 800, 600)

    # Create zoom in, zoom out, and fit to object buttons
    zoom_in_button = QPushButton("Zoom In")
    zoom_out_button = QPushButton("Zoom Out")
    fit_to_object_button = QPushButton("Fit to Object")

    # Connect button clicks to zoom functions
    zoom_in_button.clicked.connect(gl_widget.zoom_in)
    zoom_out_button.clicked.connect(gl_widget.zoom_out)
    fit_to_object_button.clicked.connect(gl_widget.fit_to_object)

    # Create a layout to arrange the buttons
    layout = QVBoxLayout()
    layout.addWidget(zoom_in_button)
    layout.addWidget(zoom_out_button)
    layout.addWidget(fit_to_object_button)

    # Create a widget to hold the layout with buttons
    control_widget = QWidget()
    control_widget.setLayout(layout)

    # Add the control widget to the main window
    window.setMenuWidget(control_widget)

    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    create_3d_window()
