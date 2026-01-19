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
