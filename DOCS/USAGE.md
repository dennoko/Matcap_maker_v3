# Matcap Maker Usage Guide

Matcap Maker is a tool for creating Matcap (Material Capture) textures for 3D models.
By layering multiple effects (lights, fresnel, noise, images, etc.), you can intuitively create original Matcaps.

## Interface Overview

The application is divided into three main areas:

1.  **Preview Window (Center)**
    *   Displays a real-time rendering of your Matcap on a sphere.
    *   Use the "Export Image" button at the bottom to save the current result as an image file (PNG/JPG).
2.  **Layer List (Left)**
    *   Lists all layers currently in the project.
    *   Processing occurs from top to bottom.
    *   **Add**: Create a new layer using the "Add Layer" button.
    *   **Remove**: Delete the currently selected layer.
    *   **Toggle Visibility**: Click the circular button next to each item to enable/disable the layer.
    *   **Reorder**: Drag and drop layers to change their order.
    *   **Context Menu**: Right-click on a layer to access "Duplicate" or "Delete" options.
3.  **Properties Panel (Right)**
    *   Adjust detailed settings for the layer selected in the list.

## Layer Types and Properties

### 1. Base Layer
Sets the foundation color and preview settings for the Matcap.

*   **Color**: Sets the base color.
*   **Preview Options**:
    *   **Mode**:
        *   `Standard`: Standard sphere preview.
        *   `With Normal Map`: Previews how the Matcap looks with a normal map applied.
    *   **Normal Map**: Select a normal map image to load.
    *   **Strength/Scale/Offset**: Adjust the application of the normal map.

### 2. Spot Light
Adds lighting effects from a specific direction. Ideal for creating highlights.

*   **Blend Mode**: Select how the light blends (Add, Screen, Overlay, etc.).
*   **Intensity**: The brightness of the light.
*   **Range**: The spread of the light.
*   **Blur**: The softness of the light edges.
*   **Scale X/Y**: Changes the aspect ratio of the light shape.
*   **Rotation**: Rotates the light shape.
*   **Direction X/Y/Z**: Sets the direction the light is coming from.
*   **Color**: The color of the light.

### 3. Fresnel / Rim
Adds light to the contours (edges) of the object. Used for rim lights and material definition.

*   **Intensity**: The brightness of the light.
*   **Power**: The sharpness of the rim. Higher values push the light closer to the edge.
*   **Bias**: Offsets the range of the effect.
*   **Color**: The color of the light.

### 4. Noise
Adds overall grain or texture.

*   **Intensity**: The strength of the noise.
*   **Scale**: The fineness of the noise grain.
*   **Seed Offset**: Changes the random seed for the noise pattern.
*   **Color**: The color of the noise. Usually used with "Multiply" blend mode for shading.

### 5. Image
Maps an arbitrary image as a texture. Used for reflections or patterns.

*   **Image**: Select the image file to use.
*   **Mapping**:
    *   `UV`: Maps the image according to the sphere's UV coordinates.
    *   `Planar`: Maps the image like a planar projection.
*   **Offset X/Y**: Adjusts the position of the image.
*   **Scale**: Adjusts the size of the image.
*   **Rotation**: Adjusts the angle of the image.
*   **Blur**: Blurs the image.
*   **Opacity**: Adjusts the transparency of the image.

### 6. Color Adjustment
Adjusts the overall tone of the composite result up to this layer.

*   **Hue**: Adjusts the hue.
*   **Saturation**: Adjusts the color intensity.
*   **Brightness**: Adjusts the brightness.
*   **Contrast**: Adjusts the contrast.

## Menu Operations

### File
*   **Open Project**: Opens a saved project file (.json).
*   **Save Project**: Saves the current state as a project. Used image assets are also copied to an `assets` folder.
*   **Export Image**: Exports the Matcap image, same as the button at the bottom.

### Options
*   **Language**: Switches language between English and Japanese (Release requires restart).
*   **Resolution**: Selects the export resolution (64x64 to 4096x4096).
*   **Padding**: Sets the margin for the exported image.

### Help
*   **Third Party Notices**: Displays legal notices for libraries used.
