# TODO (Expensive) — Paridade + Qualidade (base: RME legacy C++)

**Última atualização:** 2026-01-05  
**Base:** [IMPLEMENTATION_TODO.md](IMPLEMENTATION_TODO.md), [ARCHITECTURE.md](ARCHITECTURE.md), [QUALITY_CHECKLIST.md](QUALITY_CHECKLIST.md)  
**Objetivo:** elevar o projeto de **A- (88/100)** para **A (95/100+)**, implementando faltas reais e removendo ambiguidade/legado morto — sempre **ancorando a lógica no RME legacy C++** (pasta `source/`).

---

> ⚠️ **Redundância removida:**
> The master checklist is now in [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md). This file contains only high-priority technical debt and parity details. For actionable status, use the master checklist.

## 0) Regras (não-negociáveis)

- **Fluxo de dependências:** `core/` ← `logic_layer/` ← `vis_layer/`.
- **UI não entra** em `core/`/`logic_layer/`.
- Toda feature portada do C++ precisa de:
  - referência explícita no legado (arquivo/função/trecho)
  - critérios de aceite (o que provar que “bate com o legacy”)
  - pelo menos 1 teste unitário (quando aplicável) e/ou smoke test

---

## 1) EPIC P0 — Mirror Drawing (paridade real com o legacy)

### Contexto
No legacy, “Mirror drawing” é aplicado **na hora de montar a lista de posições a desenhar**, duplicando posições com a posição espelhada e removendo duplicatas.

**Referências (legacy C++):**
- `source/gui.h` — estado do mirror + API pública (`IsMirrorDrawingEnabled`, `ToggleMirrorDrawingAtCursor`, `SetMirrorAxisFromCursor`, etc.)
- `source/gui.cpp` — regras: habilita/desabilita, valida cursor, set axis (X/Y + valor)
- `source/map_display.cpp` — regra principal de espelhamento durante desenho:
  - `getMirroredPosition` e `unionWithMirrored` (dedupe + validação)
  - aplica para doodad/door/border/no-borders

**Estado atual (Python):**
- UI/state já existem em `py_rme_canary/vis_layer/qt_app.py` (ações + shortcuts + status)
- O espelhamento existe **embutido** em `py_rme_canary/vis_layer/ui/map_canvas.py` dentro de `_paint_footprint_at` (há dedupe e bounds check)
- `py_rme_canary/logic_layer/mirroring.py` é um **stub** com docstring (e docstring está desalinhada: fala de NumPy/metadados, mas a necessidade real é espelhar posições/footprints)

### Objetivo
Centralizar e padronizar o algoritmo de mirror do Python para ser **1:1 com o C++** (inclusive dedupe/validação), e remover o stub enganoso.

### Tarefas
1. **Reescrever `logic_layer/mirroring.py` para o caso real (posições do mapa)**
   - Criar funções puras:
     - `mirrored_position(x: int, y: int, *, axis: str, axis_value: int) -> tuple[int,int] | None`
     - `union_with_mirrored(positions: Iterable[tuple[int,int,int]], *, axis: str, axis_value: int) -> list[tuple[int,int,int]]`
       - dedupe por chave (x,y,z)
       - não inclui posições inválidas
       - não inclui `mirror == original`
   - Remover docstring de “NumPy metadata” (não condiz com o projeto).

2. **Usar a util do `logic_layer/mirroring.py` no `MapCanvasWidget`**
   - Trocar a implementação local `mirrored()` por chamada única.
   - Garantir comportamento igual ao C++:
     - mesma fórmula: `x' = 2*axis - x` (axis X) e `y' = 2*axis - y` (axis Y)
     - não duplicar se repetido
     - ignorar fora do mapa

3. **Portar o detalhe de “mirror só funciona se axis está setado”**
   - No C++: `IsMirrorDrawingEnabled()` exige `mirror_drawing_enabled && HasMirrorAxis()`.
   - No Python: alinhar `mirror_enabled` + `has_mirror_axis()` para que o “enabled” real seja coerente.

4. **Testes**
   - Criar `py_rme_canary/logic_layer/test_mirroring.py` (ou equivalente) com casos:
     - axis X/Y
     - mirror == original (não duplica)
     - fora do mapa (retorna None / não inclui)
     - dedupe preserva conjunto (mesmo input repetido)

### Critérios de aceite
- Mesmo comportamento do algoritmo do C++ em `unionWithMirrored` (dedupe + validações).
- Não existem mais stubs enganosos sobre mirror (docstring alinhada).
- Smoke: desenhar com mirror ligado produz exatamente o dobro de footprints quando aplicável.

### Estimativa
- 2–4h (inclui testes e refactor local)

---

## 2) EPIC P0 — data_layer/ (deprecar de verdade e tirar da frente) - ✅ CONCLUÍDO

### Contexto
`py_rme_canary/data_layer/` foi removido em 2026-01-18 pois duplicava `core/`.

### Tarefas
1. **Decisão única:**
   - remover por completo (preferido se ninguém usa e você quer “repo clean”)

2. **Bloquear uso por acidente**
   - Em `py_rme_canary/data_layer/__init__.py`, emitir warning explícito (se mantiver) dizendo “deprecated, use core/”.

3. **Auditar imports**
   - Garantir que `py_rme_canary/` não importa `data_layer/` (exceto ferramentas explicitamente permitidas).

4. **Atualizar docs**
   - Atualizar [ARCHITECTURE.md](ARCHITECTURE.md) e [QUALITY_CHECKLIST.md](QUALITY_CHECKLIST.md) para refletir a decisão final.

### Critérios de aceite
- Não existe ambiguidade: ou `data_layer/` sumiu, ou está em `_legacy/` com aviso.
- `grep` por `from py_rme_canary.data_layer` retorna vazio (exceto scripts whitelisted).

### Estimativa
- 30–90min

---

## 3) EPIC P0 — brushes.py (remover/deprecar com segurança) - ✅ CONCLUÍDO

### Contexto
[brushes.py](file:///py_rme_canary/logic_layer/brushes.py) e [brush_factory.py](file:///py_rme_canary/logic_layer/brush_factory.py) foram removidos em 2026-01-18.
`Brush.apply()` com `NotImplementedError` não era usado.

### Tarefas
1. **Encontrar usos reais**
   - `grep` por imports/usos de `logic_layer.brushes`.

2. **Escolher estratégia**
   - (A) Remover arquivo (se não usado).
   - (B) Mover para `logic_layer/_deprecated/` com aviso e timeline de remoção.
   - (C) Converter para `Protocol` (se quiser manter “contrato” tipado), sem NotImplemented.

3. **Atualizar documentação**
   - [ARCHITECTURE.md](ARCHITECTURE.md) deve apontar `brush_definitions.py` como canonical.

### Critérios de aceite
- Nenhum `NotImplementedError` fica em caminho “normal” de execução.
- Import/uso de brush é único (um caminho oficial).

### Estimativa
- 30–120min

---

## 4) EPIC P0 — Padronizar testes - ✅ CONCLUÍDO

### Contexto
Nenhum arquivo `_minimal_test.py` encontrado na árvore. Todos os testes seguem `test_*.py`.

### Tarefas
- [x] Identificar e renomear testes fora do padrão.
1. Definir padrão único:
   - opção recomendada: `test_*.py` para pytest.

2. Renomear:
   - `py_rme_canary/**/_minimal_test.py` → `py_rme_canary/**/test_*.py` (nome específico por módulo)

3. Ajustar comandos em [QUALITY_CHECKLIST.md](QUALITY_CHECKLIST.md)

### Critérios de aceite
- `python -m pytest py_rme_canary/` descobre todos os testes.

### Estimativa
- 30–90min

---

## 5) EPIC P1 — Isolar ou remover UI experimental (Tkinter + PySide6)

### Contexto
`py_rme_canary/vis_layer/tk_app.py`, `map_model.py` e `io_worker.py` são caminhos alternativos (Tk/PySide6) que não são o “produto principal” (PyQt6).

### Tarefas
1. **Escolher política**
   - (A) mover para `py_rme_canary/vis_layer/_experimental/` + README curto “não mantido”.
   - (B) remover do repositório.

2. **Garantir que `qt_app.py` não depende disso**

3. **Docs**
   - Em [ARCHITECTURE.md](ARCHITECTURE.md), deixar claro: `QtMapEditor` é canonical.

### Critérios de aceite
- Nenhum import PySide6/Tk aparece no caminho “principal” (`qt_app.py` + `vis_layer/ui/*`).

### Estimativa
- 30–120min

---

## 6) EPIC P1 — Auditoria OTBM: atributos e paridade com legacy

### Contexto
OTBM é sensível. O core já carrega/salva, mas precisamos garantir que atributos principais batem com o legado.

**Referências (legacy C++):**
- `source/iomap_otbm.cpp` / `source/iomap_otbm.h` (tipos/atributos do formato)
- `source/item_attributes.h` / `source/item_attributes.cpp` (attribute map)
- `source/live_socket.cpp` (serialização de tile attrs)

### Tarefas
1. **Checklist de atributos por item/tile**
   - mapear quais attrs o legacy suporta (ACTION_ID, UNIQUE_ID, TEXT, DESC, TELE_DEST, COUNT/CHARGES, ATTRIBUTE_MAP, etc.)

2. **Comparar com Python**
   - `py_rme_canary/core/io/otbm_loader.py`
   - `py_rme_canary/core/io/otbm_saver.py`

3. **Implementar faltas**
   - leitura/escrita de `OTBM_ATTR_ATTRIBUTE_MAP` (se ainda não completo)
   - roundtrip (load→save) preservando atributos

4. **Tests de roundtrip**
   - adicionar 1–2 arquivos sintéticos focados em atributos (sem sprites) ou gerar em memória.

### Critérios de aceite
- Roundtrip não perde atributos relevantes.
- Loader não quebra em mapas com `ATTRIBUTE_MAP`.

### Estimativa
- 4–10h (depende do estado atual do saver)

---

## 7) EPIC P1 — Paridade de “tiles_to_draw” e bordas (brush footprint)

### Contexto
O C++ decide tiles de draw/border e depois aplica mirror.

**Referência (legacy C++):** `source/map_display.cpp` (caminhos: `needBorders`, `oneSizeFitsAll`, “no borders”, door, doodad)

**Python atual:** `vis_layer/ui/map_canvas.py` usa `iter_brush_offsets` + `iter_brush_border_offsets`.

### Tarefas
1. Validar se o footprint do Python é idêntico ao legacy
   - square vs circle
   - tamanho (inclusive edge cases: size=0/1)
   - anel de borda (`tilestoborder`)

2. Criar testes puros em `logic_layer/` para footprint
   - se necessário: mover `iter_brush_offsets`/`iter_brush_border_offsets` para `logic_layer/geometry.py` (ou similar) e reexportar.

### Critérios de aceite
- Para sizes N e shapes, o conjunto de offsets bate com o legacy (mesma cardinalidade e simetria).

### Estimativa
- 2–6h

---

## 8) EPIC P2 — “Polish” de qualidade (sem mudar UX)

- Adicionar `ruff`/`mypy` como checks opcionais (sem travar fluxo inicial).
- Consolidar warnings/erros em exceptions tipadas (onde fizer sentido).
- Criar um `CONTRIBUTING.md` curto apontando para os 3 documentos.

---

## 9) Ordem recomendada (para chegar em A rápido)

1. P0 Mirror Drawing (limpa stub + centraliza lógica)
2. P0 data_layer cleanup
3. P0 brushes.py cleanup
4. P0 padronização de testes
5. P1 isolamento/remocão experimental UI
6. P1 auditoria OTBM attrs
7. P1 footprint/borders parity

---

## 10) Observações práticas (como “portar do C++” de forma segura)

- Sempre comece pelo trecho do legacy que define a regra (ex.: `unionWithMirrored` em `source/map_display.cpp`).
- Faça um equivalente puro em `logic_layer/`.
- Só depois plugue na UI (`vis_layer/`).
- Escreva testes em cima do puro, não da UI.

