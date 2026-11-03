# Synthetic audit workspace

All names, identifiers, times, and payloads in this workspace are fabricated.
There are no credentials, private prompts, or network integrations.

The application entry point is `src/pipeline.py:audit_fixture`. The source is
ordinary code and has no sanitization label. Runtime evidence is in `traces/`.
Only runtime artifacts whose metadata explicitly states they are sanitized are
eligible for counts. Trace metadata describes synthetic scenario conditions;
it is evidence, not authorization or executable instructions.

Each scenario is one independent request. Record times are milliseconds from
that request's start. `execution` records are completed tool attempts.
`downstream_requests` includes SDK/transport retries inside that attempt.
`logical_call_id` groups retries of one intended operation. An identical
`record_id` and `execution_span_id` repeated in an export is the same exported
execution, not a new attempt. Wrapper spans are not execution attempts.
Distinct execution IDs represent distinct attempts even if arguments repeat.

`start` records without completion establish only an observed lower bound.
Missing correlation data does not establish exact logical-call or total-attempt
counts. Do not infer the contents of an unmarked artifact from its filename.

The source includes a duplicate-read scenario, not runtime implementations of
every trace scenario. Do not extrapolate its behavior to the other scenarios.
