#version 330 core

in vec2 TexCoords;
out vec4 FragColor;

uniform sampler2D uTexture;   // unit 0: source for this pass
uniform sampler2D uOriginal;  // unit 1: untouched accumulated result (pass 1 only)

uniform int uPass;      // 0 = horizontal, 1 = vertical
uniform int uMode;      // 0 = Blur, 1 = Sharpen
uniform float uRadius;  // 0.0 - 1.0 Gaussian radius
uniform float uAmount;  // 0.0 - 2.0 sharpen strength
uniform float uOpacity; // 0.0 - 1.0 layer opacity (applied in pass 1)

// Taps per side. Step scales with radius so a fixed tap count still covers a
// large blur, while staying ~1 texel apart for small radii (no ghosting).
const int KERNEL = 16;

// Separable 1D Gaussian along `dir`. Works in premultiplied alpha to avoid
// dark halos bleeding from transparent texels, returns straight alpha.
vec4 blur1D(vec2 uv, vec2 dir) {
    ivec2 texSize = textureSize(uTexture, 0);
    float texDim = (uPass == 0) ? float(texSize.x) : float(texSize.y);
    vec2 texel = 1.0 / vec2(texSize);

    // Max blur reach in pixels, scaled by resolution for a resolution-
    // independent look.
    float radiusPx = uRadius * texDim * 0.04;
    float sigma = max(radiusPx * 0.5, 1e-3);
    float step = max(radiusPx / float(KERNEL), 1.0);

    vec4 sum = vec4(0.0);
    float totalW = 0.0;

    for (int i = -KERNEL; i <= KERNEL; i++) {
        float o = float(i) * step;
        float w = exp(-(o * o) / (2.0 * sigma * sigma));
        vec4 c = texture(uTexture, uv + dir * (o * texel));
        sum += vec4(c.rgb * c.a, c.a) * w;  // premultiply
        totalW += w;
    }

    sum /= totalW;
    // Un-premultiply back to straight alpha.
    vec3 rgb = (sum.a > 1e-5) ? sum.rgb / sum.a : vec3(0.0);
    return vec4(rgb, sum.a);
}

void main() {
    vec2 dir = (uPass == 0) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
    vec4 blurred = blur1D(TexCoords, dir);

    // Pass 0 (horizontal): just hand the intermediate to pass 1.
    if (uPass == 0) {
        FragColor = blurred;
        return;
    }

    // Pass 1 (vertical): `blurred` is now the full separable Gaussian.
    vec4 original = texture(uOriginal, TexCoords);

    vec4 result;
    if (uMode == 1) {
        // Unsharp mask: original + amount * (original - blurred)
        vec3 rgb = original.rgb + uAmount * (original.rgb - blurred.rgb);
        result = vec4(rgb, original.a);
    } else {
        // Keep the blurred color, but constrain coverage to the original
        // silhouette so the matcap circle does not grow outward as the radius
        // increases. (The blur itself still samples the expanded neighborhood;
        // only the final alpha is clamped to the original shape.)
        result = vec4(blurred.rgb, original.a);
    }

    // Layer opacity blends the effect against the untouched input.
    float op = clamp(uOpacity, 0.0, 1.0);
    FragColor = mix(original, result, op);
}
