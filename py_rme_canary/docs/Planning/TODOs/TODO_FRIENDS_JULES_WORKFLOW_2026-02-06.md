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

## Incremental Update (2026-02-11 - Track Sessions Hardening)

- Modelo recomendado atualizado para sessões fixas por trilha:
  - `JULES_LINEAR_SESSION_TESTS`
  - `JULES_LINEAR_SESSION_REFACTOR`
  - `JULES_LINEAR_SESSION_UIUX`
- `jules_runner.py` agora resolve automaticamente a variável correta por `--track`,
  com fallback compatível para `JULES_LINEAR_SESSION` apenas quando necessário.
- Workflows agendados separados por concorrência de trilha:
  - `jules-linear-tests-session`
  - `jules-linear-refactor-session`
  - `jules-linear-uiux-session`

## Incremental Update (2026-02-11 - Track Ops Commands)

- Added comandos operacionais específicos por trilha no `jules_runner.py`:
  - `track-session-status --track <tests|refactor|uiux>`
  - `track-sessions-status` (snapshot de todas as trilhas)
- Objetivo: facilitar acionamento e observabilidade por categoria (`refatoração`, `teste`, `design UI/UX`) sem risco de consultar sessão errada.
