#version 330 core
out vec4 FragColor;
in vec3 Normal;
in vec2 TexCoords; 

uniform sampler2D noiseTexture;
uniform float scale;
uniform float intensity;
uniform vec3 color;

void main()
{
    vec2 uv = TexCoords * scale;
    
    vec4 texColor = texture(noiseTexture, uv);
    float noiseVal = texColor.r; 
    
    // For Multiply mode:
    // We want base color to be white (1,1,1) where noise is 0? No wait.
    // Noise 0..1. 
    // If noise is black (0), result is 0?
    
    // Let's implement modulation:
    // Final = mix(White, Color, NoiseVal * Intensity) ?
    // Usually noise is used as a mask or direct overlay.
    
    // If Blend Mode is Multiply:
    // Output = 1.0 (No change) where we want no noise.
    // Output = Color where we want noise.
    
    // Assume NoiseVal 0..1 (Random).
    // We want to interpolate between White (1,1,1) and TargetColor based on NoiseVal * Intensity.
    
    vec3 target = color;
    vec3 white = vec3(1.0);
    
    vec3 finalColor = mix(white, target, noiseVal * intensity);
    
    // Alpha should be 1.0 because we output "the color to be multiplied".
    // If we use Alpha blending, we need to match glBlendFunc logic.
    // Multiply func: Dst * (Src + 1 - A).
    // If we output A=1, result is Dst * Src.
    
    FragColor = vec4(finalColor, 1.0); 
}
