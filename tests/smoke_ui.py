"""UI smoke test: boots MainWindow, selects every layer, adds every layer type."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QSurfaceFormat

import src.main as m
m.setup_exception_hook()

fmt = QSurfaceFormat()
fmt.setVersion(3, 3)
fmt.setProfile(QSurfaceFormat.CoreProfile)
QSurfaceFormat.setDefaultFormat(fmt)

app = QApplication(sys.argv)

from src.ui.main_window import MainWindow
win = MainWindow()
win.show()

state = {"step": 0}

def step():
    s = state["step"]
    state["step"] += 1
    try:
        if s == 0:
            # Select each layer -> rebuilds the properties panel
            for i in range(win.layer_list.list_widget.count()):
                win.layer_list.list_widget.setCurrentRow(i)
                app.processEvents()
            print("properties panel OK for", win.layer_list.list_widget.count(), "layers")
        elif s == 1:
            # Add one of each layer type via the UI path
            for t in ["spot", "fresnel", "noise", "image", "adjustment", "gradient"]:
                win.on_add_layer(t)
                app.processEvents()
            print("added all layer types, stack size:", len(win.preview.layer_stack))
        elif s == 2:
            for i in range(win.layer_list.list_widget.count()):
                win.layer_list.list_widget.setCurrentRow(i)
                app.processEvents()
            print("properties panel OK after adds")
        else:
            print("SMOKE TEST OK")
            app.quit()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("SMOKE TEST FAILED:", e)
        app.exit(1)

timer = QTimer()
timer.timeout.connect(step)
timer.start(400)
sys.exit(app.exec())
