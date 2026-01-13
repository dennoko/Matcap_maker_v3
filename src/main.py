import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QSurfaceFormat
from qt_material import apply_stylesheet
from src.ui.main_window import MainWindow

def main():
    try:
        print("Initializing Application...")
        # High DPI scaling
        os.environ["QT_API"] = "pyside6"
        os.environ["QT_FONT_DPI"] = "96" 

        # Force OpenGL 3.3 Core Profile
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        QSurfaceFormat.setDefaultFormat(fmt)

        app = QApplication(sys.argv)
        print("QApplication created.")
        
        # Apply Material Theme
        apply_stylesheet(app, theme='dark_teal.xml')
        print("Theme applied.")

        window = MainWindow()
        window.show()
        print("Window shown. Entering event loop.")

        sys.exit(app.exec())
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
