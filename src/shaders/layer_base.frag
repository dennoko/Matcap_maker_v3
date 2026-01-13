#version 330 core
out vec4 FragColor;

in vec3 Normal;
in vec3 FragPos;

uniform vec3 baseColor;

void main()
{
    // Simple flat color for now, maybe simple shading to see 3D
    // But Matcap usually implies we map normals to UVs or just use base color as starting point.
    // For Base Layer, we might just want to fill the sphere mask or standard shading.
    // Let's do simple N dot L for visualization in Checkpoint 2.
    
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(vec3(0.5, 0.5, 1.0));
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = diff * baseColor;
    vec3 ambient = 0.1 * baseColor;
    
    // Alpha 1.0
    FragColor = vec4(ambient + diffuse, 1.0);
}
