## Unreleased (py_rme_canary)

Features:

* UI parity: implementado “Find Item…” (Ctrl+F) com busca real no mapa e navegação até o resultado.
* UI parity: implementado “Find on Map → Waypoint…” (busca por substring, case-insensitive) com seleção de resultado e centralização.
* UI parity: implementado “Find on Map → Item…” reutilizando o pipeline do Find Item.
* Legacy parity: implementado “Replace Items…” como operação em lote, undoable (um único passo), com limite de segurança padrão alinhado ao legado (500) e suporte a containers.
* Legacy parity: implementado “Replace Items on Selection…” (variante restrita à seleção), mantendo semântica/undo do legado.
* Legacy parity: implementado “Remove Item on Selection…” (remove em ground + stack de topo; melhor-esforço para pular itens “complex”).
* Legacy parity: implementado “Map Statistics…” com relatório textual (Refresh/Export) inspirado no RME.

* Legacy parity: mirror drawing behavior (axis + dedupe + bounds) centralized in logic layer and used by the PyQt6 canvas.
* OTBM parity: improved loader/saver compatibility (attribute map roundtrip, OTBM v1 subtype byte support, and stackable COUNT rules for v2+).
* Legacy parity: brush footprint and border-ring offset generation extracted into a pure geometry module with tests.

Quality:

* Architecture: mantida a separação por camadas (logic_layer Qt-free + vis_layer Qt), com operações testáveis fora do GUI.
* UI robustness: corrigida a inicialização de menus/ações no app Qt (evita menus temporários e chamadas para helpers inexistentes).
* UI bugfix: corrigido bug de indentação onde dialogs de waypoint/resultados ficaram acidentalmente “nested” dentro de outra classe.
* Tests: adicionados/expandido testes de busca (itens/waypoints), replace (incl. seleção) e remove (seleção), mantendo `pytest -q` verde.
* Quality pipeline: `quality.sh` agora usa `PYTHON_BIN`, corrige normalização de issues e comparação de símbolos, e faz mypy apenas em core/logic_layer.
* Tooling: `tools/convert_png2cpp.py` migrado para Python 3 com I/O em UTF-8.
* Type safety: ajustes de tipagem em selection/live_server para alinhar com protocolos.

* Repository cleanup: removed deprecated `data_layer/` and eliminated experimental UI codepaths (no PySide6/Tk in the canonical UI).
* Test standardization: consolidated on pytest-only under `tests/`.
* Optional quality tooling: added incremental `ruff`/`mypy` setup and contributor documentation.

Planned / Future:

* Legacy parity: “Remove Monsters on Selection…” (e variações de contagem), seguindo o padrão: lógica Qt-free + operação undoable + wiring no menu.
* Legacy parity: “Remove duplicated items on selection…” (limpeza por duplicatas, restrito à seleção).
* Legacy parity: “Search for … on Selection” (action/containers/writeable/tiles/properties) com janela de resultados e export, inspirado no legado.
* Config parity: expor limites de segurança (REPLACE_SIZE/REMOVE_SIZE) como setting configurável, mantendo defaults do legado.

#### 3.5

Features:

* Implements flood fill in Terrain Brush.
* Update wall brushes for 10.98
* Added Show As Minimap menu.
* Make spawns visible when placing a new spawn.

Fixed bugs:

* Fix container item crash.

#### 3.4

Features:

* New Find Item / Jump to Item dialog.
* Configurable copy position format.
* Add text ellipsis for tooltips.
* Show hook indicators for walls.
* Updated data for 10.98

Fixed bugs:

* Icon background colour; white and gray no longer work.
* Only show colors option breaks RME.

#### 3.3

Features:

* Support for tooltips in the map.
* Support for animations preview.
* Restore last position when opening a map.
* Export search result to a .txt file.
* Waypoint brush improvements.
* Better fullscreen support on macOS.

Fixed bugs:

* Items larger than 64x64 are now displayed properly.
* Fixed potential crash when using waypoint brush.
* Fixed a bug where you could not open map files by clicking them while the editor is running.
* You can now open the extensions folder on macOS.
* Fixed a bug where an item search would not display any result on macOS.
* Fixed multiple issues related to editing houses on macOS.

#### 3.2

Features:

* Export minimap by selected area.
* Search for unique id, action id, containers or writable items on selected area.
* Go to Previous Position menu. Keyboard shortcut 'P'.
* Data files for version 10.98.
* Select Raw button on the Browse Field window.

Fixed bugs:

* Text is hidden after selecting an item from the palette. Issue #144
* Search result does not sort ids. Issue #126
* Monster direction is not saved. Issue #132

#### 3.1

Features:

* In-game box improvements. Now the hidden tiles, visible tiles and player position are displayed.
* New _Zoom In_, _Zoom Out_ and _Zoom Normal_ menus.
* New keyboard shortcuts:
	- **Ctrl+Alt+Click** Select the relative brush of an item.
	- **Ctrl++** Zoom In
	- **Ctrl+-** Zoom Out
	- **Ctrl+0** Zoom Normal(100%)
* If zoom is 100%, move one tile at a time.

Fixed bugs:

* Some keyboard shortcuts not working on Linux.
* Main menu is not updated when the last map tab is closed.
* In-game box wrong height.
* UI tweaks for Import Map window.
