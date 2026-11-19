---
name: source-cross-check
description: Compare the same figures across two or more sources (filing, data vendor, news), flag gaps and explain them. Use when asked to verify, reconcile or cross-check numbers, or before passing a figure to another agent.
---

# Source cross-check

## Procedure

1. Pull each requested figure from every source separately. Record source, section or endpoint, period, currency, units, and reported vs adjusted.
2. Normalise units and currency before comparing. Do not normalise period definitions silently; flag them.
3. Put the figures side by side in a table: one row per figure, one column per source, plus `gap_%` and `likely_reason`.
4. Flag any gap over **1%** (or the threshold the request sets).
5. For each flagged gap, give the most likely reason from the list below, and say how you would confirm it.
6. State the figure to use. **The filing wins** unless it has since been restated.

## Why numbers disagree (check in this order)

| Code | Reason | Typical tell |
| --- | --- | --- |
| `FISCAL_VS_CALENDAR` | Fiscal year vs calendar year | Company year ends Sep/Jun; news quotes calendar year |
| `REPORTED_VS_ADJUSTED` | GAAP/IFRS vs adjusted / non-GAAP | Press release headline vs income statement |
| `RESTATED` | Prior year restated | Later filing shows different prior-year figure |
| `BASIC_VS_DILUTED` | Share count basis | Vendor uses basic shares outstanding |
| `DEFINITION` | Different metric definition | Vendor's "gross margin" excludes or includes items |
| `CURRENCY_UNITS` | Currency, units or scaling | Off by ~1000x or by an FX rate |
| `STALE` | Out-of-date data | Vendor as-of date before latest filing |

## Output

```
| figure | filing | vendor | news | gap_% | flag | likely_reason | confirm_by |
```

Then one line: which value to use and why.

## Note for this project

These reasons are also realistic **context mismatch** and **semantic misinterpretation** cases: an agent that receives "FY revenue" but answers with calendar-year revenue has been handed an instruction outside its context scope, or has misread it. Reuse the codes above as labels when building test requests.
