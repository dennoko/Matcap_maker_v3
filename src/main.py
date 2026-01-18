import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QSurfaceFormat, QIcon
from src.ui.main_window import MainWindow
from src.ui.theme import apply_app_theme
from src.core.utils import get_resource_path
import src.layers # Register layers


# Global Exception Hook to capture silent crashes in Noconsole mode
def setup_exception_hook():
    def exception_hook(exctype, value, traceback_obj):
        import traceback
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_msg = f"[{timestamp}] CRITICAL ERROR:\n"
        error_msg += "".join(traceback.format_exception(exctype, value, traceback_obj))
        
        # Write to log file in executable directory (or temp if not writable)
        # In frozen mode, sys.executable is the exe path.
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__)) # src/
            
        log_path = os.path.join(base_dir, "matcap_error.log")
        
        try:
            with open(log_path, "a") as f:
                f.write(error_msg + "\n" + "-"*50 + "\n")
        except Exception:
            pass # Last resort
            
        # Call original hook
        sys.__excepthook__(exctype, value, traceback_obj)
        
    sys.excepthook = exception_hook

def main():
    setup_exception_hook() # Enable logging
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
        
        # Set Icon
        icon_path = get_resource_path("res/icon/icon.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon not found at {icon_path}")

        print("QApplication created.")
        
        # Apply Theme
        apply_app_theme(app)
        
        # Create Main Window
        window = MainWindow()
        window.show()
        
        print("Window shown. Entering event loop.")
        sys.exit(app.exec())
        
    except Exception as e:
        import traceback
        # Capture main loop errors via hook if possible, or manual write
        sys.excepthook(type(e), e, e.__traceback__)
        print(f"CRITICAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
