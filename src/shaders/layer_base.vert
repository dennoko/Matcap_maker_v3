#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in vec2 aTexCoords;
layout (location = 3) in vec3 aTangent;

out vec3 FragPos;
out vec2 TexCoords;
out mat3 TBN;
out vec3 Normal; // Fallback

uniform float previewRotation;
uniform vec3 uScale; // Aspect Ratio Scaling

void main()
{
    vec3 pos = aPos;
    vec3 norm = aNormal;
    vec3 tan = aTangent;

    // Optional Y-axis rotation for the preview object.
    // Comparison mode places the matcap sphere at x=-0.5 (never rotated)
    // and the preview object at x=+0.5 (rotated around its own center);
    // single mode places the object at x=0.
    float pivotX = 0.0;
    bool applyRot = true;

    if (pos.x < -0.1) {
        // Left Side (Sphere in Both Mode) -> NO ROTATION
        applyRot = false;
    } else if (pos.x > 0.1) {
        // Right Side (Cube in Both Mode) -> Center 0.5
        pivotX = 0.5;
    } else {
        // Center (Single Mode) -> Center 0.0
        pivotX = 0.0;
    }
    
    if (applyRot && previewRotation != 0.0) {
        pos.x -= pivotX;
        
        float c = cos(previewRotation);
        float s = sin(previewRotation);
        mat2 rot = mat2(c, -s, s, c);
        
        vec2 p_xz = vec2(pos.x, pos.z);
        p_xz = rot * p_xz;
        pos.x = p_xz.x;
        pos.z = p_xz.y;
        
        pos.x += pivotX;
        
        vec2 n_xz = vec2(norm.x, norm.z);
        n_xz = rot * n_xz;
        norm.x = n_xz.x;
        norm.z = n_xz.y;
        
        vec2 t_xz = vec2(tan.x, tan.z);
        t_xz = rot * t_xz;
        tan.x = t_xz.x;
        tan.z = t_xz.y;
    }

    FragPos = pos;
    TexCoords = aTexCoords;
    Normal = norm;
    
    vec3 T = normalize(tan);
    vec3 N = normalize(norm);
    T = normalize(T - dot(T, N) * N);
    vec3 B = cross(N, T);
    TBN = mat3(T, B, N);
    
    // Apply Aspect Ratio Scaling
    // uScale.z is ignored usually, set to 1.0
    vec3 scaledPos = pos * uScale;
    
    gl_Position = vec4(scaledPos, 1.0);
}
