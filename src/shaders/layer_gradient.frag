#version 330 core
out vec4 FragColor;
in vec3 Normal;
in vec3 FragPos;

const int MAX_STOPS = 8;
uniform int   uNumStops;
uniform float uStopPositions[8];  // sorted 0.0 to 1.0
uniform vec3  uStopColors[8];
uniform float uAngle;             // radians
uniform int   uGradientType;      // 0=Linear, 1=Radial

void main()
{
    vec3 norm = normalize(Normal);
    float t;

    if (uGradientType == 0) {
        // Linear: project normal onto gradient direction
        vec3 gradDir = vec3(cos(uAngle), sin(uAngle), 0.0);
        t = (dot(norm, gradDir) + 1.0) * 0.5;
    } else {
        // Radial: distance from sphere top pole (Normal.xy magnitude)
        t = clamp(length(norm.xy), 0.0, 1.0);
    }

    // Walk through sorted stops to find the enclosing segment
    vec3 grad_color = uStopColors[0];
    bool found = false;

    for (int i = 0; i < MAX_STOPS - 1; i++) {
        if (i >= uNumStops - 1) break;
        float pos0 = uStopPositions[i];
        float pos1 = uStopPositions[i + 1];
        if (t <= pos1) {
            float span = pos1 - pos0;
            float local_t = (span > 0.0001) ? clamp((t - pos0) / span, 0.0, 1.0) : 0.0;
            grad_color = mix(uStopColors[i], uStopColors[i + 1], local_t);
            found = true;
            break;
        }
    }

    // t is beyond the last stop: clamp to last color
    if (!found && uNumStops > 0) {
        grad_color = uStopColors[uNumStops - 1];
    }

    FragColor = vec4(grad_color, 1.0);
}
