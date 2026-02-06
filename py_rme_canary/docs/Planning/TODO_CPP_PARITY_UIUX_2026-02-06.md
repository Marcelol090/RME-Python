# TODO Deep Search - Paridade C++/Lua -> Python (2026-02-06)

## Escopo auditado
- Referência C++/Lua:
  - `remeres-map-editor-redux/data/menubar.xml`
  - `remeres-map-editor-redux/source/ui/main_menubar.cpp`
  - `remeres-map-editor-redux/source/ui/map_popup_menu.cpp`
  - `remeres-map-editor-redux/source/ui/menubar/map_actions_handler.cpp`
  - `remeres-map-editor-redux/source/ui/menubar/search_handler.cpp`
- Planejamento/visão de produto:
  - `py_rme_canary/docs/Planning/Features.md`
- Implementação Python:
  - `py_rme_canary/vis_layer/ui/main_window/*`
  - `py_rme_canary/vis_layer/ui/menus/context_menus.py`
  - `py_rme_canary/logic_layer/*`
  - `py_rme_canary/core/*`

## Resultado da análise (resumo)

### Implementado (base sólida)
- OTBM ClientID/ServerID com tradução de IDs em load/save.
- Lasso/freehand selection integrado no canvas.
- Import de monsters/NPC via Lua.
- Conversão de formato de mapa exposta no UI.
- Highlight visual de posição ao navegar.
- Infra de cross-version clipboard e sprite hash presente no projeto.

### Parcial / com lacunas de integração
- Context menu de item exibe opções avançadas, mas canvas conecta somente `set_find`, `set_replace`, `find_all`, `replace_all`.
- `FindItemDialog` possui flag `selection_only`, mas a busca itera o mapa inteiro.
- `Border Builder` atual é visualizador (sem edição persistente de regras).
- `PreferencesDialog` ainda sem persistência completa no `ConfigurationManager`.
- Export OTMM tem ação no menu, mas não há método `_export_otmm` no editor.
- Recursos "modern UX" dependentes de `menu_file/menu_edit` não são acionados porque esses atributos não são inicializados no builder atual.

### Ausências importantes vs C++ e vs Features.md
- Ações de limpeza/paridade de mapa:
  - Remove item por ID (mapa todo), remove corpses, remove unreachable, clear invalid houses.
- Busca dedicada por tipo (unique/action/container/writeable) com atalhos de menu equivalentes.
- Export Tilesets / Reload Data / Preferences / Extensions / Goto Website equivalentes de menu.
- Pipeline de ícones próprio (SVG/PNG) ainda incompleto; grande parte da UI usa emojis em labels/ações.
- "Show ClientIDs" (feature documentada) sem toggle funcional equivalente no UI.
- Aviso automático de UID duplicado no fluxo de edição/paste/load (atualmente foco manual por relatório).

## TODO de implementação (10 tarefas)

- [x] `P0-MENU-001` Paridade de menus File/About/Search/Selection com C++.
  - Incluir ações ausentes: Preferences, Reload Data, Export Tilesets, Extensions, Goto Website, Search dedicado.
  - Integrar ações no `build_actions.py` + `build_menus.py` com handlers reais.
  - Critério de aceite: menus equivalentes operando sem ação "dummy".

- [x] `P0-MAP-002` Implementar operações de limpeza de mapa em paridade.
  - Adicionar: remove item por ID (global), remove corpses, remove unreachable, clear invalid houses.
  - Integrar com `EditorSession` e histórico undo/redo quando aplicável.
  - Critério de aceite: cada ação executa, atualiza mapa/status e possui cobertura de teste unitário.
  - Status (2026-02-06): implementado no `EditorSession` + `Map` menu com ações undoable e cobertura em `tests/unit/logic_layer/test_map_cleanup_operations.py`.

- [x] `P0-SEARCH-003` Fechar paridade de busca avançada por mapa/seleção.
  - Expor ações de `Find Unique/Action/Container/Writeable` e equivalentes em seleção.
  - Corrigir `selection_only` em `FindItemDialog` para respeitar seleção ativa.
  - Critério de aceite: resultados mudam conforme escopo (mapa vs seleção) e filtros.
  - Status (2026-02-06): implementado no `map_search.py`, `find_item.py`, menus/ações da main window e testes unitários.

- [x] `P0-CONTEXT-004` Completar integração backend↔context menus (item/tile).
  - Substituir callbacks parciais dos canvases por callback set completo.
  - Implementar ações padrão pendentes em `context_menu_handlers.py` com ações transacionais.
  - Critério de aceite: ações de contexto editam mapa de fato e atualizam undo/redo.
  - Status (2026-02-06): callbacks completos conectados no canvas/software renderer com cobertura de testes.

- [x] `P0-BORDER-005` Evoluir Border Builder para autor de regras persistentes.
  - Permitir criar/editar/remover regras e salvar no armazenamento de brush definitions.
  - Aplicar reload seguro no `AutoBorderProcessor` sem reiniciar editor.
  - Critério de aceite: regra criada no UI impacta resultado de borderize.
  - Status (2026-02-06): Border Builder ganhou editor de regra por máscara (apply/clear), persistência em `brushes.overrides.json`, reload em runtime e carga automática no startup.

- [x] `P1-PREFS-006` Persistência real de preferências.
  - Ligar `PreferencesDialog` ao `ConfigurationManager`/config de projeto.
  - Remover TODOs de load/save e sincronizar defaults com runtime.
  - Critério de aceite: reiniciar app preserva ajustes de preferência.
  - Status (2026-02-06): persistência completa via `QSettings` (`UserSettings`) para todos campos do diálogo.

- [x] `P1-EXPORT-007` Concluir exportação OTMM no fluxo de UI.
  - Implementar `_export_otmm` no editor e dialog/opções mínimas de export.
  - Conectar com `core/io/otmm_saver.py` e validação de caminho/erro.
  - Critério de aceite: menu exporta `.otmm` válido para mapa de teste.
  - Status (2026-02-06): exportação consolidada para mapa OTMM completo via `core/io/otmm_saver.py` com validação de caminho/erro no fluxo de UI.

- [ ] `P1-UIUX-008` Migrar UI para iconografia própria (sem emojis).
  - Criar pacote de ícones (`resources/icons`) para ações, ferramentas e categorias.
  - Substituir labels com emoji em menus, dialogs, status widgets e tooltips.
  - Critério de aceite: interface usa ícones consistentes e sem emoji-format icon.
  - Status parcial (2026-02-06): labels/ações com emoji removidas dos módulos ativos de UI; pendente consolidar pacote dedicado de ícones próprios.

- [ ] `P1-UX-009` Paridade de Toolbars/Docks e integração moderna.
  - Ajustar builder para expor `menu_file/menu_edit` e ativar ações modernas hoje órfãs.
  - Reforçar toolbar de brushes/indicators com assets reais e estados sincronizados.
  - Critério de aceite: todas ações modernas aparecem no menu correto e executam.
  - Status parcial (2026-02-06): `menu_file/menu_edit/menu_help` agora são expostos no builder, ativando hooks do Modern UX.

- [ ] `P2-QA-010` Endurecimento de qualidade, performance e validação final.
  - Adicionar testes de integração UI↔session para features críticas.
  - Rodar `quality_lf.sh`, otimizar gargalos de cache/IO das ferramentas de quality.
  - Executar workflows locais equivalentes ao CI e anexar relatório final.
  - Critério de aceite: pipeline verde e tempo de quality reduzido de forma mensurável.
  - Status parcial (2026-02-06): `quality_lf.sh` executado em dry-run com cache ativo, Jules local validado (`status=ok`) e testes `tests/ui` + `tests/unit` verdes.

## Progresso executado (2026-02-06)
- Menus/actions/handlers implementados para `Preferences`, `Reload Data`, `Export Tilesets`, `Extensions`, `Goto Website`, `Export OTMM`.
- Menus `Search` e `Selection` adicionados para aproximar a estrutura legada C++.
- Compatibilidade de workflow Jules corrigida para Python 3.10 (`datetime.UTC` fallback em scripts).
- Validação local concluída:
  - `python -m pytest -q py_rme_canary/tests/ui` -> 11 passed
  - `python -m pytest -q py_rme_canary/tests/unit` -> 394 passed
  - `python -m pytest -q py_rme_canary/tests/unit/scripts/test_jules_runner.py` -> 7 passed
  - `bash py_rme_canary/quality-pipeline/quality_lf.sh --dry-run --timeout 900 --jobs 4`
  - `bash ./quality.sh --dry-run --skip-tests --skip-libcst --skip-sonarlint`

## Ordem de execução recomendada
1. `P0-MENU-001`
2. `P0-MAP-002`
3. `P0-SEARCH-003`
4. `P0-CONTEXT-004`
5. `P0-BORDER-005`
6. `P1-PREFS-006`
7. `P1-EXPORT-007`
8. `P1-UIUX-008`
9. `P1-UX-009`
10. `P2-QA-010`
