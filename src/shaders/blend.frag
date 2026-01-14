#version 330 core
out vec4 FragColor;
in vec2 TexCoords;

uniform sampler2D uSrc; // The current layer (Foreground)
uniform sampler2D uDst; // The accumulated background (Background)
uniform int uMode;      // Blend Mode
uniform float uOpacity; // Layer Opacity

// Blend Modes
#define MODE_NORMAL 0
#define MODE_ADD 1
#define MODE_MULTIPLY 2
#define MODE_SCREEN 3
#define MODE_SUBTRACT 4
#define MODE_LIGHTEN 5
#define MODE_DARKEN 6
#define MODE_OVERLAY 7
#define MODE_SOFT_LIGHT 8
#define MODE_HARD_LIGHT 9
#define MODE_COLOR_DODGE 10
#define MODE_DIFFERENCE 11

float blendOverlay(float b, float f) {
    return b < 0.5 ? (2.0 * b * f) : (1.0 - 2.0 * (1.0 - b) * (1.0 - f));
}

float blendSoftLight(float b, float f) {
    return (f < 0.5) ? (2.0 * b * f + b * b * (1.0 - 2.0 * f)) : (sqrt(b) * (2.0 * f - 1.0) + 2.0 * b * (1.0 - f));
}

float blendHardLight(float b, float f) {
    return blendOverlay(f, b); // Hard Light is Overlay with swapped args
}

float blendColorDodge(float b, float f) {
    return (f == 1.0) ? f : min(b / (1.0 - f), 1.0);
}

vec3 applyBlend(vec3 b, vec3 f, int mode) {
    vec3 res = b;
    
    if (mode == MODE_NORMAL) {
        res = f;
    } else if (mode == MODE_ADD) {
        res = min(b + f, vec3(1.0));
    } else if (mode == MODE_MULTIPLY) {
        res = b * f;
    } else if (mode == MODE_SCREEN) {
        res = 1.0 - (1.0 - b) * (1.0 - f);
    } else if (mode == MODE_SUBTRACT) {
        res = max(b - f, vec3(0.0));
    } else if (mode == MODE_LIGHTEN) {
        res = max(b, f);
    } else if (mode == MODE_DARKEN) {
        res = min(b, f);
    } else if (mode == MODE_OVERLAY) {
        res.r = blendOverlay(b.r, f.r);
        res.g = blendOverlay(b.g, f.g);
        res.b = blendOverlay(b.b, f.b);
    } else if (mode == MODE_SOFT_LIGHT) {
        res.r = blendSoftLight(b.r, f.r);
        res.g = blendSoftLight(b.g, f.g);
        res.b = blendSoftLight(b.b, f.b);
    } else if (mode == MODE_HARD_LIGHT) {
        res.r = blendHardLight(b.r, f.r);
        res.g = blendHardLight(b.g, f.g);
        res.b = blendHardLight(b.b, f.b);
    } else if (mode == MODE_COLOR_DODGE) {
        res.r = blendColorDodge(b.r, f.r);
        res.g = blendColorDodge(b.g, f.g);
        res.b = blendColorDodge(b.b, f.b);
    } else if (mode == MODE_DIFFERENCE) {
        res = abs(b - f);
    }
    
    return clamp(res, 0.0, 1.0);
}

void main() {
    vec4 fColor = texture(uSrc, TexCoords);
    vec4 bColor = texture(uDst, TexCoords);
    
    // Layer Opacity can be applied to src alpha
    float srcAlpha = fColor.a * uOpacity;
    
    // If src is fully transparent, result is background
    if (srcAlpha <= 0.0) {
        FragColor = bColor;
        return;
    }
    
    // Calculate Blended Color (treating both as opaque color for blending math usually)
    // But we need to handle Alpha Compositing carefully.
    // Standard formula: Out = Blend(B, S) * a + B * (1-a)
    
    vec3 blendedRGB = applyBlend(bColor.rgb, fColor.rgb, uMode);
    
    // Create final alpha (Union of alphas)
    float outAlpha = srcAlpha + bColor.a * (1.0 - srcAlpha);
    
    // Interpolate between Background and Blended Result based on Source Alpha
    vec3 finalRGB = mix(bColor.rgb, blendedRGB, srcAlpha);
    
    FragColor = vec4(finalRGB, outAlpha);
}
