from __future__ import annotations


def choose_assets_dir(editor) -> None:
    editor._choose_assets_dir()


def load_client_data_stack(editor) -> None:
    editor._open_client_data_loader()


def manage_client_profiles(editor) -> None:
    editor._manage_client_profiles()


def load_appearances(editor) -> None:
    editor._load_appearances_dat()


def unload_appearances(editor) -> None:
    editor._unload_appearances_dat()
