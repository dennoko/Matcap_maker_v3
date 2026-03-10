import os
import sys
from pathlib import Path


def main():
    try:
        import PyInstaller.__main__
    except ModuleNotFoundError:
        print(
            "PyInstaller is not installed in the active Python environment. "
            "Install it with 'pip install PyInstaller' and run this script again.",
            file=sys.stderr,
        )
        return 1

    root_dir = Path(__file__).resolve().parent
    entry_script = root_dir / "src" / "main.py"
    icon_path = root_dir / "res" / "icon" / "icon.ico"
    shaders_dir = root_dir / "src" / "shaders"
    resources_dir = root_dir / "res"
    license_dir = root_dir / "LICENSE"

    sep = ';' if os.name == 'nt' else ':'

    PyInstaller.__main__.run([
        str(entry_script),
        '--name=MatcapMaker',
        '--onefile',
        '--noconsole',
        f'--icon={icon_path}',
        f'--distpath={root_dir / "dist"}',
        f'--workpath={root_dir / "build"}',
        f'--specpath={root_dir}',
        f'--add-data={shaders_dir}{sep}src/shaders',
        f'--add-data={resources_dir}{sep}res',
        f'--add-data={license_dir}{sep}LICENSE',
    ])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
