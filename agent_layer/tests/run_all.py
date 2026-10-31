"""无 pytest 的最小测试运行器。"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from tests.test_daoql import test_causal_graph
from tests.test_tender import test_tender_state
from tests.test_agents import test_agents
from tests.test_reports import test_reports
from tests.test_sales_lifelong import test_sales_lifelong
from tests.test_learner_home import test_learner_home
from tests.test_roles import test_roles
from tests.test_head_teacher_ops import test_head_teacher_ops
from tests.test_cross_role_ops import test_cross_role_ops
from tests.test_institution_ops import test_institution_ops
from tests.test_workflow_ops import test_workflow_ops
from tests.test_workbench import test_multi_agent_workbench
from tests.test_advisor_router import test_advisor_router_and_scope
from tests.test_mentalization import test_c_end_mentalization_and_reflection
from tests.test_language_signals import (test_language_script_and_feature_spans, test_language_risk_routes_to_protection_without_diagnosis, test_language_never_updates_mastery_by_itself, test_language_api_contract)
from tests.test_agent_marketplace import test_expert_agent_marketplace
from tests.test_agent_runtime_integration import test_agent_runtime_integration
from tests.test_identity_gate import test_identity_gate_and_consent
from tests.test_safety_queue import test_safety_ticket_workflow
from tests.test_decision_loop import test_decision_loop_and_benchmark
from tests.test_cognitive_constructs import test_cognitive_constructs_and_api
from tests.test_ambient import test_ambient_mode_planner_and_feedback
from tests.test_tenant_isolation import (
    test_2026_projection_rules,
    test_physical_tenant_and_scope_isolation,
    test_sensitive_file_visibility,
)
from tests.test_knowledge_api import test_knowledge_database_api, test_knowledge_forest_snapshot
from tests.test_desktop_overlay import test_desktop_overlay_config_and_signals
from tests.test_triage_agent import (
    test_triage_routes_anxiety_to_psychology_not_subject,
    test_triage_routes_high_risk_to_safety,
    test_triage_routes_reflective_learning_turn_to_state_review,
    test_triage_routes_subject_question_to_subject_expert,
)
from tests.test_neuro_learning_evidence import (
    test_behavioral_proxy_requires_uncertainty_language,
    test_catalog_contains_behavior_and_brain_resources,
    test_direct_brain_reading_is_blocked,
    test_high_school_stage_has_behavior_and_development_data,
    test_neural_inference_is_not_enabled_at_runtime,
    test_university_stage_supports_adult_learning_analytics,
    test_working_memory_research_is_traceable,
)
from tests.test_neuro_learning_api import (
    test_neuro_learning_catalog_endpoint,
    test_neuro_learning_filters_and_claim_boundaries,
)
from tests.test_knowledge_context import (
    test_career_intent_returns_riasec_exploration_context,
    test_function_question_resolves_to_math_knowledge_node,
    test_major_query_loads_courses_and_competencies,
    test_no_match_does_not_invent_knowledge_node,
    test_subject_fallback_uses_units_when_topic_is_vague,
    test_tender_context_includes_knowledge_and_node_mastery,
)
from tests.test_tender_context import (
    test_ambient_reply_records_context_digest,
    test_comprehensive_prompt_requires_consistent_module_coverage,
    test_format_tender_context_includes_grounding_rules,
    test_llm_reply_strips_internal_agent_prefix,
    test_llm_prompt_receives_tender_context,
    test_tender_context_contains_preassessment_state_and_corrections,
    test_tender_context_exposes_longitudinal_modules,
    test_tender_context_sanitizes_non_finite_metrics,
    test_triage_routes_state_question_with_tender_context,
    test_state_review_precedes_subject_route,
)
from tests.test_preassessment import (
    test_attention_profile_and_correction_use_world_interface,
    test_explicit_consent_and_profile_persistence_without_raw_responses,
    test_item_inventory_and_estimated_time,
    test_big_five_pulse_tracks_change_from_baseline,
    test_function_consistency_is_tracked,
    test_neutral_profile_is_balanced_and_has_no_type_label,
    test_world_entry_uses_strict_two_attitudes_by_four_functions,
    test_profile_uses_support_hypotheses_not_defects,
    test_reverse_scored_conscientiousness,
)
from tests.test_preassessment_api import (
    test_preassessment_items_are_public,
    test_preassessment_submit_requires_identity_and_explicit_consent,
    test_big_five_pulse_api,
)
from tests.test_world_tree import test_world_tree_projects_roots_canopy_flowers_outcomes_and_shared_boundary
from tests.test_golden_bias import (
    test_creation_overweight_with_low_calibration_returns_calibration_probe,
    test_golden_bias_api_exists,
    test_golden_bias_inside_band_collects_quality_metrics,
    test_golden_bias_insufficient_evidence,
    test_learning_overweight_returns_output_probe,
    test_rhythm_periodicity_detects_known_cycle,
    test_rhythm_periodicity_refuses_sparse_series,
    test_rhythm_phase_detects_absorbing,
    test_rhythm_phase_detects_calibrating,
    test_rhythm_phase_detects_recovery_without_claiming_rest,
)
from tests.test_governance_phases import (
    test_cannot_skip_from_expert_council_to_public_autonomy,
    test_chain_accepts_only_commitments_after_federation,
    test_current_phase_is_offchain_expert_council,
    test_expert_council_rejects_any_chain_write,
    test_federation_opens_only_after_all_gates_pass,
    test_federation_requires_tanka_agreement_and_operational_gates,
    test_public_autonomy_requires_federated_phase_and_protections,
    test_raw_mental_and_health_data_never_go_on_chain,
)
from tests.test_metameta_cartographer import (
    test_life_tree_experience_mapper_labels_multiple_regions,
    test_life_tree_experience_mapper_uses_event_priors_without_text,
    test_objective_event_is_decomposed_into_subjective_nodes_without_mutation,
    test_subjective_experience_map_enters_tender_context,
    test_metameta_api_exposes_objective_to_subjective_decomposition,
)

from tests.test_mechanism_design import (
    test_bft_diverse_quorum_enters_human_review,
    test_bft_rejects_signer_claiming_multiple_sources,
    test_bft_requires_minimum_validator_roster,
    test_bft_rejects_three_signatures_from_one_source_group,
    test_bft_rejects_two_signatures_for_one_fault,
    test_bft_threshold_for_one_fault,
    test_reporting_incentive_diagnostic,
    test_shapley_additive_game,
    test_source_concentration_raises_review_priority_not_guilt,
)

TESTS = [
    test_causal_graph,
    test_tender_state,
    test_agents,
    test_reports,
    test_sales_lifelong,
    test_learner_home,
    test_roles,
    test_head_teacher_ops,
    test_cross_role_ops,
    test_institution_ops,
    test_workflow_ops,
    test_multi_agent_workbench,
    test_advisor_router_and_scope,
    test_c_end_mentalization_and_reflection,
    test_language_script_and_feature_spans,
    test_language_risk_routes_to_protection_without_diagnosis,
    test_language_never_updates_mastery_by_itself,
    test_language_api_contract,
    test_expert_agent_marketplace,
    test_agent_runtime_integration,
    test_identity_gate_and_consent,
    test_safety_ticket_workflow,
    test_decision_loop_and_benchmark,
    test_cognitive_constructs_and_api,
    test_ambient_mode_planner_and_feedback,
    test_knowledge_database_api,
    test_knowledge_forest_snapshot,
    test_desktop_overlay_config_and_signals,
    test_life_tree_experience_mapper_labels_multiple_regions,
    test_life_tree_experience_mapper_uses_event_priors_without_text,
    test_objective_event_is_decomposed_into_subjective_nodes_without_mutation,
    test_subjective_experience_map_enters_tender_context,
    test_metameta_api_exposes_objective_to_subjective_decomposition,
    test_triage_routes_anxiety_to_psychology_not_subject,
    test_triage_routes_subject_question_to_subject_expert,
    test_triage_routes_high_risk_to_safety,
    test_triage_routes_reflective_learning_turn_to_state_review,
    test_shapley_additive_game,
    test_reporting_incentive_diagnostic,
    test_bft_threshold_for_one_fault,
    test_bft_rejects_two_signatures_for_one_fault,
    test_bft_rejects_three_signatures_from_one_source_group,
    test_bft_diverse_quorum_enters_human_review,
    test_bft_requires_minimum_validator_roster,
    test_bft_rejects_signer_claiming_multiple_sources,
    test_source_concentration_raises_review_priority_not_guilt,
    test_current_phase_is_offchain_expert_council,
    test_expert_council_rejects_any_chain_write,
    test_cannot_skip_from_expert_council_to_public_autonomy,
    test_federation_requires_tanka_agreement_and_operational_gates,
    test_federation_opens_only_after_all_gates_pass,
    test_chain_accepts_only_commitments_after_federation,
    test_raw_mental_and_health_data_never_go_on_chain,
    test_public_autonomy_requires_federated_phase_and_protections,
    test_catalog_contains_behavior_and_brain_resources,
    test_high_school_stage_has_behavior_and_development_data,
    test_university_stage_supports_adult_learning_analytics,
    test_working_memory_research_is_traceable,
    test_direct_brain_reading_is_blocked,
    test_behavioral_proxy_requires_uncertainty_language,
    test_neural_inference_is_not_enabled_at_runtime,
    test_neuro_learning_catalog_endpoint,
    test_neuro_learning_filters_and_claim_boundaries,
    test_item_inventory_and_estimated_time,
    test_neutral_profile_is_balanced_and_has_no_type_label,
    test_world_entry_uses_strict_two_attitudes_by_four_functions,
    test_function_consistency_is_tracked,
    test_reverse_scored_conscientiousness,
    test_attention_profile_and_correction_use_world_interface,
    test_profile_uses_support_hypotheses_not_defects,
    test_big_five_pulse_tracks_change_from_baseline,
    test_explicit_consent_and_profile_persistence_without_raw_responses,
    test_preassessment_items_are_public,
    test_preassessment_submit_requires_identity_and_explicit_consent,
    test_big_five_pulse_api,
    test_tender_context_contains_preassessment_state_and_corrections,
    test_format_tender_context_includes_grounding_rules,
    test_triage_routes_state_question_with_tender_context,
    test_llm_prompt_receives_tender_context,
    test_ambient_reply_records_context_digest,
    test_comprehensive_prompt_requires_consistent_module_coverage,
    test_llm_reply_strips_internal_agent_prefix,
    test_tender_context_exposes_longitudinal_modules,
    test_tender_context_sanitizes_non_finite_metrics,
    test_state_review_precedes_subject_route,
    test_function_question_resolves_to_math_knowledge_node,
    test_subject_fallback_uses_units_when_topic_is_vague,
    test_no_match_does_not_invent_knowledge_node,
    test_tender_context_includes_knowledge_and_node_mastery,
    test_major_query_loads_courses_and_competencies,
    test_career_intent_returns_riasec_exploration_context,
    test_physical_tenant_and_scope_isolation,
    test_sensitive_file_visibility,
    test_2026_projection_rules,
    test_world_tree_projects_roots_canopy_flowers_outcomes_and_shared_boundary,
    test_golden_bias_insufficient_evidence,
    test_golden_bias_inside_band_collects_quality_metrics,
    test_learning_overweight_returns_output_probe,
    test_creation_overweight_with_low_calibration_returns_calibration_probe,
    test_golden_bias_api_exists,
    test_rhythm_periodicity_detects_known_cycle,
    test_rhythm_periodicity_refuses_sparse_series,
    test_rhythm_phase_detects_recovery_without_claiming_rest,
    test_rhythm_phase_detects_absorbing,
    test_rhythm_phase_detects_calibrating,
]

if __name__ == "__main__":
    for test in TESTS:
        test()
        print("ok", test.__name__)
    print(f"passed {len(TESTS)} tests")
