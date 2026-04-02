import random
import string

import pytest

from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import build_utterance_surface


def _surface(text: str):
    unit = ground_epistemic_input(
        InputMaterial(material_id=f"m-{abs(hash(text))}", content=text),
        SourceMetadata(
            source_id="fuzz-user",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    ).unit
    return build_utterance_surface(unit)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   \t \r\n",
        "?!?!!....",
        '"blarf zint',
        "(вставка",
        "`code-like",
        "blarf zint",
        "ну э-э я... не знаю",
        "blarf\n\nzint\t?",
        "blarf\u200bzint",
        "blarf🙂zint",
        "кириллица and latin MIXED",
        "a" * 800 + " ?!?!",
    ],
)
def test_surface_builder_does_not_crash_on_noisy_inputs(text: str) -> None:
    result = _surface(text)
    assert result.surface.normalization_log
    assert result.telemetry.attempted_paths
    if result.surface.raw_text:
        assert result.surface.reversible_span_map_present is True


def test_random_punctuation_clusters_keep_contract_honesty() -> None:
    random.seed(1337)
    baseline = _surface("blarf zint?").confidence
    punct = "!?.,:;—-"
    for _ in range(40):
        cluster = "".join(random.choice(punct) for _ in range(random.randint(2, 14)))
        text = f"blarf {cluster} zint"
        result = _surface(text)
        assert result.surface.reversible_span_map_present is True
        assert result.telemetry.token_count >= 1
        if any(ch in cluster for ch in "!?"):
            assert result.confidence <= baseline
            assert result.partial_known is True


def test_mixed_whitespace_generator_preserves_anchorability() -> None:
    random.seed(4242)
    alphabet = string.ascii_letters + "абвгд🙂"
    ws = [" ", "\t", "\n", "\r\n"]
    for _ in range(30):
        parts: list[str] = []
        for _ in range(random.randint(2, 8)):
            token = "".join(random.choice(alphabet) for _ in range(random.randint(1, 5)))
            parts.append(token)
            parts.append(random.choice(ws))
        text = "".join(parts)
        result = _surface(text)
        assert result.surface.reversible_span_map_present is True
        for token in result.surface.tokens:
            assert result.surface.raw_text[token.raw_span.start : token.raw_span.end] == token.raw_text
