# Matcap Maker v3

High-performance, layer-based Matcap texture generator using Python and OpenGL (PySide6).

## Project File Format Specification (.json)

Matcap Maker uses a JSON-based project format designed for forward and backward compatibility.

### Structure

```json
{
    "app_version": "3.0",
    "layers": [
        {
            "type": "LayerClassName",
            "enabled": true,
            "blend_mode": "Normal",
            "params": {
                "param_name": value,
                ...
            }
        },
        ...
    ]
}
```

### Compatibility Rules (Robustness)

1.  **Missing Parameters (Backward Compatibility)**
    *   If a parameter exists in the class code but is missing from the JSON (e.g., loading an old file into a newer version), the **class default value** defined in `__init__` is used.
    *   The loader will NOT error out.

2.  **Unknown Parameters (Forward Compatibility)**
    *   If a parameter exists in the JSON but not in the class code (e.g., loading a new file into an older version), the parameter is **ignored**.
    *   A warning may be logged, but the application will NOT crash.

3.  **Unknown Layer Types**
    *   If a layer type string in the JSON does not match any registered class in the current version, that layer is **skipped**.

## Development Setup

### Dependencies
*   Python 3.10+
*   PySide6
*   PyOpenGL
*   NumPy
*   Pillow
*   qt-material

### Environment
We recommend using `uv` for dependency management.

```bash
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -r requirements.txt
```

### Running
```bash
python -m src.main
```
