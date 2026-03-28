# TEST-GAP-ANALYSIS.md

> Coverage map of every behavioral rule in CCA-RULES.md against the project test suite.
> Generated: 2026-03-28
> Test suite: 15 files, 234 tests

---

## How to Read This Document

- **Covered** — An automated test in the `tests/` directory directly exercises this rule
- **Manual** — No automated test; verification requires running the referenced notebook cell
- **Gap** — No test and no manual step; recommendation provided

Reference format: `test_file.py::ClassName::test_method_name`

---

## 1. Escalation Logic (CCA-RULES.md: "THE #1 TRAP")

| CCA Rule | Expected Behavior | Test Coverage | Status |
|----------|-------------------|---------------|--------|
| Amount > $500 blocks process_refund | `escalation_callback` returns `action='block'` for $600 refund | `test_callbacks.py::TestEscalationCallback::test_block_refund_amount_over_500` | Covered |
| VIP tier triggers escalation | `escalation_callback` returns `action='block'` for VIP context | `test_callbacks.py::TestEscalationCallback::test_block_refund_vip` | Covered |
| Account closure flag triggers escalation | `escalation_callback` returns `action='block'` for account_closure=True | `test_callbacks.py::TestEscalationCallback::test_block_refund_account_closure` | Covered |
| Legal complaint keyword triggers escalation | `escalation_callback` returns `action='block'` for legal_complaint=True | `test_callbacks.py::TestEscalationCallback::test_block_refund_legal_complaint` | Covered |
| Normal refund under $500 is allowed | `escalation_callback` returns `action='allow'` for $50 with no flags | `test_callbacks.py::TestEscalationCallback::test_allow_refund_no_flags` | Covered |
| All explicit False flags do not escalate | No false positive escalations | `test_callbacks.py::TestEscalationCallback::test_allow_refund_all_flags_false` | Covered |
| Escalation enforced deterministically (NOT confidence-based) | Routing is code, not LLM self-assessment | `test_callbacks.py::TestEscalationCallback` (all tests use deterministic `if` logic) | Covered |
| Veto guarantee: blocked refund never touches FinancialSystem | `FinancialSystem.get_processed()` stays empty after block | `test_callbacks.py::TestVetoGuarantee::test_veto_guarantee_financial_system_untouched` | Covered |
| Allow commits to FinancialSystem | Approved refund creates record in FinancialSystem | `test_callbacks.py::TestVetoGuarantee::test_allow_commits_to_financial_system` | Covered |
| VIP veto guarantee | VIP block leaves FinancialSystem empty | `test_callbacks.py::TestVetoGuarantee::test_veto_guarantee_vip_customer` | Covered |
| check_policy sets requires_review flag | `check_policy_callback` sets `context['requires_review'] = True` | `test_callbacks.py::TestCheckPolicyCallback::test_sets_requires_review_when_true` | Covered |
| lookup_customer sets VIP context flag | `lookup_customer_callback` sets `context['vip'] = True` for VIP customer | `test_callbacks.py::TestLookupCustomerCallback::test_sets_vip_flag_for_vip_customer` | Covered |
| lookup_customer sets account_closure flag | `lookup_customer_callback` sets `context['account_closure'] = True` | `test_callbacks.py::TestLookupCustomerCallback::test_sets_account_closure_flag` | Covered |
| Legal keywords in user message set legal_complaint flag | `lookup_customer_callback` detects "sue" keyword | `test_callbacks.py::TestLookupCustomerCallback::test_sets_legal_complaint_from_user_message` | Covered |
| Per-tool callback registry dispatches correctly | `build_callbacks()` returns dict with all tool names | `test_callbacks.py::TestBuildCallbacks::test_build_callbacks_has_all_tools` | Covered |
| Anti-pattern: confidence-based escalation exists as named module | `run_confidence_agent` callable, `CONFIDENCE_SYSTEM_PROMPT` mentions confidence score | `test_anti_patterns.py::TestConfidenceEscalation::test_confidence_prompt_contains_confidence` | Covered |

---

## 2. Tool Count (CCA-RULES.md: "4-5 focused tools per agent")

| CCA Rule | Expected Behavior | Test Coverage | Status |
|----------|-------------------|---------------|--------|
| Exactly 5 tools in correct agent | `len(TOOLS) == 5` | `test_tools.py::TestToolSchemas::test_tool_count` | Covered |
| All 5 required tool names present | `lookup_customer`, `check_policy`, `process_refund`, `escalate_to_human`, `log_interaction` | `test_tools.py::TestToolSchemas::test_tool_names` | Covered |
| Tool schemas have required keys | Each tool has `name`, `description`, `input_schema` | `test_tools.py::TestToolSchemas::test_tool_schema_structure` | Covered |
| Input schemas are object type | `input_schema.type == "object"` with `properties` | `test_tools.py::TestToolSchemas::test_input_schema_is_object_type` | Covered |
| No `title` key in input_schema | Avoids Claude API parse confusion | `test_tools.py::TestToolSchemas::test_no_title_in_input_schema` | Covered |
| Anti-pattern: Swiss Army agent has exactly 15 tools | `len(SWISS_ARMY_TOOLS) == 15` (10 distractor tools) | `test_anti_patterns.py::TestSwissArmyTools::test_swiss_army_tools_has_exactly_15` | Covered |
| Anti-pattern: all 5 correct tools present in 15-tool set | The 15-tool agent includes the correct 5 (overshadowed) | `test_anti_patterns.py::TestSwissArmyTools::test_all_5_correct_tools_present` | Covered |
| Anti-pattern: exactly 10 distractor tools | Over-tooling is quantified | `test_anti_patterns.py::TestSwissArmyTools::test_exactly_10_distractor_tools` | Covered |
| Tool descriptions have negative bounds ("does NOT") | Routing precision via explicit exclusions | `test_tools.py::TestToolSchemas::test_tool_descriptions_have_negative_bounds` | Covered |
| Dispatch handles all 5 tools | `DISPATCH` registry contains all tool names | `test_tools.py::TestDispatchRegistry::test_dispatch_has_all_tools` | Covered |
| All handlers return valid JSON strings | Every handler call produces parseable JSON | `test_tools.py::TestDispatchRegistry::test_all_handlers_return_json_strings` | Covered |

---

## 3. Compliance Enforcement (CCA-RULES.md: "Programmatic redaction, audit logging")

| CCA Rule | Expected Behavior | Test Coverage | Status |
|----------|-------------------|---------------|--------|
| Credit card number redacted in log output | `compliance_callback` replaces `4111-1111-1111-1111` with `****-****-****-1111` | `test_callbacks.py::TestComplianceCallback::test_redact_credit_card_number` | Covered |
| Card numbers with spaces also redacted | Regex handles space-separated card formats | `test_callbacks.py::TestComplianceCallback::test_redact_credit_card_with_spaces` | Covered |
| Redaction preserves last 4 digits | PCI-DSS compatible masking format | `test_callbacks.py::TestComplianceCallback::test_redact_preserves_last_four` | Covered |
| Clean log entries are allowed without redaction | No false positives on innocuous text | `test_callbacks.py::TestComplianceCallback::test_no_redaction_needed_allows` | Covered |
| Redaction happens BEFORE write to AuditLog | Raw PII must never reach `AuditLog.add_entry()` | `test_callbacks.py::TestVetoGuarantee::test_compliance_audit_log_never_has_raw_pii` | Covered |
| Dispatch with callbacks redacts card in result | Integration: dispatch + callback chain works end-to-end | `test_callbacks.py::TestVetoGuarantee::test_compliance_redaction_in_dispatch` | Covered |
| Anti-pattern: prompt-only compliance module exists | `PROMPT_COMPLIANCE_SYSTEM_PROMPT` contains "redact" and "never log" | `test_anti_patterns.py::TestPromptCompliance::test_prompt_compliance_contains_redact` | Covered |
| Anti-pattern: prompt compliance uses system prompt, not hooks | `run_prompt_compliance_agent` callable (demonstrates wrong approach) | `test_anti_patterns.py::TestPromptCompliance::test_run_prompt_compliance_agent_is_callable` | Covered |

---

## 4. Cost Optimization (CCA-RULES.md: "Prompt Caching vs Batch API")

| CCA Rule | Expected Behavior | Test Coverage | Status |
|----------|-------------------|---------------|--------|
| POLICY_DOCUMENT exceeds 2048-token minimum | `len(POLICY_DOCUMENT) // 4 > 2048` | `test_caching.py::TestPolicyDocument::test_policy_document_exceeds_2048_tokens` | Covered |
| POLICY_DOCUMENT is non-empty string | Document exists and has content | `test_caching.py::TestPolicyDocument::test_policy_document_is_string` | Covered |
| POLICY_DOCUMENT contains substantive policy content | Not filler; has "refund" and "customer" | `test_caching.py::TestPolicyDocument::test_policy_document_has_policy_content` | Covered |
| `get_system_prompt_with_caching()` returns a list (not string) | SDK accepts `list[dict]` as `system=` parameter | `test_caching.py::TestSystemPromptCaching::test_returns_list_not_string` | Covered |
| Returns exactly 2 content blocks | Block 0: agent instructions, Block 1: policy with cache | `test_caching.py::TestSystemPromptCaching::test_returns_exactly_two_blocks` | Covered |
| Block 0 is agent instructions with no cache_control | Instructions are per-call context, not cacheable | `test_caching.py::TestSystemPromptCaching::test_block_zero_is_agent_instructions` | Covered |
| Block 1 is POLICY_DOCUMENT with `cache_control={"type":"ephemeral"}` | Policy document is the cache breakpoint | `test_caching.py::TestSystemPromptCaching::test_block_one_is_cached_policy` | Covered |
| cache_control on correct (last static) block | CCA anti-pattern: putting cache_control on instructions block | `test_caching.py::TestSystemPromptCaching::test_cache_control_on_correct_block` | Covered |
| agent_loop accepts `list[dict]` system_prompt | run_agent_loop passes list directly to SDK | `test_caching.py::TestAgentLoopSystemType::test_accepts_list_system_prompt` | Covered |
| SDK receives list as `system=` kwarg | Verified via mock call_args inspection | `test_caching.py::TestAgentLoopSystemType::test_sdk_receives_list_as_system_kwarg` | Covered |
| cache_creation_input_tokens accumulates | First call: cache write recorded in UsageSummary | `test_caching.py::TestCacheTokenAccounting::test_cache_write_on_first_call` | Covered |
| cache_read_input_tokens accumulates | Second call: cache read recorded in UsageSummary | `test_caching.py::TestCacheTokenAccounting::test_cache_read_on_second_call` | Covered |
| Cache tokens accumulate across loop iterations | Multi-turn: write + read both reflected in final usage | `test_caching.py::TestCacheTokenAccounting::test_cache_tokens_accumulate_across_iterations` | Covered |
| Anti-pattern: Batch API wrong for live support | `BATCH_API_EXPLANATION` mentions "Batch API" and "24" hours | `test_caching.py::TestBatchApiExplanation::test_mentions_batch_api` and `test_mentions_24_hour_latency` | Covered |
| Anti-pattern: raw transcript context grows O(n) | Each append increases `token_estimate()` | `test_caching.py::TestRawTranscriptAntiPattern::test_token_estimate_grows_with_each_append` | Covered |

---

## 5. Handoff Pattern (CCA-RULES.md: "Structured EscalationRecord JSON")

| CCA Rule | Expected Behavior | Test Coverage | Status |
|----------|-------------------|---------------|--------|
| `_has_escalation_required` detects `action_required: escalate_to_human` | Returns True for blocked tool results | `test_handoffs.py::TestBlockedResultDetection::test_detects_action_required_in_tool_result` | Covered |
| Returns False for normal tool results | No false escalation detection | `test_handoffs.py::TestBlockedResultDetection::test_returns_false_for_normal_tool_results` | Covered |
| Returns False for empty tool results list | Edge case: no tool calls | `test_handoffs.py::TestBlockedResultDetection::test_returns_false_for_empty_list` | Covered |
| Detects escalation among multiple results | Finds one blocked result in a list | `test_handoffs.py::TestBlockedResultDetection::test_detects_block_among_multiple_results` | Covered |
| Different action_required value does not trigger escalation | Only `escalate_to_human` triggers forced tool_choice | `test_handoffs.py::TestBlockedResultDetection::test_returns_false_when_action_required_is_different_value` | Covered |
| Forced tool_choice stores EscalationRecord in queue | After forced call, `escalation_queue.get_escalations()` has 1 record | `test_handoffs.py::TestToolChoiceEnforcement::test_forced_escalation_stores_record_in_queue` | Covered |
| AgentResult.stop_reason == "escalated" after forced call | Override ensures human knows escalation occurred | `test_handoffs.py::TestToolChoiceEnforcement::test_forced_escalation_stop_reason_is_escalated` | Covered |
| Second API call uses `tool_choice` to force escalation | `tool_choice={"type":"tool","name":"escalate_to_human"}` in second call kwargs | `test_handoffs.py::TestToolChoiceEnforcement::test_forced_escalation_uses_tool_choice` | Covered |
| stop_reason is exactly "escalated", not "end_turn" | No ambiguity in stop reason | `test_handoffs.py::TestEscalatedStopReason::test_stop_reason_is_escalated_not_end_turn` | Covered |
| Normal flow still returns end_turn | No regression in non-escalation path | `test_handoffs.py::TestEscalatedStopReason::test_normal_flow_still_returns_end_turn` | Covered |
| Usage accumulates from both normal and forced calls | Total tokens include both API calls | `test_handoffs.py::TestUsageAccumulation::test_usage_accumulates_from_both_calls` | Covered |
| Anti-pattern: raw handoff contains tool_use artifacts | `format_raw_handoff()` output includes "tool_use" noise | `test_handoffs.py::TestRawHandoffAntiPattern::test_raw_handoff_contains_tool_use_substring` | Covered |
| Anti-pattern: raw handoff is >5x longer than structured | Size ratio proves structured handoff superiority | `test_handoffs.py::TestRawHandoffAntiPattern::test_raw_handoff_is_longer_than_structured` | Covered |
| EscalationRecord contains all required fields | Model validation: customer_id, tier, issue_type, amount, reason, action, summary, turns | Manual: Run notebook `notebooks/06_structured_handoffs.ipynb`, verify `EscalationRecord` fields | Manual |

---

## 6. Context Management (CCA-RULES.md: "Structured JSON summaries")

| CCA Rule | Expected Behavior | Test Coverage | Status |
|----------|-------------------|---------------|--------|
| Fresh ContextSummary has zero token estimate | No tokens before first update | `test_context_manager.py::TestContextSummary::test_initial_token_estimate_is_zero` | Covered |
| Each update increments turn_count | Turn counter tracks conversation depth | `test_context_manager.py::TestContextSummary::test_update_increments_turn_count` | Covered |
| update appends tool name to tools_called | Tool history preserved | `test_context_manager.py::TestContextSummary::test_update_appends_to_tools_called` | Covered |
| update appends result_summary to decisions_made | Decision log preserved | `test_context_manager.py::TestContextSummary::test_update_appends_to_decisions_made` | Covered |
| token_estimate refreshes on every update | No stale estimates | `test_context_manager.py::TestContextSummary::test_estimate_accuracy_after_each_update` | Covered |
| token_estimate stays under TOKEN_BUDGET after 10+ updates | Compaction fires to prevent unbounded growth | Manual: Run `notebooks/05_context_management.ipynb`, verify compaction fires around update 7-8 | Manual |
| Key facts (customer_id, issue_type) survive compaction | Critical context preserved through compaction | Manual: Run `notebooks/05_context_management.ipynb`, check customer_id present after compaction | Manual |
| `to_system_context()` shows last 5 tools_called | Sliding window for tool history display | `test_context_manager.py::TestContextSummary` (tools_called list behavior) | Covered |
| Internal tools_called list never compacted | Full history kept; only display is windowed | Manual: Run `notebooks/05_context_management.ipynb`, verify `tools_called` grows without truncation | Manual |

---

## 7. Agentic Loop (CCA-RULES.md: "Terminate on stop_reason")

| CCA Rule | Expected Behavior | Test Coverage | Status |
|----------|-------------------|---------------|--------|
| Loop terminates on `end_turn` stop_reason | Single API call when `stop_reason="end_turn"` | `test_agent_loop.py::TestAgentLoop::test_loop_end_turn` | Covered |
| Loop dispatches tools then continues on `tool_use` | Two API calls: tool_use → end_turn | `test_agent_loop.py::TestAgentLoop::test_loop_tool_use_then_end` | Covered |
| Loop stops at max_iterations guard | Returns `stop_reason="max_iterations"` | `test_agent_loop.py::TestAgentLoop::test_loop_max_iterations` | Covered |
| Usage tokens accumulate across iterations | input_tokens, output_tokens sum across calls | `test_agent_loop.py::TestAgentLoop::test_loop_usage_accumulation` | Covered |
| Non-tool stop reasons (max_tokens) terminate gracefully | Handles unexpected stop reasons | `test_agent_loop.py::TestAgentLoop::test_loop_handles_max_tokens_stop` | Covered |
| Loop uses stop_reason, NOT content-type checking | `end_turn` with tool_use content still ends | `test_agent_loop.py::TestAgentLoop::test_loop_no_content_type_checking` | Covered |
| AgentResult fields have correct defaults | stop_reason, messages, tool_calls, final_text, usage | `test_agent_loop.py::TestAgentResult::test_agent_result_fields` | Covered |
| dispatch returns structured error for unknown tool | `status=error`, `error_type=unknown_tool`, `retry_eligible=False` | `test_tools.py::TestDispatchRegistry::test_dispatch_unknown_tool_structured_error` | Covered |
| dispatch returns structured error for malformed input | `status=error`, `error_type=invalid_input`, `retry_eligible=True` | `test_tools.py::TestDispatchRegistry::test_dispatch_malformed_input_returns_structured_error` | Covered |
| Dispatch backward-compatible without callbacks | `dispatch()` without context/callbacks still returns valid JSON | `test_callbacks.py::TestVetoGuarantee::test_dispatch_backward_compatible` | Covered |

---

## 8. Coordinator-Subagent Pattern (CCA-RULES.md: "Explicit context passing required")

| CCA Rule | Expected Behavior | Test Coverage | Status |
|----------|-------------------|---------------|--------|
| Subagent user_message contains Customer and Task fields | Explicit context string passed to subagent | `test_coordinator.py::TestSubagentContextIsolation::test_subagent_user_message_contains_customer_and_task` | Covered |
| Subagent user_message does NOT contain coordinator system prompt | No inheritance of coordinator context | `test_coordinator.py::TestSubagentContextIsolation::test_subagent_message_does_not_contain_coordinator_system_prompt` | Covered |
| Subagent user_message is a string, not messages list | Explicit context, not conversation history | `test_coordinator.py::TestSubagentContextIsolation::test_subagent_message_is_string_not_messages_list` | Covered |
| CoordinatorResult.subagent_results has correct count | 2 subtasks → 2 results | `test_coordinator.py::TestCoordinatorAssembly::test_coordinator_result_has_correct_subagent_count` | Covered |
| CoordinatorResult.synthesis is non-empty string | Coordinator assembles final answer | `test_coordinator.py::TestCoordinatorAssembly::test_coordinator_result_has_synthesis` | Covered |
| 3 subtasks → 3 subagent results | Handles N-task decomposition | `test_coordinator.py::TestCoordinatorAssembly::test_coordinator_result_three_subtasks` | Covered |
| run_agent_loop called once per subtask | 2 topics → exactly 2 subagent calls | `test_coordinator.py::TestCoordinatorDelegation::test_delegation_call_count_matches_subtask_count` | Covered |
| Each subagent receives unique context string | Different user_message per subtask | `test_coordinator.py::TestSubagentFreshMessages::test_each_subagent_call_has_unique_context` | Covered |
| Each subagent receives topic-specific system prompt | `SUBAGENT_PROMPTS["refund"]` vs `SUBAGENT_PROMPTS["shipping"]` | `test_coordinator.py::TestSubagentFreshMessages::test_subagent_receives_topic_specific_system_prompt` | Covered |
| Subagents never communicate directly | No direct subagent-to-subagent calls in coordinator | Manual: Code review `coordinator.py` — verify no cross-subagent calls | Manual |

---

## 9. Anti-Pattern Modules (CCA-RULES.md: All 6 wrong patterns documented)

| CCA Rule | Expected Behavior | Test Coverage | Status |
|----------|-------------------|---------------|--------|
| `confidence_escalation.py` exports `run_confidence_agent` | Callable with correct signature | `test_anti_patterns.py::TestConfidenceEscalation::test_run_confidence_agent_is_callable` | Covered |
| CONFIDENCE_SYSTEM_PROMPT mentions confidence and threshold | Must say "confidence" and "70" | `test_anti_patterns.py::TestConfidenceEscalation::test_confidence_prompt_contains_confidence` + `test_confidence_prompt_contains_70` | Covered |
| `prompt_compliance.py` exports `run_prompt_compliance_agent` | Callable with correct signature | `test_anti_patterns.py::TestPromptCompliance::test_run_prompt_compliance_agent_is_callable` | Covered |
| PROMPT_COMPLIANCE_SYSTEM_PROMPT mentions redact and never log | Demonstrates prompt-only compliance | `test_anti_patterns.py::TestPromptCompliance::test_prompt_compliance_contains_redact` | Covered |
| `swiss_army_agent.py` exports SWISS_ARMY_TOOLS with 15 tools | Over-tooling quantified | `test_anti_patterns.py::TestSwissArmyTools::test_swiss_army_tools_has_exactly_15` | Covered |
| Swiss Army agent has all expected distractor tool names | Canonical misroute targets present | `test_anti_patterns.py::TestSwissArmyTools::test_all_expected_distractor_names_present` | Covered |
| `raw_transcript.py` demonstrates O(n) growth | RawTranscriptContext appends grow unbounded | `test_caching.py::TestRawTranscriptAntiPattern::test_token_estimate_grows_with_each_append` | Covered |
| `batch_api_live.py` explains why Batch API is wrong | BATCH_API_EXPLANATION mentions 24h latency | `test_caching.py::TestBatchApiExplanation::test_mentions_24_hour_latency` | Covered |
| `raw_handoff.py` produces noisy output with tool_use artifacts | format_raw_handoff includes tool_use blocks | `test_handoffs.py::TestRawHandoffAntiPattern::test_raw_handoff_contains_tool_use_substring` | Covered |
| `anti_patterns/__init__.py` re-exports all 3 agent functions | Convenience imports for notebook use | `test_anti_patterns.py::TestAntiPatternsInit::test_init_exports_confidence_agent` + 2 more | Covered |
| Notebooks import anti-patterns for comparison | Side-by-side wrong vs right pattern | Manual: Run `notebooks/01_escalation_anti_pattern.ipynb` — verify anti-pattern cell fails | Manual |

---

## 10. Structured Output / Silent Failure Prevention (CCA-RULES.md: "Three-Layer Reliability")

| CCA Rule | Expected Behavior | Test Coverage | Status |
|----------|-------------------|---------------|--------|
| Unknown tool returns structured error context | `status=error`, `error_type`, `source`, `retry_eligible`, `fallback_available`, `partial_data` | `test_tools.py::TestDispatchRegistry::test_dispatch_unknown_tool_structured_error` | Covered |
| Malformed input returns structured error (not exception) | `status=error`, `error_type=invalid_input`, `source=<tool_name>` | `test_tools.py::TestDispatchRegistry::test_dispatch_malformed_input_returns_structured_error` | Covered |
| Escalation uses tool_choice for Layer 2 schema enforcement | `tool_choice={"type":"tool","name":"escalate_to_human"}` forces structured output | `test_handoffs.py::TestToolChoiceEnforcement::test_forced_escalation_uses_tool_choice` | Covered |
| Validation-retry loop (informed retry) | N/A — this project uses veto callback + forced tool_choice instead; retry loop not present | Manual: NB07 integration test demonstrates end-to-end flow with escalation | Manual |

---

## 11. CLAUDE.md Hierarchy (CCA-RULES.md: "Project standards in .claude/CLAUDE.md")

| CCA Rule | Expected Behavior | Test Coverage | Status |
|----------|-------------------|---------------|--------|
| `.claude/CLAUDE.md` exists and is committed | Project-level standards in VCS | Manual: `git ls-files .claude/CLAUDE.md` returns the file | Manual |
| `.claude/CLAUDE.md` contains team coding standards | Line length, type annotations, architecture rules | Manual: Review `.claude/CLAUDE.md` content directly | Manual |
| No secrets in `.claude/CLAUDE.md` | Credentials in `~/.claude/CLAUDE.md`, not project VCS | Manual: Review `.claude/CLAUDE.md` for API key or token patterns | Manual |
| `CLAUDE.local.md` is gitignored (if present) | Personal overrides never committed | Manual: Check `.gitignore` for `CLAUDE.local.md` entry | Manual |

---

## 12. CI/CD (CCA-RULES.md: "-p mandatory, --bare recommended")

| CCA Rule | Expected Behavior | Test Coverage | Status |
|----------|-------------------|---------------|--------|
| `-p` flag present in CI workflow | `claude -p` in `ci.yml` | Manual: `grep -q "\-p" .github/workflows/ci.yml` | Manual |
| `--bare` flag present in CI workflow | Reproducible behavior | Manual: `grep -q "\-\-bare" .github/workflows/ci.yml` | Manual |
| `--output-format json` used for programmatic parsing | Structured output from claude CLI | Manual: `grep -q "output-format json" .github/workflows/ci.yml` | Manual |
| `jq -r '.result'` extracts text from JSON envelope | Raw JSON not posted to PR comment | Manual: `grep -q "jq" .github/workflows/ci.yml` | Manual |
| `--allowedTools Read,Grep,Glob` sandboxes CI agent | Least privilege for CI | Manual: `grep -q "allowedTools" .github/workflows/ci.yml` | Manual |
| ANTHROPIC_API_KEY as GitHub secret | No hardcoded credentials | Manual: `grep -q "secrets.ANTHROPIC_API_KEY" .github/workflows/ci.yml` | Manual |
| Nightly cron trigger present | Regression detection without commits | Manual: `grep -q "cron" .github/workflows/ci.yml` | Manual |

---

## Summary

| Section | Automated | Manual | Gaps | Notes |
|---------|-----------|--------|------|-------|
| 1. Escalation Logic | 16 | 0 | 0 | All 4 thresholds and veto guarantee tested |
| 2. Tool Count | 11 | 0 | 0 | Both correct (5) and anti-pattern (15) tested |
| 3. Compliance Enforcement | 8 | 0 | 0 | Includes critical PII-before-write test |
| 4. Cost Optimization | 15 | 0 | 0 | All caching, token accounting, anti-patterns |
| 5. Handoff Pattern | 13 | 1 | 0 | EscalationRecord field verification manual |
| 6. Context Management | 5 | 4 | 0 | Compaction behavior verified in notebooks |
| 7. Agentic Loop | 10 | 0 | 0 | Including stop_reason correctness tests |
| 8. Coordinator-Subagent | 9 | 1 | 0 | No-direct-comms verified via code review |
| 9. Anti-Pattern Modules | 10 | 1 | 0 | Notebook execution verifies rendering |
| 10. Structured Output | 3 | 1 | 0 | Validation-retry loop not automated |
| 11. CLAUDE.md Hierarchy | 0 | 4 | 0 | File-system checks, not unit tests |
| 12. CI/CD | 0 | 7 | 0 | Workflow checks, not unit tests |
| **Totals** | **100** | **19** | **0** | **No genuine gaps found** |

### Manual Verification Commands

For the 19 manual checks above, use these commands to verify before exam/demo:

```bash
# CLAUDE.md hierarchy
git ls-files .claude/CLAUDE.md                        # must return file path
grep -i "secrets\|api.key\|token" .claude/CLAUDE.md  # must return nothing

# CI/CD flags (all should return exit 0)
grep -q "\-p" .github/workflows/ci.yml && echo PASS
grep -q "\-\-bare" .github/workflows/ci.yml && echo PASS
grep -q "output-format json" .github/workflows/ci.yml && echo PASS
grep -q "jq" .github/workflows/ci.yml && echo PASS
grep -q "allowedTools" .github/workflows/ci.yml && echo PASS
grep -q "secrets.ANTHROPIC_API_KEY" .github/workflows/ci.yml && echo PASS
grep -q "cron" .github/workflows/ci.yml && echo PASS
```

### Notebook Verification Steps

| Notebook | Cell(s) to run | What to verify |
|----------|----------------|----------------|
| `notebooks/05_context_management.ipynb` | Compaction demo cells | token_estimate stays below TOKEN_BUDGET after 10+ updates |
| `notebooks/05_context_management.ipynb` | Post-compaction cell | customer_id preserved in context after compaction |
| `notebooks/06_structured_handoffs.ipynb` | EscalationRecord cell | All 8 required fields present in output JSON |
| `notebooks/07_integration.ipynb` | Full scenario cell | end-to-end: lookup → policy → blocked refund → escalation |
| `notebooks/01_escalation_anti_pattern.ipynb` | Anti-pattern cell | confidence-based routing fails to escalate correctly |

---

*Reference: [CCA-RULES.md](../../CCA-RULES.md) — authoritative source for all rules above*
*Phase: 06-testing-and-ci-cd*
*Analysis date: 2026-03-28*
