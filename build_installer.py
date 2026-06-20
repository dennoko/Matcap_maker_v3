"""Matcap Maker のインストーラをワンコマンドで生成する。

手順:
  1. dist/MatcapMaker をクリーン
  2. build_exe.py を実行して onedir 形式の exe 一式を生成
  3. Inno Setup コンパイラ (ISCC.exe) で installer/MatcapMaker.iss をビルド

成果物: dist/installer/MatcapMaker-Setup-<version>.exe

前提: Inno Setup 6 がインストール済みであること
  (未導入なら: winget install JRSoftware.InnoSetup)
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.version import __version__

ISS_PATH = ROOT / "installer" / "MatcapMaker.iss"
ONEDIR_OUT = ROOT / "dist" / "MatcapMaker"


def find_iscc() -> str | None:
    """ISCC.exe を PATH → 既定インストール先の順で探す。"""
    found = shutil.which("ISCC")
    if found:
        return found
    candidates = [
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
    ]
    # winget's per-user install location
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        candidates.append(Path(local_appdata) / "Programs" / "Inno Setup 6" / "ISCC.exe")
    for c in candidates:
        if c.exists():
            return str(c)
    return None


def main() -> int:
    iscc = find_iscc()
    if not iscc:
        print(
            "ISCC.exe (Inno Setup compiler) が見つかりません。\n"
            "Inno Setup 6 をインストールしてください:\n"
            "  winget install JRSoftware.InnoSetup",
            file=sys.stderr,
        )
        return 1

    # 1. clean onedir output
    if ONEDIR_OUT.exists():
        print(f"Cleaning {ONEDIR_OUT} ...")
        shutil.rmtree(ONEDIR_OUT)

    # 2. build the onedir exe
    print("Building onedir exe via build_exe.py ...")
    import build_exe
    rc = build_exe.main()
    if rc != 0:
        print("build_exe.py failed.", file=sys.stderr)
        return rc
    if not (ONEDIR_OUT / "MatcapMaker.exe").exists():
        print(f"Expected {ONEDIR_OUT / 'MatcapMaker.exe'} not found.", file=sys.stderr)
        return 1

    # 3. compile the installer
    print(f"Compiling installer with {iscc} ...")
    rc = subprocess.call([iscc, f"/DAppVersion={__version__}", str(ISS_PATH)])
    if rc != 0:
        print("Inno Setup compilation failed.", file=sys.stderr)
        return rc

    out = ROOT / "dist" / "installer" / f"MatcapMaker-Setup-{__version__}.exe"
    print(f"\nDone. Installer: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
