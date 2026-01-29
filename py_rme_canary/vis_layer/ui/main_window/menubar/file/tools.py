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


def import_monsters_npcs(editor) -> None:
    editor._import_monsters_npcs()


def import_monster_folder(editor) -> None:
    editor._import_monster_folder()


def import_map(editor) -> None:
    editor._import_map()
