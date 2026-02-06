# Deep Analysis of Remere's Map Editor Redux

## 1. Overview
Redux is a C++20/OpenGL 4.5 fork of RME.

## 2. Rendering System
*   **MapDrawer**: Uses composition (FloorDrawer, ItemDrawer).
*   **SpriteBatch**: Uses `GL_TEXTURE_2D_ARRAY` and MDI (`glMultiDrawElementsIndirect`).
*   **Shaders**: `sprite_batch.vert/frag` use `sampler2DArray`.

## 3. Tech Deep Dive (Internal Mechanisms)

### A. Rendering Pipeline (`sprite_batch.cpp`)
Redux uses a **Ring Buffer** approach.
1.  **Storage**: `GL_DYNAMIC_DRAW` buffer mapped via `glMapBufferRange`.
2.  **DSA**: Uses `glVertexArrayVertexBuffer`.
3.  **Vertex Layout**: Static Quad Geometry + Instance Data (Rect, UV, Tint, Layer).
4.  **MDI**: Aggregates batches to minimize CPU/GPU sync.

### B. Auto-Bordering Logic (`ground_brush.cpp`)
The `GroundBrush::getBrushTo` function determines connectivity.
*   **Priority**: Z-order > Border Rules.
*   **Complexity**: O(N) lookup.

### C. IO Optimization (`iomap_otbm.cpp`)
*   **Memory Mapping**: Streaming for large maps.
*   **OTGZ Support**: `libarchive` integration.
