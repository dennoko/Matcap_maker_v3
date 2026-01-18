#version 330 core
out vec4 FragColor;

// --- Inputs ---
in vec3 Normal;
in vec2 TexCoords; 
in mat3 TBN;
in vec3 FragPos; 

// --- Uniforms ---
uniform sampler2D noiseTexture;
uniform float scale;
uniform float intensity;
uniform vec3 color;

// Normal Map Uniforms
uniform bool useNormalMap;
uniform sampler2D normalMap;
uniform float normalStrength;
uniform float normalScale;
uniform vec2 normalOffset;

// Preview State
uniform int previewMode; // 0=Standard, 1=Comparison

// --- Functions ---
vec3 getMappedNormal() {
    if (useNormalMap) {
        vec2 uv = TexCoords * normalScale + normalOffset;
        vec3 normal = texture(normalMap, uv).rgb;
        normal = normal * 2.0 - 1.0;
        normal.xy *= normalStrength;
        return normalize(normal);
    }
    return vec3(0.0, 0.0, 1.0);
}

void main()
{
    vec2 uv = TexCoords;
    
    // Apply Normal Map Distortion ONLY if:
    // 1. We have a specific Normal Map
    // 2. We are in Comparison Mode (previewMode == 1)
    // 3. We are drawing the Right Side (FragPos.x > 0.0)
    if (useNormalMap && previewMode == 1 && FragPos.x > 0.0) {
        vec3 mappedNormal = getMappedNormal();
        uv -= mappedNormal.xy * 0.1; 
    }

    uv = uv * scale;
    
    vec4 texColor = texture(noiseTexture, uv);
    float noiseVal = texColor.r; 
    
    vec3 target = color;
    vec3 white = vec3(1.0);
    
    vec3 finalColor = mix(white, target, noiseVal * intensity);
    
    FragColor = vec4(finalColor, 1.0); 
}
