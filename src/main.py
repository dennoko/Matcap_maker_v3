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
        
        # Override highlights to be less bright (User Request)
        # Replacing bright primary highlight with subtle white overlay
        custom_css = """
        QListWidget::item:hover, QMenu::item:selected {
            background-color: rgba(255, 255, 255, 30);
            color: white;
        }
        QListWidget::item:selected:hover {
            background-color: rgba(255, 255, 255, 40);
        }
        """
        app.setStyleSheet(app.styleSheet() + custom_css)
        print("Theme applied with custom highlights.")

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
