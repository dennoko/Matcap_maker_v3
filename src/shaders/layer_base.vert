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

    // "Both" mode detection: Right side object (Cube) is at x=0.5
    // "Single" mode (Cube only): Center is 0.0
    // But currently GeometryEngine.get_cube() uses offset_x=0.0 default.
    // Wait, if I select "Cube" only, offset is 0.
    // My logic `if (pos.x > 0.0)` assumes "Both" mode separation.
    // If "Cube" only is selected, it is at 0.0. User might want to rotate it too.
    // "Sphere" only is at 0.0.
    // But User said "Separate Matcap Preview" implies "Both" mode is the main use case for this differentiation.
    // If I rotate everything when previewRotation > 0, it's fine?
    // User said "Cubeを回転させる" (Rotate the Cube).
    // If "Sphere" (Matcap Gen) is rotating, the Matcap changes dynamically. Maybe desired?
    // But "Matcap Preview" usually implies static standard view.
    // I will stick to "Rotate if x > 0 (Right Side)" OR "Rotate if Shape is Cube centered"?
    // The safest heuristic for "Both" mode is x > 0.
    // For "Cube Only" mode, x approx 0.
    // Since "Both" mode puts Sphere at -0.5, it is < 0.
    // So `if (pos.x > 0.1)` targets the Right object.
    
    // However, if Single Cube is at 0, how to rotate?
    // Maybe pass `uniform int previewMode;`?
    // Or just "Always rotate logic, but `previewRotation` is 0 for Sphere"?
    // `PreviewWidget` controls `previewRotation`.
    // If Shape == Sphere, rotation = 0.
    // If Shape == Cube, rotation = animated.
    // If Shape == Both, rotation = animated (but only apply to Cube?).
    
    // Let's refine logic:
    // If `aPos.x > 0.1` (Right Object in Both Mode) -> Rotate about 0.5.
    // If `abs(aPos.x) < 0.8` (Centered Object) -> Rotate about 0.0?
    // Actually, `GeometryEngine` for Single Cube has offset 0.
    // `GeometryEngine` for Combined has Cube at 0.5.
    
    // Robust logic:
    // uniform vec3 rotationCenter;
    // uniform bool doRotate;
    // Too complex for vertex shader injection via Engine?
    
    // Let's stick to: Rotate Right Side Object (x > 0.1) around 0.5.
    // AND Rotate Center Object (Cube Mode) around 0.0?
    // How to distinguish Cube Mode from Sphere Mode in Vertex Shader?
    // Sphere Mode (Single) Vertices are same range as Cube Mode (Single).
    // I can't distinguish geometry.
    // But `PreviewWidget` knows.
    // If I pass `rotation` as 0 when Sphere Only, it works.
    // The only issue is "Both" mode. Sphere should stay static.
    
    // Logic:
    bool isRightObject = (pos.x > 0.05); // "Both" mode right side
    bool isCenterObject = (abs(pos.x) < 2.0 && abs(pos.x - 0.5) > 0.2 && abs(pos.x + 0.5) > 0.2); 
    // Wait, simpler:
    // If "Both" mode, Sphere is at -0.5, Cube at 0.5.
    // If "Single" mode, Object is at 0.0.
    // If `previewRotation` is active, we apply it.
    // To protect Left Sphere in "Both" mode, we check pos.x.
    
    // Shift processing:
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
