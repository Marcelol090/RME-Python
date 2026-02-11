# TODO Friends + Jules + Workflow (2026-02-06)

## Objetivo
Concluir a camada social do editor em PyQt6, reforçar integração Jules/Codex e estabilizar pipeline/workflows sem perder paridade existente.

## Plano (8 tarefas)

- [x] `TASK-01` Validar P0 de busca/context menu já implementado (`P0-SEARCH-003`, `P0-CONTEXT-004`).
- [x] `TASK-02` Implementar backend de amizades com persistência SQLite (`users`, `friendships`, `user_presence`).
- [x] `TASK-03` Implementar serviço de domínio para pedidos, aceites/rejeições, snapshot e presença.
- [x] `TASK-04` Implementar dock PyQt6 de amigos (status, pedidos pendentes, privacidade, ação de "View Map").
- [x] `TASK-05` Integrar backend social ao `QtMapEditor` (init, refresh, timer, sync com sessão live).
- [x] `TASK-06` Refinar prompts Jules com estratégia estruturada orientada a passos lineares.
- [x] `TASK-07` Otimizar `quality_lf.sh` para cenários de cache pesado e timeout.
- [x] `TASK-08` Rodar quality, suíte de testes, workflows locais e sincronização final de branches.

## Critérios de aceite

- Dock de amigos funcional no editor com estado online/offline e pedidos pendentes.
- Mudanças de amizade e presença persistem em banco local.
- Privacidade (`public`, `friends_only`, `private`) afeta exibição de atividade de mapa.
- P0 busca/contexto segue verde em testes direcionados.

## Incremental Update (2026-02-11)

- Identificada causa de explosão de sessões no Jules:
  - `generate-suggestions` criava sessão nova em toda execução sem tentativa de reuso.
- Planejada e implementada estratégia de pool local para reuso controlado:
  - pool por `source + branch + task`;
  - tamanho padrão `2` sessões;
  - rotação round-robin com `send_message`;
  - fallback para `create_session` quando sessão não existe/expira.
