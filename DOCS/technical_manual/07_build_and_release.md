# 07. ビルドとリリース（バージョン管理・インストーラ）

Matcap Maker は **Inno Setup によるインストーラ** で配布します。このセクションでは、プログラムを更新したときの **バージョン管理** と **インストーラの再ビルド・更新** の手順をまとめます。

## 全体像

```
src/version.py (__version__)
        │  ← ここ1か所を更新するのが基本
        ├─→ build_exe.py     : exe のファイルプロパティ（製品名/バージョン）に反映
        └─→ build_installer.py : Inno Setup の AppVersion / 出力ファイル名に反映
                                  (/DAppVersion=<version> で .iss に注入)
```

成果物:
- `python build_exe.py` → `dist/MatcapMaker/`（onedir 形式の実行ファイル一式）
- `python build_installer.py` → `dist/installer/MatcapMaker-Setup-<version>.exe`（配布物）

## バージョン番号の体系

| 場所 | 変数 | 用途 | 更新するか |
|---|---|---|---|
| `src/version.py` | `__version__` | **配布物（exe / インストーラ）のバージョン** | リリース毎に更新 |
| `src/core/project_io.py` | `ProjectIO.APP_VERSION` | プロジェクト `.json` の `app_version` | **基本変更しない**（後方互換のため独立管理） |

- `__version__` は `"3.0.0"` のような **3桁（MAJOR.MINOR.PATCH）** を推奨。
  - exe のファイルバージョン（Windows のプロパティ）は内部的に4桁 `(3, 0, 0, 0)` へ自動変換されます（`build_exe.py` の `_version_tuple`）。
- `APP_VERSION`（プロジェクトファイル形式のバージョン）は、保存フォーマットの互換性を壊す変更をしない限り変えません。両者は **意図的に別管理** です。

### バージョンの上げ方の目安
- **PATCH**（例 3.0.0 → 3.0.1）: バグ修正のみ。
- **MINOR**（例 3.0.1 → 3.1.0）: 機能追加（後方互換あり）。
- **MAJOR**（例 3.1.0 → 4.0.0）: 大きな仕様変更。プロジェクトファイル形式に破壊的変更が入る場合は `APP_VERSION` の扱いも検討する。

## リリース手順（プログラム更新時）

1. **コードを更新**してコミットする。
2. **`src/version.py` の `__version__` を更新**する。これがバージョン管理の起点。
   ```python
   __version__ = "3.0.1"
   ```
3. **インストーラをビルド**する（onedir ビルド＋Inno Setup を一括実行）。
   ```powershell
   python build_installer.py
   ```
   → `dist/installer/MatcapMaker-Setup-3.0.1.exe` が生成される。
4. **動作確認**（下記「検証」参照）。
5. 生成された `MatcapMaker-Setup-<version>.exe` を配布する（GitHub Releases 等）。

> exe だけ作り直したい（インストーラ不要）場合は `python build_exe.py` のみ。

## インストーラの更新（既存ユーザーの上書きインストール）

`installer/MatcapMaker.iss` の `AppId`（GUID）が **同一である限り**、新しいバージョンのインストーラを実行すると **既存インストールを検出して更新** されます。

- `AppId` は **絶対に変更しない**（変更すると別アプリ扱いになり、旧版が残って二重インストールになる）。
- インストール先（`{autopf}\MatcapMaker`）やショートカット名を変えても、`AppId` が同じなら更新として扱われる。

### 旧バージョンの完全削除（クリーン更新）
`[InstallDelete]` セクションで、**新ファイルを展開する前に `{app}` 配下を一掃**してから入れ直すように設定済み。

```ini
[InstallDelete]
Type: filesandordirs; Name: "{app}\*"
```

- これにより、PyInstaller/PySide6 のバージョンアップで **依存DLLのファイル名が変わっても、古いファイルが取り残されない**。
- **ユーザーデータは削除されない**。設定・プロジェクト・出力はすべて `Documents\MatcapMaker\`（`config.json` / `projects/` / `output/`）、クラッシュログは `%LOCALAPPDATA%\MatcapMaker\` にあり、**`{app}` の外**にあるため `[InstallDelete]` の対象外。
- ⚠️ この前提を守るため、**`{app}`（インストール先）にユーザーデータを書き込むコードを追加しないこと**。設定類は必ず `Settings`（`src/core/settings.py`、`Documents\MatcapMaker`）経由にする。

### アイコンを変更したい場合
- `res/icon/icon.ico` を差し替えるだけで、以下すべてに反映される（コード変更不要）:
  - exe 埋め込みアイコン（`build_exe.py` の `--icon`）
  - 実行時のウィンドウ/タスクバーアイコン（`src/main.py` が `get_resource_path("res/icon/icon.ico")` を参照）
  - インストーラ自身のアイコン（`.iss` の `SetupIconFile`）
  - ショートカット／アンインストーラのアイコン（`.iss` の `IconFilename` / `UninstallDisplayIcon` が exe を指す）

## インストーラ設定を変えたいとき（`installer/MatcapMaker.iss`）

| やりたいこと | 編集箇所 |
|---|---|
| アプリ名・発行者 | `[Setup]` の `AppName` / `AppPublisher`（または冒頭の `#define`） |
| インストール先 | `DefaultDirName`（既定 `{autopf}\MatcapMaker`） |
| 管理者権限の要否 | `PrivilegesRequired`（`admin`＝Program Files、`lowest`＋`{userpf}`＝ユーザー領域） |
| 対応言語 | `[Languages]` |
| デスクトップショートカット | `[Tasks]` の `desktopicon`（既定は未チェック） |
| インストール後の自動起動 | `[Run]` |

## 前提・環境

- **Inno Setup 6** が必要（`ISCC.exe`）。未導入なら:
  ```powershell
  winget install JRSoftware.InnoSetup
  ```
  `build_installer.py` は `ISCC.exe` を PATH → `C:\Program Files (x86)\Inno Setup 6\` → `C:\Program Files\Inno Setup 6\` → `%LOCALAPPDATA%\Programs\Inno Setup 6\`（winget のユーザーインストール先）の順で自動探索する。
- 中間生成物（`build/`、`dist/`、生成される `*.spec` や `build/version_info.txt`）は `.gitignore` 対象。`installer/*.iss` と `src/version.py` は Git 管理対象。

## 検証（リリース前チェック）

1. `python build_installer.py` → `dist/installer/MatcapMaker-Setup-<version>.exe` が生成される。
2. 生成インストーラを実行 → ウィザードのアイコン表示・インストール完了を確認。
3. インストール先の `MatcapMaker.exe` を起動 → **ウィンドウ/タスクバーアイコン**が正しい。
4. スタートメニュー／デスクトップショートカットの**アイコン**が正しい。
5. 「アプリと機能」で**表示アイコン・バージョン**が正しい、アンインストール成功。
6. クラッシュ時のログが `%LOCALAPPDATA%\MatcapMaker\matcap_error.log` に書ける（インストール先は読み取り専用）。
7. **上書き更新の確認**: 旧バージョンをインストール済みの状態で新バージョンを実行 → 二重インストールにならず更新される（`AppId` 同一）。

## 関連ファイル

- `src/version.py` — 配布バージョンの単一ソース
- `build_exe.py` — PyInstaller（onedir）ビルド、exe バージョン情報生成
- `build_installer.py` — onedir ビルド → Inno Setup コンパイルの一括スクリプト
- `installer/MatcapMaker.iss` — Inno Setup スクリプト
- `src/main.py` — 実行時アイコン設定、クラッシュログ出力先
