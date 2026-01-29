"""Menubar tool handlers.

Each top-level menubar menu gets its own folder with pure functions that
implement the menu actions. This keeps `QtMapEditor` mixins small and avoids
scattering QAction handlers across unrelated modules.
"""
