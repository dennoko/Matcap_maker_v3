#version 330 core
out vec4 FragColor;
in vec3 Normal;
in vec3 FragPos;
in vec2 TexCoords;
in mat3 TBN;

uniform vec3 lightDir;
uniform vec3 lightColor;
uniform float intensity;
uniform float range;
uniform float blur;

// New Shape Uniforms
uniform float scaleX;
uniform float scaleY;
uniform float rotation;

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
    
    // 1. Light Basis Construction
    // We want a coordinate system where Z is pointing TO the light (L).
    vec3 L = normalize(-lightDir); 
    
    // Standard backface check
    float raw_ndotl = dot(norm, L);
    if (raw_ndotl <= 0.0) {
        FragColor = vec4(0.0);
        return;
    }
    
    // Construct orthogonal basis (Gram-Schmidt-like)
    vec3 UpGuess = abs(L.y) < 0.99 ? vec3(0, 1, 0) : vec3(1, 0, 0);
    vec3 Right = normalize(cross(UpGuess, L));
    vec3 Up = cross(L, Right);
    
    // 2. Project Normal onto this basis (Local Light Coordinates)
    // x, y represents the 'deviation' from the light center
    float x = dot(norm, Right);
    float y = dot(norm, Up);
    
    // 3. Apply 2D Rotation
    float rad = radians(rotation);
    float c = cos(rad);
    float s = sin(rad);
    float rx = x * c - y * s;
    float ry = x * s + y * c;
    
    // 4. Apply Scale (Inverse scaling of the coordinate stretches the feature)
    // Scale > 1.0 -> Coordinate smaller -> Deviation smaller -> Spot WIDER
    float sx = rx / max(0.001, scaleX);
    float sy = ry / max(0.001, scaleY);
    
    // 5. Reconstruct "Modified Z" (Pseudo NdotL)
    // dist_sq is sin^2(theta) in the distorted space
    float dist_sq = sx*sx + sy*sy;
    
    // If dist_sq > 1, it means the normal is 'behind' the plane in distorted space (clamped)
    float modified_ndotl = sqrt(max(0.0, 1.0 - dist_sq));
    
    // 6. Apply Standard Spot Logic with modified_ndotl
    // Map range to cutoff (larger range = smaller cutoff req = wider spot)
    float cutoff = 1.0 - range; 
    
    float epsilon = blur + 0.0001;
    float spot = smoothstep(cutoff - epsilon, cutoff + epsilon, modified_ndotl);
    
    vec3 finalColor = spot * lightColor * intensity;
    
    FragColor = vec4(finalColor, spot); 
}
