#version 330 core
out vec4 FragColor;

in vec3 Normal;
in vec3 FragPos;

uniform vec3 baseColor;

void main()
{
    // Pure Flat Color (Unlit)
    // Matcap base is essentially a mask or starting canvas.
    FragColor = vec4(baseColor, 1.0);
}
