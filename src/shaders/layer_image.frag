#version 330 core
out vec4 FragColor;
in vec3 Normal;
in vec3 FragPos; 
in vec2 TexCoords;
in mat3 TBN;

uniform sampler2D imageTexture;
uniform int mappingMode; // 0=UV, 1=Planar
uniform float scale;
uniform vec2 scaleXY; // Per-axis multipliers on top of `scale`
uniform float rotation;
uniform vec2 offset;
uniform float aspectRatio; // Image Aspect Ratio (w/h)
uniform float blur;

uniform int previewMode; // 0=Standard, 1=Comparison

uniform bool useNormalMap;
uniform sampler2D normalMap;
uniform float normalStrength;
uniform float normalScale;
uniform vec2 normalOffset;

#define PI 3.14159265359

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

vec2 rotateUV(vec2 uv, float angle)
{
    float s = sin(angle);
    float c = cos(angle);
    mat2 rot = mat2(c, -s, s, c);
    return rot * uv;
}

void main()
{
    vec2 uv;
    
    // ---------------------------------------------------------
    // 1. Determine which Mapping Logic to use
    // ---------------------------------------------------------
    
    bool isRightSidePreview = (previewMode == 1) && (FragPos.x > 0.0);
    
    if (mappingMode == 0) {
        // --- UV (Wrapped) ---
        // Maps texture using Mesh UV coordinates.
        uv = TexCoords;
        
        // distortion from normal map
        // If we have a normal map, we want to distort the UVs based on the bumps.
        // Concept: Position shift = Normal_Map_Value * Strength
        // We can approximate this by shifting UVs based on the difference between 
        // the Geometric Normal and the Mapped Normal.
        
        if (useNormalMap) {
            // Original normal vs Mapped normal
            vec3 geomNormal = normalize(Normal);
            vec3 mappedNormal = getNormal();
            
            // Start with simple offset based on normal deviation in Tangent Space?
            // Or just use the TBN projected difference.
            // Let's use the XY components of the mapped normal in Tangent Space?
            // getNormal returns World Space normal.
            // We need Tangent Space deviation to shift UVs reasonably.
            
            // Re-calculate Tangent Space Normal from World Space Mapped Normal
            // N_tangent = TBN_inverse * mappedNormal
            // TBN is orthogonal, so Inverse = Transpose
            
            vec3 tangentNormal = transpose(TBN) * mappedNormal;
            
            // tangentNormal.xy contains the slope information (perturbation).
            // If Strength is 0, tangentNormal is (0,0,1).
            // If Strength > 0, xy deviates from 0.
            
            // We can subtract the "flat" vector (0,0,1) or just take xy.
            // Direction of shift?
            // Usually looking at a bump, the texture behind it should distort.
            // Parallax mapping uses ViewDir, but here we just want basic "wobble".
            // Simply adding (normal.xy * 0.5) roughly simulates refraction/distortion.
            
            // Scale factor tuning might be needed.
            uv -= tangentNormal.xy * 0.1; // 0.1 is an arbitrary factor to make it look nice
        }

        uv.y = 1.0 - uv.y; // Fix inverted UVs from Geometry
    } else {
        // --- Planar (Screen Space / Matcap) ---
        
        if (isRightSidePreview) {
            // [RIGHT SIDE PREVIEW - PLANAR MODE]
            // If we are in Planar mode, the user likely wants to see how this Matcap looks 
            // on the sphere (Spherical Mapping driven by Normal).
            vec3 n = getNormal(); // Includes Normal Map distortion
            uv = n.xy * 0.5 + 0.5;
        } else {
            // [LEFT SIDE GENERATOR - PLANAR MODE]
            // Standard Screen Space mapping for creating the Matcap.
             float centerX = (previewMode == 1) ? -0.5 : 0.0;
            vec2 centerInfo = vec2(centerX, 0.0);
            vec2 pos = FragPos.xy - centerInfo;
            
            // Normalize based on Radius
            // Preview Mode 1 (Comparison) -> Radius 0.45
            // Preview Mode 0 (Standard)   -> Radius 1.0
            float radius = (previewMode == 1) ? 0.45 : 1.0;
            uv = (pos / radius) * 0.5 + 0.5;
        }
    }
    
    // ---------------------------------------------------------
    // 2. Aspect Ratio Correction (Before Rotation/Scale)
    // ---------------------------------------------------------
    // Correct for image Aspect Ratio to prevent stretching usage logic:
    // Center is 0.5
    uv -= 0.5;
    
    // If AR > 1 (Wide), we want to squash Y (uv.y * AR) to make pixels square
    // If AR < 1 (Tall), we want to squash X (uv.x / AR) -> (uv.x * (1/AR))
    
    if (aspectRatio > 1.0) {
        uv.y *= aspectRatio;
    } else {
        uv.x *= (1.0 / aspectRatio);
    }
    
    // ---------------------------------------------------------
    // 3. Apply Transforms (Offset, Rotation, Scale)
    // ---------------------------------------------------------
    
    // Rotation
    uv = rotateUV(uv, radians(rotation));
    
    // Scale (overall * per-axis)
    uv.x /= scale * scaleXY.x;
    uv.y /= scale * scaleXY.y;
    
    // Offset (Applied after scale/rot? Or before? User usually expects "Move image")
    // If we move AFTER scaling/aspect, "Offset" unit depends on scale/aspect.
    // Let's apply Offset LAST (so it translates the final image window)
    // Wait, standard UV math:
    // Pos -> Scale -> Rot -> Trans -> UV
    // Here we are doing Inverse: UV -> Inverse Trans -> Inverse Rot -> Inverse Scale -> Image
    // So:
    // uv -= offset; // Move the window
    // uv = rot(uv);
    // uv = uv / scale;
    
    // Re-center for transform calc was already done at "uv -= 0.5"
    // Let's add offset here.
    uv -= offset;
    
    // Shift back to 0..1 range
    uv += 0.5;

    // ---------------------------------------------------------
    // 4. Sample & Output
    // ---------------------------------------------------------
    
    vec4 texColor = vec4(0.0);

    if (blur <= 0.001) {
        texColor = texture(imageTexture, uv);
    } else {
        // Gaussian blur in the image's own texel space. Two tricks keep it
        // smooth and artifact-free regardless of blur amount:
        //  1) Tap spacing scales with the radius (in texels), so taps never
        //     spread into the sparse ghosting the old fixed kernel produced.
        //  2) Each tap reads a mip level matched to that spacing (textureLod),
        //     so it is pre-filtered and the gaps between taps don't alias.
        // Premultiplied alpha avoids dark halos bleeding from transparent texels.
        ivec2 ts = textureSize(imageTexture, 0);
        vec2 texel = 1.0 / vec2(ts);
        float maxDim = float(max(ts.x, ts.y));

        const int K = 3;                              // 7x7 taps
        float radiusTexels = blur * maxDim * 0.04;    // up to ~4% of the image
        float spacing = max(radiusTexels / float(K), 1.0);
        float sigma = max(radiusTexels * 0.5, 1e-3);
        float lod = max(0.0, log2(spacing));

        float totalWeight = 0.0;
        for (int x = -K; x <= K; x++) {
            for (int y = -K; y <= K; y++) {
                vec2 o = vec2(float(x), float(y)) * spacing;
                float weight = exp(-dot(o, o) / (2.0 * sigma * sigma));
                vec4 c = textureLod(imageTexture, uv + o * texel, lod);
                texColor += vec4(c.rgb * c.a, c.a) * weight;  // premultiply
                totalWeight += weight;
            }
        }
        texColor /= totalWeight;
        texColor.rgb = (texColor.a > 1e-5) ? texColor.rgb / texColor.a : vec3(0.0);
    }
    
    // Check Bounds for Planar? (Clamp to border?)
    // GL_REPEAT is set in load_texture, so it repeats.
    // Layer opacity is applied by the blend pass (blend.frag).
    FragColor = texColor;
}
