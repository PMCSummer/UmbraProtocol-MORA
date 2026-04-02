from __future__ import annotations

from substrate.morphosyntax.models import (
    SyntaxDownstreamGateDecision,
    SyntaxHypothesisResult,
    SyntaxHypothesisSet,
    SyntaxTelemetry,
)


def build_syntax_telemetry(
    *,
    hypothesis_set: SyntaxHypothesisSet,
    source_lineage: tuple[str, ...],
    ambiguity_reasons: tuple[str, ...],
    attempted_paths: tuple[str, ...],
    downstream_gate: SyntaxDownstreamGateDecision,
    causal_basis: str,
) -> SyntaxTelemetry:
    all_hypotheses = hypothesis_set.hypotheses
    unresolved_count = sum(
        len(hypothesis.unresolved_attachments) for hypothesis in all_hypotheses
    )
    clause_count = sum(len(hypothesis.clause_graph.clauses) for hypothesis in all_hypotheses)
    agreement_count = sum(len(hypothesis.agreement_cues) for hypothesis in all_hypotheses)
    morphology_count = sum(len(hypothesis.token_features) for hypothesis in all_hypotheses)
    negation_count = sum(
        len(clause.negation_carrier_ids)
        for hypothesis in all_hypotheses
        for clause in hypothesis.clause_graph.clauses
    )
    segment_spans = tuple(
        (clause.raw_span.start, clause.raw_span.end)
        for hypothesis in all_hypotheses
        for clause in hypothesis.clause_graph.clauses
    )

    return SyntaxTelemetry(
        source_lineage=source_lineage,
        input_surface_ref=hypothesis_set.source_surface_ref,
        input_segment_spans=segment_spans,
        hypothesis_count=len(all_hypotheses),
        unresolved_edge_count=unresolved_count,
        clause_count=clause_count,
        agreement_cue_count=agreement_count,
        morphology_feature_count=morphology_count,
        negation_carrier_count=negation_count,
        ambiguity_reasons=ambiguity_reasons,
        attempted_paths=attempted_paths,
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
    )


def syntax_result_snapshot(result: SyntaxHypothesisResult) -> dict[str, object]:
    hypothesis_set = result.hypothesis_set
    return {
        "confidence": result.confidence,
        "partial_known": result.partial_known,
        "partial_known_reason": result.partial_known_reason,
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "hypothesis_set": {
            "source_surface_ref": hypothesis_set.source_surface_ref,
            "ambiguity_present": hypothesis_set.ambiguity_present,
            "no_selected_winner": hypothesis_set.no_selected_winner,
            "reason": hypothesis_set.reason,
            "hypotheses": tuple(
                {
                    "hypothesis_id": hypothesis.hypothesis_id,
                    "confidence": hypothesis.confidence,
                    "reason": hypothesis.reason,
                    "clause_graph": {
                        "clauses": tuple(
                            {
                                "clause_id": clause.clause_id,
                                "span": (clause.raw_span.start, clause.raw_span.end),
                                "boundary_kind": clause.boundary_kind.value,
                                "token_ids": clause.token_ids,
                                "negation_carrier_ids": clause.negation_carrier_ids,
                                "confidence": clause.confidence,
                            }
                            for clause in hypothesis.clause_graph.clauses
                        ),
                        "inter_clause_edges": hypothesis.clause_graph.inter_clause_edges,
                        "confidence": hypothesis.clause_graph.confidence,
                    },
                    "edges": tuple(
                        {
                            "edge_id": edge.edge_id,
                            "head_token_id": edge.head_token_id,
                            "dependent_token_id": edge.dependent_token_id,
                            "relation": edge.relation,
                            "clause_id": edge.clause_id,
                            "confidence": edge.confidence,
                        }
                        for edge in hypothesis.edges
                    ),
                    "unresolved_attachments": tuple(
                        {
                            "unresolved_id": unresolved.unresolved_id,
                            "dependent_token_id": unresolved.dependent_token_id,
                            "candidate_head_ids": unresolved.candidate_head_ids,
                            "relation_hint": unresolved.relation_hint,
                            "confidence": unresolved.confidence,
                            "reason": unresolved.reason,
                        }
                        for unresolved in hypothesis.unresolved_attachments
                    ),
                    "token_features": tuple(
                        {
                            "token_id": feature.token_id,
                            "span": (feature.raw_span.start, feature.raw_span.end),
                            "coarse_pos": feature.coarse_pos.value,
                            "number": feature.number.value,
                            "feature_map": feature.feature_map,
                            "confidence": feature.confidence,
                            "provenance": feature.provenance,
                        }
                        for feature in hypothesis.token_features
                    ),
                    "agreement_cues": tuple(
                        {
                            "cue_id": cue.cue_id,
                            "controller_token_id": cue.controller_token_id,
                            "target_token_id": cue.target_token_id,
                            "feature_name": cue.feature_name,
                            "status": cue.status.value,
                            "confidence": cue.confidence,
                            "reason": cue.reason,
                        }
                        for cue in hypothesis.agreement_cues
                    ),
                }
                for hypothesis in hypothesis_set.hypotheses
            ),
        },
        "telemetry": {
            "source_lineage": result.telemetry.source_lineage,
            "input_surface_ref": result.telemetry.input_surface_ref,
            "hypothesis_count": result.telemetry.hypothesis_count,
            "unresolved_edge_count": result.telemetry.unresolved_edge_count,
            "clause_count": result.telemetry.clause_count,
            "agreement_cue_count": result.telemetry.agreement_cue_count,
            "morphology_feature_count": result.telemetry.morphology_feature_count,
            "negation_carrier_count": result.telemetry.negation_carrier_count,
            "ambiguity_reasons": result.telemetry.ambiguity_reasons,
            "attempted_paths": result.telemetry.attempted_paths,
            "downstream_gate": {
                "accepted": result.telemetry.downstream_gate.accepted,
                "restrictions": result.telemetry.downstream_gate.restrictions,
                "reason": result.telemetry.downstream_gate.reason,
                "accepted_hypothesis_ids": result.telemetry.downstream_gate.accepted_hypothesis_ids,
                "rejected_hypothesis_ids": result.telemetry.downstream_gate.rejected_hypothesis_ids,
            },
        },
    }
