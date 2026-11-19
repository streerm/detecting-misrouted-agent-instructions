# Vendored: Anthropic financial-services skills

Source: https://github.com/anthropics/financial-services
Commit: 3e32c2287dcb637c184c01cc0ad82d6af7e9bb0f (12 Nov 2026)
Licence: Apache License 2.0 (see LICENSE in this folder). Copyright Anthropic. Copied unmodified.

| Folder | From plugin |
| --- | --- |
| 3-statement-model, audit-xls, clean-data-xls, competitive-analysis, comps-analysis, dcf-model, deck-refresh, ib-check-deck, lbo-model, ppt-template-creator, pptx-author, skill-creator, xlsx-author | financial-analysis |
| catalyst-calendar, earnings-analysis, earnings-preview, idea-generation, initiating-coverage, model-update, morning-note, sector-overview, thesis-tracker | equity-research |
| ic-memo | private-equity |
| pitch-deck | investment-banking |

## Portability

These were written for Claude. Most are plain methodology and work as system-prompt context for any model.
Some assume Claude-side tools: `xlsx-author`, `pptx-author`, `comps-analysis`, `lbo-model` and `clean-data-xls`
refer to live Excel / Office or MCP tools. With Llama or Qwen, give the agent equivalent tools
(e.g. openpyxl, python-pptx) or use those skills for methodology only.

## Updating

```bash
git clone --depth 1 https://github.com/anthropics/financial-services /tmp/fs
cp -R /tmp/fs/plugins/vertical-plugins/financial-analysis/skills/. skills/vendor/anthropic-financial-services/
# ...same for equity-research, private-equity/ic-memo, investment-banking/pitch-deck; update the commit above
```

Do not edit these files in place; put project-specific changes in our own skills so updates stay clean.
