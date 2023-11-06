import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from vispy import app, gloo
from vispy.util.transforms import perspective, translate
import numpy as np

# Create a simple cube geometry
vertices = np.array([
    [-0.5, -0.5, -0.5],
    [0.5, -0.5, -0.5],
    [0.5, 0.5, -0.5],
    [-0.5, 0.5, -0.5],
    [-0.5, -0.5, 0.5],
    [0.5, -0.5, 0.5],
    [0.5, 0.5, 0.5],
    [-0.5, 0.5, 0.5]
], dtype=np.float32)

indices = np.array([
    0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 5, 6, 2, 3, 7, 4
], dtype=np.uint32)

# Create the Vertex Shader
vertex_shader = """
#version 120

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

attribute vec3 position;
void main()
{
    gl_Position = projection * view * model * vec4(position, 1.0);
}
"""

# Create the Fragment Shader
fragment_shader = """
#version 120

void main()
{
    gl_FragColor = vec4(1.0, 1.0, 1.0, 1.0);
}
"""

class MyOpenGLWidget(QMainWindow):
    def __init__(self):
        super().__init__()

        self.canvas = app.Canvas(keys='interactive')
        self.canvas.show()
        self.setCentralWidget(self.canvas.native)

        self.program = gloo.Program(vertex_shader, fragment_shader)
        self.program['position'] = gloo.VertexBuffer(vertices)
        self.program['index'] = gloo.IndexBuffer(indices)

        self.view = np.eye(4, dtype=np.float32)
        self.model = np.eye(4, dtype=np.float32)
        self.projection = perspective(45.0, 800.0 / 600.0, 2.0, 10.0)

        self.program['model'] = self.model
        self.program['view'] = self.view
        self.program['projection'] = self.projection

        zoom_in_button = QPushButton("Zoom In")
        zoom_out_button = QPushButton("Zoom Out")

        zoom_in_button.clicked.connect(self.zoom_in)
        zoom_out_button.clicked.connect(self.zoom_out)

        layout = QVBoxLayout()
        layout.addWidget(zoom_in_button)
        layout.addWidget(zoom_out_button)
        widget = QWidget()
        widget.setLayout(layout)

        self.setMenuWidget(widget)

    def zoom_in(self):
        self.view = np.dot(translate((0, 0, 1)), self.view)
        self.update()

    def zoom_out(self):
        self.view = np.dot(translate((0, 0, -1)), self.view)
        self.update()

    def on_resize(self, event):
        gloo.set_viewport(0, 0, *event.physical_size)
        self.projection = perspective(45.0, *event.physical_size, 2.0, 10.0)
        self.program['projection'] = self.projection

    def on_draw(self, event):
        gloo.clear()
        self.program.draw('triangles')

app.use_app('PyQt5')
qapp = QApplication(sys.argv)
win = MyOpenGLWidget()
win.show()

if __name__ == '__main__':
    sys.exit(qapp.exec_())
