#version 330 core
out vec4 FragColor;
in vec3 Normal;
in vec3 FragPos; 
in vec2 TexCoords;
in mat3 TBN;

uniform vec3 color;
uniform float intensity;
uniform float power;
uniform float bias;

uniform bool useNormalMap;
uniform sampler2D normalMap;
uniform float normalStrength;
uniform float normalScale;
uniform vec2 normalOffset;

vec3 getNormal() {
    if (useNormalMap && FragPos.x > 0.0) {
        vec2 uv = TexCoords * normalScale + normalOffset;
        vec3 normal = texture(normalMap, uv).rgb;
        normal = normal * 2.0 - 1.0;
        normal.xy *= normalStrength;
        return normalize(TBN * normalize(normal));
    }
    return normalize(Normal);
}

void main()
{
    vec3 norm = getNormal();
    // View direction: from surface toward camera
    // Camera looks down -Z, so view direction is -Z
    vec3 viewDir = vec3(0.0, 0.0, -1.0); 
    
    // dot(N, V): high at center (normals point toward camera), low at edge
    float ndotv = max(dot(norm, viewDir), 0.0);
    
    // Fresnel/Rim: bright at edge (ndotv~0), dark at center (ndotv~1)
    float rim = pow(1.0 - ndotv, max(power, 0.001));
    
    rim = clamp(rim + bias, 0.0, 1.0);
    
    vec3 finalColor = rim * color * intensity;
    
    FragColor = vec4(finalColor, rim); 
}
