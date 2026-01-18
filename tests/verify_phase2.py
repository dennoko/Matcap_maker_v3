import sys
import os

# Ensure src in path
sys.path.append(os.getcwd())

from PySide6.QtWidgets import QApplication
from PySide6.QtOpenGL import QOpenGLWindow
from PySide6.QtGui import QSurfaceFormat
from src.core.engine import Engine

# Force GL 3.3 Core
fmt = QSurfaceFormat()
fmt.setVersion(3, 3)
fmt.setProfile(QSurfaceFormat.CoreProfile)
QSurfaceFormat.setDefaultFormat(fmt)

app = QApplication(sys.argv)
print("QApplication created.")

class TestWindow(QOpenGLWindow):
    def initializeGL(self):
        print("GL Init started...")
        try:
            # Create Engine
            engine = Engine(512, 512)
            print("Engine instantiated.")
            
            # Initialize (creates Compositor, Shaders, FBOs)
            engine.initialize()
            print("Engine initialized successfully via Compositor.")
            
            # Try resize
            engine.resize(256, 256)
            print("Resize successful.")
            
        except Exception as e:
            print(f"FAIL: Exception during Engine init: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
            
        print("PASS: Phase 2 Verification Successful.")
        self.close()
        sys.exit(0)

w = TestWindow()
w.resize(100, 100)
w.show()

sys.exit(app.exec())
