#version 330 core
out vec4 FragColor;
in vec2 TexCoords;

uniform sampler2D screenTexture;

void main()
{
    // The accumulator stores straight (un-premultiplied) alpha. Effects like
    // Blur let color bleed past the matcap silhouette (alpha clamped to the
    // original shape for export), so the texture still holds stray RGB where
    // alpha == 0. Composite over the black preview background using alpha to
    // cut that region out before display — without this the bleed would show
    // as the matcap circle visually growing outward.
    vec4 c = texture(screenTexture, TexCoords);
    FragColor = vec4(c.rgb * c.a, 1.0);
}
