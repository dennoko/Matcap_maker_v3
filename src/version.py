"""配布物（exe / インストーラ）のバージョン定義。

ここを更新すると build_exe.py（exe のファイルプロパティ）と
build_installer.py 経由の Inno Setup（AppVersion / 出力ファイル名）に反映される。

注意: プロジェクト .json の `app_version`（ProjectIO.APP_VERSION）は
後方互換のため別管理であり、この値とは独立している。
"""

__version__ = "3.0.0"
