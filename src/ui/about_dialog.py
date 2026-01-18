from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel
from PySide6.QtCore import Qt
import os

from src.core.i18n import tr
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("menu.help.about"))
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("<h3>Matcap Maker v3 uses the following third-party software:</h3>")
        header.setTextFormat(Qt.RichText)
        layout.addWidget(header)
        
        # Content
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        
        # Load License File
        self.load_license_content()
        
        # Close Button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
    def load_license_content(self):
        # Resolve path relative to project root
        # Assuming run from root
        # If strict: get path relative to this file
        # this file: src/ui/about_dialog.py
        # root: ../../
        
        from src.core.utils import get_resource_path
        license_path = get_resource_path("LICENSE/ThirdPartyNotices.md")
        
        if os.path.exists(license_path):
            with open(license_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.text_edit.setMarkdown(content)
        else:
            self.text_edit.setText(f"License file not found at: {license_path}")
