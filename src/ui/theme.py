from qt_material import apply_stylesheet

def apply_app_theme(app):
    """
    Applies the application theme using qt_material.
    """
    # Using 'dark_teal.xml' as the default theme
    # We can extend this to load from a config or allow switching later.
    try:
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
    except Exception as e:
        print(f"Failed to apply theme: {e}")
