---
name: finance-research-rules
description: Rules for any finance research answer built from filings, transcripts, market data or news. Use whenever an agent reports a financial figure, price, guidance change, risk factor, debt term or adjusted metric.
---

# Finance research rules

Follow these for every finance answer, whichever model you are.

## Before answering

1. **Name the exact source and section.** "10-K Item 1A", "MD&A", "Note 9 (Debt)", "segment note", "Q3 FY2026 earnings call". Never "the report".
2. **Fix the basics.** State fiscal year (and its end month), currency, units (thousands, millions), and whether a figure is reported (GAAP/IFRS) or adjusted.
3. **Primary sources first.** Filings and call transcripts beat press releases, which beat news, which beat blogs. When sources disagree, the filing wins.
4. **Live data for prices.** Prices, market caps, yields and FX come from a tool call (market-data connector or web search) made now. Never from memory. If no tool is available, say so and give no number.

## In the answer

5. **Source every point:** a short quote, the speaker (for calls), and the page or section.
6. **Date-stamp everything:** each price and figure carries an as-of date or period.
7. **Use the requested format** (list, table, schedule). Default to a table for anything with more than three figures.
8. **Flag what was asked to be flagged**, for example maturities due within 24 months, new risk factors, guidance cuts.

## Output contract

End with a `sources` block, one line per source: `[id] document, section, page, as-of date`.
If you could not verify a figure, write `UNVERIFIED` next to it rather than omitting the caveat.

## Prompt patterns that work

- *Guidance changes:* list every quantitative guidance change between the Q2 and Q3 calls, with quote, speaker and page.
- *Risk factors:* compare Item 1A in the last two 10-Ks in a table: new, removed, reworded.
- *Debt:* pull the maturity schedule and covenants from the debt note as a table; flag anything due within 24 months.
- *Adjusted EBITDA:* reconcile reported to adjusted; list every add-back, its page, and its year-on-year change.

## Models built from this data

Formulas, not hard-coded values. Assumptions on one tab. Sanity-check against history and peers. Break-test one input at a time.
