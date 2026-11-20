# Workshop notes: "Claude for Finance" (Claude Builder Club Oxford, 19 Nov 2026)

Source: the workshop's slide deck, a public claude.ai artifact: https://claude.ai/artifact/EAuL4Q1NvnAfyNKDacLg7x
Read in full on 19 Nov 2026: all 53 slides and their speaker notes. These are notes in our own words, not a copy; open the link for the slides themselves. Figures quoted from the deck are the deck's, not checked by us.

Event: Thursday 19 Nov 2026, 4 to 7pm, Cohen Quad. Run by Claude Builder Club Oxford with CapitOx and Alpha Fund. There was also a guest talk on deal sourcing with Claude.

---

## 1. Data sources (the part that matters most for our desk)

### 1a. Free sources the deck recommends

| Source | What it gives | How the deck connects it | State in this repo |
| --- | --- | --- | --- |
| Web search | News, press releases, RNS (UK regulatory news) | Built in to claude.ai | Not wired; Tavily deferred by Mark |
| Google Drive | Past pitches, templates, Sheets | Built-in connector | Not relevant to the desk yet |
| SEC EDGAR | Every US filing and its financials | Hosted server edgar.tools at `https://app.edgar.tools/mcp`; sign in with Google or email, no key; free tier | Have it, via the local `edgartools` server instead |
| Alpha Vantage | Prices, fundamentals, earnings, FX; also a news-and-sentiment feed | Hosted server at mcp.alphavantage.co with a free key | Have it (`alphavantage`, official local server) |
| FRED | 800,000+ macro series: rates, CPI, GDP | Community server in the desktop app, free key | Have it (`fred`) |
| Companies House | UK accounts, directors, owners | Community server in the desktop app, free key | Have it (`companies_house`, our own server) |

Deck's cautions: free claude.ai accounts get one custom connector; community servers are not built by Anthropic or the data provider, so check who built one and test it; never paste an API key into a chat. Alpha Vantage's free key allows 25 requests a day, so pull data once and save it.

### 1b. Licensed sources "you'll meet at work" (what a real desk has)

None of these is available to us. They are the honest list of holes between our example desk and a real one, and good labels for placeholder agents or tools.

| Provider | What the deck says it is used for |
| --- | --- |
| FactSet | Consensus estimates, pulled into a comps table |
| S&P Capital IQ | Precedent transactions and deal multiples |
| PitchBook | Screening private companies by sector, stage, last round |
| Morningstar | Fund holdings, fees and ratings |
| LSEG | Price history, fundamentals and newswires |
| Moody's | Credit ratings and outlooks |
| MSCI | ESG ratings and index weights |
| Daloopa | Model-ready KPIs extracted from filings |
| Financial Modeling Prep | Mentioned in the notes as a cheaper API alternative |

Deck's points: a licence is needed and Claude sees only what the firm pays for; the connectors also work inside Excel.

### 1c. Document types the deck works from

These are inputs, not providers. Each is a candidate for a document or research agent.

- Annual reports and 10-K / 10-Q filings, by named section (MD&A, Item 1A risk factors, the debt note, the segment note).
- Earnings call transcripts (the last two, to compare tone and guidance).
- News from the last 30 days, grouped by theme, each item dated and linked.
- Central bank minutes (the deck's example: six Bank of England minutes rated hawkish to dovish).
- Broker notes and analyst views.
- Investor Day material (Nike's was 16 to 17 Nov 2026).
- A price history CSV for quant work.

### 1d. Candidates to add to the desk, in order of usefulness

1. **Earnings call transcripts.** Done 19 Nov: the `news` agent reads them through `mcp_servers/news.py` (Alpha Vantage, existing key).
2. **News.** Done 19 Nov: the `news` agent gets Finnhub company news. Sentiment scores are not available: Alpha Vantage's news-and-sentiment endpoint is premium on our free key.
3. **Web search** for news, press releases and RNS (Tavily, when Mark wants it).
4. **Central bank minutes** (Bank of England, Fed, ECB): public pages, no key; would need a small server of our own.
5. **Financial Modeling Prep**: the one "at work"-style source with a cheap API; needs an account.
6. **edgar.tools hosted server**: an alternative to our local EDGAR server; only worth it if the local one causes trouble.
7. Placeholders only: FactSet, Capital IQ, PitchBook, Morningstar, LSEG, Moody's, MSCI, Daloopa.

---

## 2. The Investment Committee Challenge (slides 50 to 51)

- Brief: act as a student fund's investment committee and decide in 60 minutes (17:30 to 18:30) whether to buy Nike (NKE).
- Three deliverables with soft checkpoints: a one-page tear sheet by 17:45; a five-year DCF with bear, base and bull cases, a WACC build-up, the growth implied by today's price, and live formulas by 18:10; a 3 to 4 slide, two-minute pitch with a price target by 18:30, red-teamed first.
- Tools: one connector (Alpha Vantage, free key), the data pack, web search.
- **The data pack** was Nike's FY26 10-K, the Q1 FY27 results and the call transcript. It was handed out at the event; it is not in the deck.
- Nike traps the deck lists: the fiscal year ends in May, so label years FY; reported versus adjusted figures and restructuring costs; free cash flow did not cover the dividend in FY26 (the deck's claim); use guidance from the Q1 call and the Investor Day, not older targets; trace every number to a page or a cell.

Our Nike work is in `~/Dropbox/Code/nke-investment-committee/`, built without the data pack.

---

## 3. Rules and checks (already partly in `skills/finance-research-rules` and `skills/source-cross-check`)

### Research
- Prompt rules: name the source and section; set the comparison (this quarter versus last); ask for a format; require a source (quote, speaker or page) for every point; say what to flag.
- Checks: name the exact section; fix fiscal year, currency, units and reported-or-adjusted in every prompt; primary sources before news; ask for an as-of date on every price and figure; prices from live data, never from model memory.
- Common errors: thousands versus millions; fiscal years that do not match the calendar or each other; quotes that are not in the transcript; uploading confidential data.

### Why sources disagree (slide 25)
Fiscal versus calendar year; reported versus adjusted; restated prior years; basic versus diluted share counts; currency, units or stale data. When sources disagree, the filing wins. The deck's exercise: pull the same four figures from the 10-K, Alpha Vantage and a news article, and explain any gap over 1%.

### Analysis
- Prompt rules: fix the basis (peers, LTM or NTM, calendarised); formulas not values, with assumptions on one tab; ask for a bear, base and bull range; show the workings (WACC build-up, a source per input); ask what was assumed and what would break the answer.
- Model checks: formulas not hard-coded values; define net debt and share count; calendarise peers; sanity-check terminal value share, exit multiple and margins; change one input and confirm the output moves the right way.
- Common errors: arithmetic done in prose; peer multiples from memory; mixed bases across peers. The person signs off on the model, not Claude.
- Quant work (code execution): returns and volatility, beta against an index, maximum drawdown, rolling correlation, 95% historical VaR, macro overlay from FRED.
- Backtest warnings: look-ahead bias (using information not available at the time), survivorship bias (testing only companies that still exist), and a good backtest still ignores costs, turnover and regime changes.

### Sentiment (slide 19)
Collect the text; write the scoring rubric into the prompt (the deck uses −2 to +2); require the quoted sentence behind each score; chart the change over time in code. Spot-check ten scores by hand and filter out companies with look-alike names.

### Building tools
- Start small; Claude drafts and a person sends; give connectors read-only access unless they must write; keys in environment variables, never in code or chats; test on cases you already know; check every run for the first week.
- The deck's example of a connector to build yourself is a Companies House server with three tools (search a company, list officers, get filing history), which is what `mcp_servers/companies_house.py` now does.

---

## 4. Ideas this gives the misroute project

- **Semantic misinterpretation cases:** the "why sources disagree" list is a ready set of plausible misreadings (FY versus calendar, reported versus adjusted, basic versus diluted, LTM versus NTM, thousands versus millions). Several are already in `SEMANTIC_SWAPS` in `src/misroute/inject.py`; the rest could be added.
- **Context mismatch cases:** look-ahead and survivorship bias in a backtest; stale data; old guidance used after an Investor Day.
- **Authority mismatch cases:** "Claude drafts, you send" and least-access connectors are authority rules; a data agent that sends or approves breaks them.
- **A held-out request set:** the deck's worked prompts (guidance changes, risk-factor comparison, debt schedule, adjusted EBITDA reconciliation, comps, DCF, implied growth, stress test) overlap with `data/requests/sample.jsonl`, so they should not be used as held-out test items.
- **Org map:** section 1b is the list of data a real desk has that ours lacks.

---

## 5. Tools and products the deck names

- Skills repository: github.com/anthropics/financial-services (comps, DCF, LBO, three-statement model, earnings analysis, IC memo, pitch deck). Already vendored under `skills/vendor/anthropic-financial-services/`. In Claude Code the `financial-analysis` plugin gives `/comps`, `/dcf` and `/lbo`.
- Free plan: chat, web search, file uploads and creation, code execution, connectors, skills, up to 5 Projects, one custom connector.
- Paid plans add: Research mode, the most capable models, Claude in Excel, PowerPoint and Word, scheduled tasks, Claude Code, about five times the usage.
- Scheduled tasks: the deck's examples are a weekday watchlist brief, a Friday sentiment tracker, an earnings-day check against guidance, a Monday macro calendar and a month-end fund-versus-benchmark report.
- Presentation: Claude Slides and Docs, file creation, Claude in PowerPoint, a design system built from a brand, voice mode for rehearsal, and a red-team prompt that plays a sceptical portfolio manager.

## 6. Figures the deck uses to motivate the topic (slide 6; the deck's sources, unchecked)

- 86% of UK financial services firms use AI, up from 58% in 2022 (Bank of England and FCA, 2026).
- JPMorgan's 2026 technology budget is $19.8bn, with about $2bn a year on AI.
- Generative AI could add $200bn to $340bn a year in value to banking (McKinsey).

## 7. Club details

Claude Builder Club Oxford: meetings 3 to 4 times a term, a monthly workshop, a hackathon at the end of Hilary term. Instagram @cbc_oxford. Next event: Ecosystem Social, Friday 20 Nov 2026, 7 to 9pm, The Oxford Retreat.
