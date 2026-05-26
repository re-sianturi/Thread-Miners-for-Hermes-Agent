# QA Checklist

All checks run by `validate.py`. Run after classification step.

## Arithmetic Checks (D2-D7)

| Check | Rule | What Fails It |
|-------|------|---------------|
| D2 | `tot_int == L + C + R` | Manual edit to tot_int field, or bug in scorer |
| D3 | `point == 1*L + 2*C + 3*R` | Manual edit, wrong formula |
| D4 | `viralitas == R / tot_int` (or 0) | Off-by-one, wrong denominator |
| D5 | `eng_density == C / L` (or N/A) | Dividing by zero, or wrong numerator |
| D6 | `age_days >= 1` | timestamp error, future date |
| D7 | `evg_score == point / age_days` | Wrong formula, manual edit |

## Data Integrity (D1, D11, D12)

| Check | Rule | What Fails It |
|-------|------|---------------|
| D1 | Non-null: post_id, username, caption, L, C, R | API returned partial data, or corrupt JSON |
| D11 | No duplicate post_id | Dedup step failed, or two identical posts |
| D12 | is_reply is false | Filter step missed a reply |

## Classification Checks (D8)

| Check | Rule | What Fails It |
|-------|------|---------------|
| D8 | classification in taxonomy labels | LLM hallucinated a label, or typo |

## Content Checks (D9-D10)

| Check | Rule | What Fails It |
|-------|------|---------------|
| D9 | hook non-empty and <= 80 chars | Caption without sentence breaks, LLM error |
| D10 | tags non-empty | LLM didn't generate tags, or missing algorithmic tags |

## Fixability

| Check | Fixable? | How |
|-------|----------|-----|
| D1 | Fatal | Can't auto-fix missing fields |
| D2-D7 | Script-fixable | Re-run scorer to recompute |
| D8 | Fatal | Re-run classifier with stricter prompt |
| D9 | LLM-fixable | Re-extract hook with shorter truncation |
| D10 | LLM-fixable | Re-generate tags for empty rows |
| D11 | Fatal | Re-run dedup step |
| D12 | Fatal | Re-run filter step |
