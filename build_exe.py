import PyInstaller.__main__
import os

if __name__ == '__main__':
    # Determine separator for add-data (Windows: ';', Unix: ':')
    sep = ';' if os.name == 'nt' else ':'
    
    PyInstaller.__main__.run([
        'src/main.py',
        '--name=MatcapMaker_v3',
        '--onefile',
        '--noconsole',
        '--icon=res/icon/icon.ico',
        # Include Shaders
        f'--add-data=src/shaders{sep}src/shaders',
        # Include Resources (Icon, Texture, etc.)
        f'--add-data=res{sep}res',
        # Include License
        f'--add-data=LICENSE{sep}LICENSE',
        #'--windowed', # Implicit with --noconsole
    ])
