# Stage 5 GUI Plan (PySide6, русская презентация)

## Назначение
GUI остаётся presentation/inspection слоем над Stage 5 harness. Он не добавляет когнитивную логику и не изменяет core subject.

## Что GUI теперь показывает
- Символическую сцену `A/B/стена/апертура`.
- Причинную цепочку `W01..W06 -> Response -> Affordance -> Actuator -> Verification`.
- Пошаговую timeline-модель (15 шагов) с явными статусами:
  - `trace_derived`
  - `inferred_from_stage5_summary`
  - `not_exposed`
  - `blocked`
  - `skipped`
  - `failed`
  - `verified`
- Разделение:
  - `offer candidate` vs `invocation request` vs `world actuator invocation`.
  - `passive scenario packets` vs `causal post-invocation packets`.
  - `transfer result` vs `completion verification`.
- Anti-shortcut checklist на базе Stage 5 falsifier summary.
- Developer inspector (raw trace JSON).

## Управление (GUI controls)
- Выбор сценария.
- Выбор режима: наблюдение / выполнение внешнего действия.
- Кнопки: запуск, сброс.
- Навигация по timeline: к первому, назад, вперёд, к последнему.
- Play/Pause.
- Скорость воспроизведения: медленно / нормально / быстро.
- Индикатор текущего шага `Шаг X / N`.
- Переключатель режима разработчика.
- Отдельный переключатель `Показать eval_only` (доступен только в режиме разработчика).

## Граница eval_only
- Публичный режим: `eval_only` не показывается.
- Dev mode без `Показать eval_only`: raw trace без eval-only полей.
- Dev mode + `Показать eval_only`: eval-only появляется только в инспекторе и помечается как audit-only.
- Eval-only поля не используются для рендеринга решения, статуса completion или anti-shortcut результата.

## No-exec vs exec
- No-exec: `world_actuator_invoked=False`, `transfer_result=not_attempted`, `completion=False`.
- Exec: actuator может быть вызван только при явном флаге и валидной цепочке Stage 5.

## Что GUI не доказывает
- Нет claim’а автономной торговли.
- Нет claim’а экономической агентности.
- Нет claim’а natural-language negotiation.
- Нет claim’а subject motor-control competence.
- Нет claim’а consciousness/ToM/social cognition.
- Нет claim’а learning/update execution.

## Запуск
- `python tools/symbolic_trade_gui.py --help`
- `python tools/symbolic_trade_gui.py --scenario successful_scripted_exchange_cycle --dry-run`
- `python tools/symbolic_trade_gui.py --scenario successful_scripted_exchange_cycle --execute-world-actuator --dry-run`
- `python tools/symbolic_trade_gui.py --scenario successful_scripted_exchange_cycle --timeline-dry-run`

## Известные ограничения
- Символическая визуализация, не физический симулятор.
- World actuator остаётся harness/world-side механизмом.
- Сравнительная панель shortcut vs MORA — explanatory panel, не benchmark-доказательство.
