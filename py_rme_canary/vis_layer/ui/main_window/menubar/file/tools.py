from __future__ import annotations


def new_map(editor) -> None:
    editor._new_map()


def open_map(editor) -> None:
    editor._open_otbm()


def save(editor) -> None:
    editor._save()


def save_as(editor) -> None:
    editor._save_as()


def exit_app(editor) -> None:
    editor.close()


def export_png(editor) -> None:
    editor._export_png()


def export_otmm(editor) -> None:
    editor._export_otmm()


def export_tilesets(editor) -> None:
    editor._export_tilesets()


def reload_data(editor) -> None:
    editor._reload_data_files()


def open_preferences(editor) -> None:
    editor._open_preferences()


def open_extensions(editor) -> None:
    editor._open_extensions_dialog()


def goto_website(editor) -> None:
    editor._goto_website()


def import_monsters_npcs(editor) -> None:
    editor._import_monsters_npcs()


def import_monster_folder(editor) -> None:
    editor._import_monster_folder()


def import_map(editor) -> None:
    editor._import_map()


def generate_map(editor) -> None:
    editor._generate_map()


def close_map(editor) -> None:
    editor._close_map()


def export_minimap(editor) -> None:
    editor._export_minimap()
