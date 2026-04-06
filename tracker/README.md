# Roadmap Research Tracker v4 — PySide6

Это не косметический порт старого Tkinter-трекера, а новая база под **research-aware roadmap tracker** для цифрового субъекта.

## Единый вердикт по изменениям трекера

Старый Tkinter-трекер был нормален как:
- список фаз,
- статусы,
- заметки,
- summary,
- claim ladder.

Но он слабо подходил для трёх вещей, которые стали критичными:
- **граф причинных зависимостей**,
- **knowledge/evidence layer**, где у фазы есть не просто описание, а mechanistic foundation,
- **карточка исследовательской честности**, где видно observables, falsifiers, forbidden shortcuts, biological analogy/support и maturity.

Поэтому новая версия делает следующее:

### 1. Переход с Tkinter на PySide6
Причина:
- нужен более живой desktop UI,
- нужен нормальный графический слой,
- нужен более современный и расширяемый shell.

### 2. Переход от “phase list + notes” к knowledge-aware модели
У каждой фазы теперь есть `knowledge_card`, где можно хранить:
- functional role,
- why exists,
- inputs / outputs,
- authority,
- forbidden shortcuts,
- uncertainty policy,
- observables,
- failure modes,
- falsifiers,
- tests,
- biological analogy,
- biological support,
- evidence strength,
- provenance,
- disciplines,
- alternative models,
- evidence ids.

### 3. Несколько семанических слоёв графа
Граф больше не трактуется как один универсальный рисунок.
Есть слои:
- causal / conceptual,
- computational / workflow,
- provenance / evidence,
- validation / falsification.

### 4. Типизированные узлы и рёбра
Узлы:
- phase,
- mechanism,
- evidence,
- validation_protocol,
- failure_mode,
- constraint,
- capability,
- biological_process,
- governance.

Рёбра:
- causes,
- enables,
- requires,
- tests,
- contradicts,
- grounds,
- generated_by,
- implemented_by,
- measured_by,
- supports,
- challenged_by,
- refines,
- abstracts_to,
- belongs_to_scope,
- blocks_claim,
- forbids_shortcut.

### 5. Разделение claim-state и maturity
Чтобы не путать “идея”, “спека”, “код” и “поддержано данными”, добавлены:
- `claim_state`,
- `maturity`.

### 6. Evidence tab
Появился отдельный слой evidence/provenance с возможностью хранить:
- citation,
- url,
- summary,
- supports,
- challenges,
- provenance,
- updated_at.

### 7. Сводка теперь показывает пробелы knowledge coverage
Summary показывает, где у фаз нет:
- observables,
- falsifiers,
- forbidden shortcuts,
- biological support при наличии analogy.

## Что реализовано в коде

### Архитектура
- `roadmap_tracker/model.py` — data model, миграция старых схем, knowledge layer, graph model.
- `roadmap_tracker/app.py` — PySide6 UI.
- `main.py` — точка входа.

### Что поддерживает UI
- загрузка JSON roadmap,
- импорт legacy DOCX,
- сохранение JSON,
- экспорт CSV,
- таблица фаз с фильтрами,
- редактирование фазы,
- knowledge-card editor,
- governance editor,
- graph tab с узлами и рёбрами,
- evidence tab,
- claim ladder,
- summary,
- selection inspector в dock panel.

## Ограничения текущей версии

Это **рабочий фундамент**, а не финальная IDE.
Пока не сделано:
- SQLite backend,
- полноценный multi-view architecture browser,
- rich edge editing с batch operations,
- отдельные nested internal mechanism maps для micro-pipelines внутри фазы,
- graph persistence history / undo-redo,
- full model/view abstraction поверх Qt item models.

## Установка

```bash
pip install PySide6 python-docx
```

## Запуск

```bash
python main.py
```

## Формат данных

Новая схема — `schema_version = 4`.
Старые `schema_version <= 3` автоматически мигрируются в память при загрузке.

## Следующий разумный шаг

Если трекер приживётся, следующий этап лучше делать так:
- storage → SQLite,
- graph analytics → NetworkX,
- UI shell оставить на PySide6,
- knowledge cards и evidence перевести из JSON-кусков в более строгую схему хранения.
