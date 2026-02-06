"""GLSL Shader sources for the rendering system.

This module provides shader source code matching the Redux architecture:
- sprite_batch.vert/frag: Modern sprite batching with texture arrays
- basic.vert/frag: Simple 2D rendering

Reference:
    - C++ Redux: source/rendering/shaders/
"""

from __future__ import annotations

# =============================================================================
# SPRITE BATCH SHADER (Modern - uses sampler2DArray)
# =============================================================================
# Matches: remeres-map-editor-redux/source/rendering/shaders/sprite_batch.vert/frag

SPRITE_BATCH_VERTEX = """
#version 330 core

// Vertex attributes
layout(location = 0) in vec2 a_pos;       // Screen position
layout(location = 1) in vec2 a_uv;        // Texture UV (0-1)
layout(location = 2) in vec4 a_color;     // Tint color
layout(location = 3) in float a_layer;    // Texture array layer index

// Uniforms
uniform vec2 u_viewport;                  // Viewport dimensions

// Outputs to fragment shader
out vec2 v_uv;
out vec4 v_color;
flat out int v_layer;

void main() {
    // Convert screen coordinates to NDC (-1 to 1)
    vec2 ndc = vec2(
        (a_pos.x / u_viewport.x) * 2.0 - 1.0,
        1.0 - (a_pos.y / u_viewport.y) * 2.0
    );
    gl_Position = vec4(ndc, 0.0, 1.0);

    v_uv = a_uv;
    v_color = a_color;
    v_layer = int(a_layer);
}
"""

SPRITE_BATCH_FRAGMENT = """
#version 330 core

// Inputs from vertex shader
in vec2 v_uv;
in vec4 v_color;
flat in int v_layer;

// Uniforms
uniform sampler2DArray u_texture_array;   // Sprite atlas as texture array
uniform int u_use_texture;                // 0 = color only, 1 = use texture

// Output
out vec4 fragColor;

void main() {
    vec4 base = v_color;

    if (u_use_texture == 1) {
        // Sample from texture array using layer as Z coordinate
        vec4 tex = texture(u_texture_array, vec3(v_uv, float(v_layer)));

        // Discard fully transparent pixels
        if (tex.a < 0.01) {
            discard;
        }

        base *= tex;
    }

    fragColor = base;
}
"""

# =============================================================================
# BASIC SHADER (Simple 2D - for colored quads and lines)
# =============================================================================

BASIC_VERTEX = """
#version 330 core

layout(location = 0) in vec2 a_pos;
layout(location = 1) in vec2 a_uv;
layout(location = 2) in vec4 a_color;

uniform vec2 u_viewport;

out vec2 v_uv;
out vec4 v_color;

void main() {
    vec2 ndc = vec2(
        (a_pos.x / u_viewport.x) * 2.0 - 1.0,
        1.0 - (a_pos.y / u_viewport.y) * 2.0
    );
    gl_Position = vec4(ndc, 0.0, 1.0);
    v_uv = a_uv;
    v_color = a_color;
}
"""

BASIC_FRAGMENT = """
#version 330 core

in vec2 v_uv;
in vec4 v_color;

uniform sampler2D u_texture;
uniform int u_use_texture;

out vec4 fragColor;

void main() {
    vec4 base = v_color;
    if (u_use_texture == 1) {
        vec4 tex = texture(u_texture, v_uv);
        base *= tex;
    }
    fragColor = base;
}
"""

# =============================================================================
# LIGHTING SHADER (For preview window)
# =============================================================================

LIGHTING_VERTEX = """
#version 330 core

layout(location = 0) in vec2 a_pos;
layout(location = 1) in vec2 a_uv;

uniform vec2 u_viewport;

out vec2 v_uv;
out vec2 v_screen_pos;

void main() {
    vec2 ndc = vec2(
        (a_pos.x / u_viewport.x) * 2.0 - 1.0,
        1.0 - (a_pos.y / u_viewport.y) * 2.0
    );
    gl_Position = vec4(ndc, 0.0, 1.0);
    v_uv = a_uv;
    v_screen_pos = a_pos;
}
"""

LIGHTING_FRAGMENT = """
#version 330 core

in vec2 v_uv;
in vec2 v_screen_pos;

uniform sampler2D u_scene;           // Rendered scene
uniform sampler2D u_lightmap;        // Per-tile light intensity (R8)
uniform vec3 u_ambient_light;        // Ambient light color (0-1)
uniform float u_light_intensity;     // Global light multiplier

out vec4 fragColor;

void main() {
    vec4 scene = texture(u_scene, v_uv);
    float light = texture(u_lightmap, v_uv).r;

    // Combine ambient with per-tile light
    vec3 total_light = u_ambient_light + vec3(light) * u_light_intensity;
    total_light = clamp(total_light, 0.0, 1.0);

    fragColor = vec4(scene.rgb * total_light, scene.a);
}
"""

# =============================================================================
# GRID OVERLAY SHADER (For preview window)
# =============================================================================

GRID_VERTEX = """
#version 330 core

layout(location = 0) in vec2 a_pos;

uniform vec2 u_viewport;
uniform vec2 u_offset;      // Camera offset
uniform float u_scale;      // Zoom level

out vec2 v_world_pos;

void main() {
    vec2 ndc = vec2(
        (a_pos.x / u_viewport.x) * 2.0 - 1.0,
        1.0 - (a_pos.y / u_viewport.y) * 2.0
    );
    gl_Position = vec4(ndc, 0.0, 1.0);

    // Calculate world position for grid calculation
    v_world_pos = (a_pos + u_offset) / u_scale;
}
"""

GRID_FRAGMENT = """
#version 330 core

in vec2 v_world_pos;

uniform float u_tile_size;      // Size of one tile (typically 32)
uniform vec4 u_grid_color;      // Grid line color
uniform float u_line_width;     // Grid line thickness

out vec4 fragColor;

void main() {
    // Calculate distance to nearest grid line
    vec2 grid_uv = mod(v_world_pos, u_tile_size);
    vec2 to_line = min(grid_uv, u_tile_size - grid_uv);
    float dist = min(to_line.x, to_line.y);

    // Anti-aliased grid line
    float alpha = 1.0 - smoothstep(0.0, u_line_width, dist);

    if (alpha < 0.01) {
        discard;
    }

    fragColor = vec4(u_grid_color.rgb, u_grid_color.a * alpha);
}
"""

__all__ = [
    "SPRITE_BATCH_VERTEX",
    "SPRITE_BATCH_FRAGMENT",
    "BASIC_VERTEX",
    "BASIC_FRAGMENT",
    "LIGHTING_VERTEX",
    "LIGHTING_FRAGMENT",
    "GRID_VERTEX",
    "GRID_FRAGMENT",
]
