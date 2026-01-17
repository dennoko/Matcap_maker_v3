#version 330 core

in vec2 TexCoords;
out vec4 FragColor;

uniform sampler2D uTexture;

uniform float uHue;        // -0.5 to 0.5 (shifts around circle)
uniform float uSaturation; // 0.0 to 2.0 (1.0 = normal)
uniform float uBrightness; // -1.0 to 1.0 (0.0 = normal)
uniform float uContrast;   // 0.0 to 2.0 (1.0 = normal)

// RGB to HSV conversion
vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));

    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

// HSV to RGB conversion
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void main() {
    vec4 color = texture(uTexture, TexCoords);
    vec3 rgb = color.rgb;

    // 1. Hue & Saturation
    vec3 hsv = rgb2hsv(rgb);
    hsv.x += uHue;
    hsv.y *= uSaturation;
    rgb = hsv2rgb(hsv);

    // 2. Brightness
    rgb += uBrightness;

    // 3. Contrast
    // Interpolate around 0.5 (gray)
    rgb = (rgb - 0.5) * uContrast + 0.5;

    FragColor = vec4(rgb, color.a);
}
