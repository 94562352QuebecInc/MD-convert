# Fund Report — Full Extraction & Markdown Generation Prompt

> **Purpose:** A single, end-to-end instruction for any LLM. This prompt applies to **each PDF individually**. When given one or more PDFs, process each one independently and produce **one `.md` output file per PDF**. Each output file is named after its source PDF (same filename, `.md` extension). The LLM will:
> 1. Identify which schema(s) the document matches.
> 2. Convert the entire PDF to rich Markdown.
> 3. Extract the structured schema data.
> 4. Write an investment professional summary.
> 5. Produce **one `.md` output file per PDF**, named identically to the source PDF (e.g. `Q4_2023_Report.pdf` → `Q4_2023_Report.md`).

---

## ⚡ SINGLE INSTRUCTION TO THE LLM

You are a meticulous financial document processing agent. You will receive one or more PDF fund reports. **Process each PDF independently** — carry out all stages below for each PDF in sequence and produce **one `.md` output file per PDF**. Do NOT produce JSON. Do NOT produce plain text. Each output file must be valid Markdown, saved with the **same filename as its source PDF** but with a `.md` extension.

---

## STAGE 1 — Identify the Document Schema

> 🔴 **IMPORTANT — BEFORE READING THE DOCUMENT, IDENTIFY WHICH SCHEMA IT BELONGS TO.**
> Review all schemas listed below. Once you have identified the correct schema(s) for this document, state that identification at the very top of your output file (see Stage 4 for the exact format).
> If the document does not match any of the schemas below, that is perfectly fine — skip the schema identification statement and proceed directly with the Markdown conversion in Stage 2.

The following schemas are available. A document may match **one primary schema** (for its fund-level data) and one **portfolio-level schema** (for its investment data). Identify the best match for each.

---

### Schema A — Fund Report (Quarterly / Annual)

This schema applies to standard quarterly or annual fund reports that include a manager's letter, portfolio overview, and summary financial metrics.

#### A1: Fund-Level Fields

| Field | Definition |
|---|---|
| `fund_name` | Official fund name exactly as written, including abbreviations and special characters. |
| `report_date` | Report closing date (end of reporting period). Format: `DD-MM-YYYY`. Prioritize over publication date. |
| `fund_investment_region` | Geographic region or country the fund invests in. If country is specified alongside regions, return country only. This is for the fund, NOT a portfolio company. |
| `report_currency` | Currency the fund reports in (3-letter ISO 4217, e.g. `USD`). Prioritize explicit labels ("Fund currency", "Reporting currency"). If absent, infer from fund-level figures. |
| `fund_vintage` | Explicit vintage year as stated. If absent, use the year of the fund's first investment. Return as `YYYY`. |
| `fund_commitment` | Total LP commitments to the fund. NOT capital called or contributed. Return as full number. |
| `fund_capitalinvested` | Cumulative capital invested into all companies (active + exited). NOT capital called or committed. Often labeled "Invested Cost" or "Total Cost." |
| `fund_contributions` | Total capital called from investors since inception. Also called "Capital Contributions." Include both GP and LP. |
| `fund_distributions` | Cumulative distributions to all partners since inception. Found in Statement of Changes in Partners' Capital. DO NOT use portfolio-level "Realized Proceeds" or "Exit Value." |
| `fund_nav` | Net Asset Value = Total Assets − Total Liabilities. Also called "Partners' Capital" or "Total Partners' Equity." Found at bottom of Balance Sheet. |
| `fund_investment_assets` | Fair value of assets invested in portfolio companies as of report date. Usually "Investments at Fair Value." |
| `fund_letterupdate` | 3–6 sentence summary of the manager's letter or quarterly update. Focus on performance, strategy, market outlook. Support with figures. |

#### A2: Portfolio Company Fields

| Field | Definition |
|---|---|
| `investment_name` | Name exactly as stated. Use holding company name if both holding and operating names appear. Ignore parenthetical qualifiers. |
| `investment_description` | 1–2 sentences: sector, industry, core activities, business model (e.g. SaaS, marketplace). |
| `investment_update` | 2–3 sentences on the company's progress, challenges, or key events for the current reporting period. |
| `investment_geography` | Primary country of operation. Full country name. NOT city-level. |
| `investment_first_investment_date` | Earliest recorded investment date. Format: `DD-MM-YYYY`. |
| `investment_ownership` | Fund's fully diluted ownership % of the company's equity. NOT a partner's share of the fund. |
| `investment_total_cost` | Cumulative investment cost. Labeled "Cost" or "Invested Capital." Sum multiple line items (equity + notes) if needed. Prefer fund currency. |
| `investment_realized` | Total amount realized from the company (partial or full exits). Sum multiple entries. |
| `investment_unrealized` | Current fair value ("Fair Value," "FMV," "Carrying Value"). Prefer fund currency. Sum if multiple. |
| `investment_industry` | Industry or sector label exactly as written. |
| `investment_irr` | Investment-level IRR (not fund-level). Expressed as a percentage. |
| `investment_exit_date` | Date of full exit or write-off. Format: `DD-MM-YYYY`. |
| `investment_currency` | Currency in which the portfolio company reports its financials. 3-letter ISO code. |
| `investment_revenue` | Revenue for the **quarter only** (not TTM/LTM). Null if not provided. Do NOT calculate. |
| `investment_ebitda` | EBITDA for the **quarter only** (not TTM/LTM). Null if not provided. Do NOT calculate. |
| `investment_cash` | Total cash on hand as of report date ("Cash Balance," "Available Cash"). NOT net debt. |
| `investment_fte` | Total employees as of report date ("FTE," "Full-Time," "Employees"). |

---

### Schema B — Capital Call Notice

This schema applies to documents that notify a limited partner of a capital call (drawdown request).

| Field | Definition |
|---|---|
| `notice_date` | The date the notice was issued, in DD-MM-YYYY format. |
| `notice_id` | A unique identifier for the capital call notice. |
| `fund_name` | The full legal name of the fund. |
| `lp_name` | The full legal name of the limited partner receiving the notice. |
| `payment_due_date` | The date by which the capital call payment is due. Return in DD-MM-YYYY format. |
| `currency` | The currency in which the payment is to be made in ISO 4217. |
| `lp_current_call_total` | The total amount requested from the limited partner in this capital call. |
| `lp_remaining_unfunded_commitment` | The remaining unfunded commitment of the limited partner after this call. |
| `event_summary` | A concise summary of the capital call event. |

---

### Schema C — Distribution Notice

This schema applies to documents that notify a limited partner of a distribution.

| Field | Definition |
|---|---|
| `notice_date` | The date the notice was issued, in DD-MM-YYYY format. |
| `notice_id` | A unique identifier for the notice. |
| `fund_name` | The legal name of the fund. |
| `lp_name` | The full legal name of the limited partner receiving the notice. |
| `distribution_date` | The date on which the distribution is scheduled or occurred, in DD-MM-YYYY format. |
| `currency` | The currency in which the distribution is made in ISO 4217. |
| `lp_current_distribution_total` | The amount distributed to the LP in this event. |
| `distribution_summary` | A concise summary of the distribution event. |

---

### Schema D — Combined Capital Call & Distribution Notice (Netted)

This schema applies to documents where a capital call and a distribution have been netted against each other into a single notice.

| Field | Definition |
|---|---|
| `notice_date` | The date the notice was issued, in DD-MM-YYYY format. |
| `notice_id` | A unique identifier for the notice. |
| `fund_name` | The legal name of the fund. |
| `lp_name` | The full legal name of the limited partner receiving the notice. |
| `transaction_date` | The effective date for the payment or receipt of funds (Due Date or Distribution Date), in DD-MM-YYYY format. |
| `currency` | The currency in which the transaction is settled in ISO 4217. |
| `lp_current_call_total` | The gross capital call amount before any distribution offset is applied. |
| `lp_current_distribution_total` | The gross distribution amount before any capital call offset is applied. |
| `net_amount` | The final cash amount to be transferred. This should match the difference between the Call Total and Distribution Total. |
| `transaction_direction` | Indicates the direction of the Net Amount. Values should be `'Payable by LP'` or `'Receivable by LP'`. |
| `lp_remaining_unfunded_commitment` | The remaining unfunded commitment of the limited partner after this event. |
| `event_summary` | A concise summary of the event, explicitly mentioning that a capital call was netted against a distribution. |

---

### Schema E — Capital Account Statement

This schema applies to capital account schedules or statements showing an LP's beginning and ending capital balance for a reporting period.

| Field | Definition |
|---|---|
| `fund_name` | The name of the fund for which the schedule is prepared. Will be similar to general_partner_name. |
| `report_period` | The period covered by the report (e.g., Year Ended December 31, 2023). |
| `report_date` | The specific date as of which balances are reported. Return in DD-MM-YYYY format. |
| `lp_name` | The name of the limited partner. Fund of Funds will generally be the LP. |
| `general_partner_name` | The name of the general partner associated with the fund. Will be similar to fund_name. |
| `report_currency` | Currency in which the notice is issued. |
| `lp_total_commitment` | The total amount of capital committed by the limited partner. This is not contributions. |
| `total_capital_called_since_inception` | The total amount of capital contributions made since inception by the limited partner. |
| `lp_beginning_balance` | The limited partner's capital account balance at the beginning of the reporting period. |
| `lp_current_contributions` | The limited partner's amount of capital contributed during the current period. |
| `lp_current_distributions` | The limited partner's amount of capital distributed during the current period. |
| `lp_current_management_fees` | Management fees charged during the current period to the limited partner. |
| `lp_current_fund_expenses` | Fund expenses incurred during the current period by the limited partner. |
| `lp_current_carried_interest` | Carried interest allocated during the current period to the limited partner. |
| `lp_realized_gain_loss` | Net realized gain or loss for the current period incurred by the limited partner. |
| `lp_unrealized_gain_loss` | Net unrealized gain or loss for the current period incurred by the limited partner. |
| `lp_ending_balance` | The limited partner's capital account balance at the end of the reporting period. |
| `lp_total_distributions_since_inception` | Total amount of capital distributed to the limited partner since inception. |

---

### Schema F — Financial Statements

This schema applies to formal financial statement packages, including the Statement of Operations, Statement of Assets & Liabilities, and Statement of Changes in Partners' Capital.

#### F1: Fund-Level Financial Statement Fields

| Field | Definition |
|---|---|
| `fund_name` | The official name of the fund as written in the financial report. Return the name exactly as written, including any special characters or abbreviations. |
| `report_date` | The report's closing date (end of the reporting period). Prioritize this over the publication date. Return in DD-MM-YYYY format. |
| `report_period` | The text describing the primary duration of the income statement. Prioritize the Year-to-Date or 'For the Year Ended' period if multiple are present. This field defines 'the period' for all subsequent fields. |
| `report_currency` | The currency explicitly mentioned for the financial statements. If no currency is explicitly mentioned, return exactly null. Return the 3-letter ISO 4217 code. |
| `fund_investment_assets` | The value of assets invested in portfolio companies, usually labeled 'Investments at Fair Value', as of the `report_date`. Found on the Statement of Assets, Liabilities, and Partners' Capital. Return the full numerical value, applying any scale indicators. |
| `fund_cash_assets` | The fund's cash and cash-equivalent holdings as of the `report_date`. Found on the Statement of Assets, Liabilities, and Partners' Capital. Return the full numerical value, applying scale indicators. |
| `fund_other_assets` | Any additional assets not categorized as investments or cash as of the `report_date`. Found on the Statement of Assets, Liabilities, and Partners' Capital. Return the value as stated, applying any scale indicators. |
| `fund_liabilities` | The total liabilities of the fund as of the `report_date`. Found on the Statement of Assets, Liabilities, and Partners' Capital. Return the full numerical value, applying any scale indicators. |
| `fund_nav` | The fund's Net Asset Value (NAV), also seen as 'Partners' Equity' or 'Partners' Capital' or 'Total Net Assets', as of the `report_date`. Return the full numerical value, applying any scale indicators. |
| `fund_interest_dividend_income` | Income earned from investments for the duration specified in `report_period` (prioritizing YTD). Do not include gains or fees. Found on the Statement of Operations. |
| `fund_gain_loss_unrealized` | The net change in unrealized gains or losses for the duration specified in `report_period` (prioritizing YTD). Found on the Statement of Operations. Return positive for gains, negative for losses. |
| `fund_management_fee` | Management fees charged for the duration specified in `report_period` (prioritizing YTD). Exclude performance/incentive fees. Found on the Statement of Operations. |
| `fund_expenses` | Other fund expenses for the duration specified in `report_period` (prioritizing YTD). Excludes management fees. Found on the Statement of Operations. |
| `fund_gain_loss_realized` | The net realized gains or losses during the duration specified in `report_period` (prioritizing YTD). Found on the Statement of Operations. Return positive for gains, negative for losses. |
| `fund_contributions` | Capital contributions received from Limited Partners during the `report_period`, sourced exclusively from the 'Limited Partners' column of the Statement of Changes in Partners' Capital. |
| `fund_distributions` | Distributions paid to Limited Partners during the `report_period`, sourced exclusively from the 'Limited Partners' column of the Statement of Changes in Partners' Capital. |
| `fund_accrued_carry` | The cumulative, unpaid carried interest or performance allocation accrued by the General Partner as of the `report_date`. This is a balance sheet figure. |

#### F2: Portfolio-Level Financial Statement Fields

| Field | Definition |
|---|---|
| `investment_name` | Extract the name of the portfolio investment. Return the name exactly as stated in the document, preserving casing and punctuation. |
| `investment_first_investment_date` | The earliest recorded investment date. Typically found in the Schedule of Investment. Return in DD-MM-YYYY format. |
| `investment_type` | Classify the investment as either a `'Company'` or a `'Fund'`. |
| `investment_geography` | The primary country or region of operation. Do not extract city-level data. Return location exactly as written. |
| `investment_currency` | The currency used for reporting for this specific investment if different from `report_currency`. Return the 3-letter ISO code. |
| `investment_instrument` | The type of financial instrument (e.g., 'Equity', 'Convertible Note'). Return the specific term used. |
| `investment_industry` | The industry classification of the portfolio company. Return as written. |
| `investment_ownership` | The fund's fully diluted ownership percentage in the portfolio company as of the report date. Return null if not available. |
| `investment_total_cost` | The cost of the investment as of the `report_date`. If multiple costs exist for a single `investment_name`, sum them. Usually found in the Schedule of Investments. |
| `investment_unrealized` | The current fair value of the investment as of the `report_date`, usually labeled 'Fair Value', 'FMV', 'unrealized value' or 'Carrying Value'. If multiple values exist, sum them. |
| `investment_realized` | The total proceeds or distributions received from the investment as of the `report_date`. Return the full numerical value in fund currency. |
| `investment_exit_date` | The date the fund fully exited or wrote off the investment. Return in DD-MM-YYYY format. |
| `investment_irr` | The Internal Rate of Return (IRR) for this specific investment. Return the value as presented, or null if not available. |

---

### Schema G — Limited Partnership Agreement (LPA)

This schema applies to LPA documents or LPA summaries that define the legal and economic terms of the fund.

| Field | Definition |
|---|---|
| `fund_name` | Extract the exact legal name of the Fund entity per the LPA. If not present, return null. |
| `management_fee` | Summarize the Management Fee. State the rate and basis during the Investment Period. Detail any step-down. If not present, return null. |
| `distribution_waterfall` | Summarize the order of the Distribution Waterfall. Note if it's 'whole-fund' (European) or 'deal-by-deal' (American). If not present, return null. |
| `preferred_return` | Summarize the Preferred Return. State the percentage and how it is calculated. If not present, return null. |
| `carried_interest` | Summarize the Carried Interest. State the GP's percentage. If not present, return null. |
| `gp_catch_up` | Summarize the GP Catch-Up. State its percentage and its exact position in the waterfall. If not present, return null. |
| `clawback_provision` | Summarize the Clawback. Specify who is liable, if it's 'net of taxes,' and any time limits. If not present, return null. |
| `gp_commitment` | Summarize the GP Commitment. State the specific dollar amount or percentage. If not present, return null. |
| `capital_call_mechanics` | Summarize the notice period for Capital Calls. If not present, return null. |
| `recycling_provision` | Summarize the Recycling provision. State the limit and the time period it is permitted. If not present, return null. |
| `lpac_governance` | Summarize the LPAC's composition and list the key actions that require LPAC consent. If not present, return null. |
| `key_person_event` | Summarize the Key Person provision. List the names of 'Key Persons' and the exact consequences of an event. If not present, return null. |
| `gp_removal_provisions` | Summarize GP Removal for Cause and No-Fault (if applicable). State the LP voting threshold. If not present, return null. |
| `conflicts_and_affiliates` | Summarize how Conflicts of Interest and Affiliate Transactions are handled. If not present, return null. |
| `gp_liability_standard` | Summarize the GP's liability standard (e.g., 'gross negligence,' 'willful misconduct'). If not present, return null. |
| `fund_term_and_extensions` | Summarize the Fund Term. State the initial duration and the extension provisions. If not present, return null. |
| `investment_period` | Summarize the Investment Period. State its length and key early termination triggers. If not present, return null. |
| `reporting_requirements` | Summarize the Reporting requirements. List the key reports and their deadlines. If not present, return null. |
| `valuation_policy` | Summarize the Valuation methodology. If not present, return null. |
| `investment_limitations` | Summarize the key Investment Limitations and major restrictions. If not present, return null. |
| `fund_level_borrowing` | Summarize the Fund Borrowing limits. State the percentage limit and purpose. If not present, return null. |
| `co_investment_rights` | Summarize the Co-Investment policy and how opportunities are allocated. If not present, return null. |
| `transfer_of_interests` | Summarize the restrictions on an LP's ability to Transfer their Interest. If not present, return null. |
| `lp_default` | Summarize the key remedies and penalties for an LP Default. If not present, return null. |
| `amendments` | Summarize the voting thresholds required to Amend the LPA. If not present, return null. |
| `mfn_side_letters` | Summarize the Most Favored Nation (MFN) provision. Specify the commitment threshold and election process. If not present, return null. |
| `fund_expenses` | Summarize the 'Fund Expenses' clause. Confirm GP overhead is excluded. State the cap on 'Organizational Expenses'. If not present, return null. |
| `lp_excuse_rights` | Summarize the 'LP Excuse Rights.' List the primary reasons an LP can be excused from an investment. If not present, return null. |
| `future_funds` | Summarize the 'Future Funds' or 'Successor Fund' clause. State the threshold that permits the GP to raise a new fund. If not present, return null. |
| `distributions_in_kind` | Summarize the 'Distributions-in-Kind' clause. Specify how such assets are valued. If not present, return null. |

---

### Extraction Rules (All Schemas)

1. **Exact extraction** — Extract data as specified. Do not infer or calculate unless a rule explicitly permits it.
2. **Missing values** — Use `""` for missing strings, `null` for missing numbers.
3. **Monetary values** — Full numbers, no currency symbols or commas (e.g. `$1.5M` → `1500000`).
4. **Scale indicators** — Apply stated scale ("in thousands" → multiply by 1,000).
5. **Dates** — `DD-MM-YYYY` format (e.g. `Mar 2021` → `01-03-2021`).
6. **Portfolio companies** — Extract ALL unique direct investments (active, exited, partial exits, write-offs, mentioned in passing, new, follow-on). Exclude indirect/underlying investments. One entry per company; use the most complete data across all sections.
7. **Currency** — Use fund reporting currency. No conversions unless an explicit exchange rate is provided.
8. **Ownership** — Fund's stake in the company, not a partner's stake in the fund.

---

## STAGE 2 — Convert the Entire PDF to Markdown

> 🔴 **PROCESS THE FULL DOCUMENT. Do not skip, summarize, or omit any section.**

> ⛔ **ANTI-TRUNCATION DIRECTIVE — THIS IS MANDATORY:**
> - **Reproduce every word.** Every sentence, paragraph, heading, list item, footnote, disclaimer, and caption must appear in the output verbatim or as a faithful Markdown equivalent. Nothing may be omitted.
> - **Do not summarize prose.** Do not replace any paragraph, section, or block of body text with a shorter summary, a "[…]" ellipsis, a "(continued)" note, or any other placeholder. Reproduce the original text in full.
> - **Do not skip pages.** Every page of the PDF — including cover pages, table of contents, appendices, footnotes, legal disclaimers, and back covers — must appear in Section 2.
> - **Do not stop early.** If the document is long, continue outputting until the very last page is included. Do not stop because of output length concerns.
> - **Repeat content if necessary.** If a section header or disclaimer appears multiple times in the source document, reproduce it every time it appears.

Convert every page of the PDF to Markdown, preserving the document's structure. Apply the following rules:

### Text Content
- **Reproduce word-for-word.** Every sentence and paragraph must appear exactly as written in the source document. Do not paraphrase, condense, or abbreviate any body text.
- Reproduce all headings, sub-headings, paragraphs, bullet points, and numbered lists using proper Markdown syntax (`#`, `##`, `-`, `1.`, etc.).
- Preserve emphasis (bold, italic) where present.
- Include all footnotes, endnotes, disclaimers, legal notices, and fine print exactly as they appear.

### Tables
- Convert every table to a Markdown table.
- If a table is too wide or complex, render it as a code block (```` ``` ````) with column-aligned plain text to preserve readability.
- Add a heading above each table: `#### [TABLE: <descriptive title>]`
- Add an explanation below each table (2–4 sentences) describing: what the table shows, the time period it covers, the units used, and any notable values or trends visible.
- Tag complex tables with: `<!-- TABLE: <descriptive title> -->`

### Charts, Graphs, and Diagrams
- For every chart, graph, or visual diagram found, insert a clearly labeled block:
  ```
  <!-- CHART: <chart title or description> -->
  #### [CHART: <chart title or description>]
  **Type:** <e.g. Bar chart, Pie chart, Line graph, Waterfall chart>
  **Title:** <exact title from the document, or "Untitled" if absent>
  **Location:** <page number and position, e.g. "Page 4, top-right">
  **Axes / Legend:** <describe axes labels, units, and legend entries>
  **Key Data Points:** <list the most important values, peaks, or trends visible>
  **Context:** <2–3 sentences explaining what this chart represents in the context of the document>
  ```

### Images, Logos, and Non-Text Visuals
- For each image or non-text visual, insert:
  ```
  <!-- IMAGE: <description> -->
  #### [IMAGE: <description>]
  **Location:** <page number and position>
  **Description:** <what the image shows>
  **Context:** <why it appears here and what it relates to in the document>
  ```

### Page Breaks
- Insert `---` between pages to preserve document flow.
- Add a page label before each section: `<!-- PAGE: <n> -->`

### Integrity Tags (for LLM navigation)
Use the following inline tags throughout the Markdown to help any LLM consuming this file quickly locate information:

| Tag | Purpose |
|---|---|
| `<!-- FUND-LEVEL -->` | Marks the section containing fund-level financial data |
| `<!-- PORTFOLIO-COMPANY: <name> -->` | Marks the start of each portfolio company section |
| `<!-- FINANCIALS -->` | Marks a financial data table or paragraph |
| `<!-- MANAGER-LETTER -->` | Marks the manager's letter or quarterly commentary |
| `<!-- KPI: <metric> -->` | Inline tag for a specific key metric (e.g. `<!-- KPI: NAV -->`) |
| `<!-- EXIT: <company> -->` | Marks any exit or write-off event |
| `<!-- NEW-INVESTMENT: <company> -->` | Marks any new investment announcement |
| `<!-- WARNING: <reason> -->` | Marks a data point that is ambiguous, implied, or requires judgment |

Insert these tags as HTML comments immediately before the relevant paragraph, table, or heading.

### Final Check Before Moving to Stage 3

> ✅ Before proceeding, confirm:
> - [ ] Every page of the PDF is represented in the Markdown output above.
> - [ ] No paragraph has been replaced with a summary, ellipsis, or placeholder.
> - [ ] All tables have been fully rendered — no rows or columns are missing.
> - [ ] All footnotes, disclaimers, and appendices are included.
> - [ ] The output has not been cut off mid-sentence or mid-section.
>
> If any check fails, go back and complete the missing content before continuing.

---

## STAGE 3 — Extract Schema Data

Using the schema you identified in Stage 1, extract all relevant fields from the document. If no schema matched, skip this stage entirely and proceed to Stage 4.

---

## STAGE 3.5 — Write the Investment Professional Summary

After completing Stage 3, write a concise summary of the document **from the point of view of an investment professional reviewing this document**.

- **If the document matched a schema:** Base the summary on the extracted schema fields. Interpret the data in terms of business logic and investment significance — e.g., fund performance vs. commitment, capital deployment pace, NAV trends, LP cash flow implications, key terms, or portfolio health. Always ground the summary in the specific numbers and facts extracted.
- **If the document did not match any schema:** Base the summary on the full Markdown text from Stage 2 instead.
- **In both cases:** The summary must be written in plain prose, no more than **300 words**, and must always be from the perspective of an investment professional assessing what matters, what stands out, and what warrants attention.
- **Do not** restate field labels or reproduce raw data tables — synthesize and interpret.

---

## STAGE 4 — Compile the Output `.md` File

Produce a single `.md` file structured exactly as follows:

---

```
# [Fund Name] — Extracted Report
> Generated by AI extraction pipeline | Source: [PDF filename or "uploaded document"] | Extraction date: [today's date]

---

> 🟢 **DOCUMENT SCHEMA IDENTIFICATION:**
> This document has been identified as: **[Schema Name and Letter, e.g. "Schema A — Fund Report (Quarterly / Annual)"]**
> Fund-Level Schema: **[e.g. A1: Fund-Level Fields]** | Portfolio Schema: **[e.g. A2: Portfolio Company Fields, or "N/A"]**
>
> *(If no schema matched, omit this block entirely and begin directly with the LLM Reading Instructions below.)*

---

> 🔴 **LLM READING INSTRUCTIONS:**
> Read the Schema Block (Section 1) in full before reading the Document Content (Section 2).
> The Schema Block contains all extracted structured data. The Document Content is the full source text.
> Use the inline tags (<!-- TAG -->) throughout the document to navigate to specific data points quickly.
> When a field value conflicts between sections, prefer the value tagged with <!-- FINANCIALS --> over narrative text.

---

# SECTION 0 — INVESTMENT PROFESSIONAL SUMMARY
<!-- SUMMARY-START -->

*[Insert the ≤300-word investment professional summary here. Written in plain prose. Interprets the document from the perspective of an investor or investment analyst — what the numbers mean, what stands out, and what warrants attention. If no schema was matched, this is based on the full document text.]*

<!-- SUMMARY-END -->

---

# SECTION 1 — EXTRACTED SCHEMA DATA
<!-- SCHEMA-START -->

## Report Metadata

| Field | Value |
|---|---|
| *(fields from the matched schema go here)* | |

---

## Portfolio Companies *(if applicable — repeat block below for each company)*

### [Company Name]
<!-- PORTFOLIO-COMPANY: [Company Name] -->

| Field | Value |
|---|---|
| *(portfolio-level fields from the matched schema go here)* | |

<!-- END PORTFOLIO-COMPANY: [Company Name] -->

<!-- SCHEMA-END -->

---

# SECTION 2 — FULL DOCUMENT MARKDOWN

> This section contains the complete Markdown conversion of the source PDF.
> All tables, charts, images, and non-text objects are described in full.
> Use the inline <!-- TAGS --> to navigate to specific sections.

[PASTE THE COMPLETE MARKDOWN OUTPUT FROM STAGE 2 HERE IN FULL — every page, every paragraph, every table, every footnote. Do NOT summarize, truncate, or abbreviate anything. If the document is long, continue until the very last page is rendered. This section must be a complete, faithful reproduction of the entire PDF in Markdown format.]
```

---

## Output Rules

- **One file per PDF:** Each PDF is processed independently. Produce one `.md` output file per source PDF — do not combine multiple PDFs into a single file.
- **Output format:** `.md` file only. No JSON. No plain text. No additional commentary outside the `.md` structure above.
- **Naming:** The output file must use the **exact same filename as the source PDF**, with the extension changed to `.md` (e.g. `Q4_2023_NovastarIII.pdf` → `Q4_2023_NovastarIII.md`). Do not rename based on fund name or report date.
- **Completeness:** Every page of the PDF must appear in Section 2 in full. **Truncation of any kind is a critical failure.** This includes: stopping early, summarizing paragraphs, replacing content with ellipses or placeholders, omitting pages, or condensing tables. If the output is long, continue until every page is fully rendered.
- **Schema identification first:** The schema identification statement always appears before Section 1. If no schema matched, omit it entirely.
- **Schema first:** Section 1 (schema) always precedes Section 2 (document).
- **Self-contained:** The file must be readable and navigable by another LLM without access to the original PDF.

---

## Gold Standard Reference (Calibration)

Use the examples below to calibrate extraction accuracy, field values, and formatting.

### Fund-Level Example (Schema A1)

| Field | Value |
|---|---|
| `fund_name` | Novastar Ventures Africa Fund II LP |
| `report_date` | 31-12-2023 |
| `fund_investment_region` | East and West Africa |
| `report_currency` | USD |
| `fund_vintage` | 2018 |
| `fund_commitment` | 108080000 |
| `fund_capitalinvested` | 74419805 |
| `fund_contributions` | 87962485 |
| `fund_distributions` | 111592 |
| `fund_nav` | 128592553 |
| `fund_investment_assets` | 125332802 |
| `fund_letterupdate` | The fourth quarter of 2023 continued to reflect a challenging global venture capital environment, with venture funding in Africa falling 46% year-over-year to $3.5 billion. Growth-stage investments were particularly affected, and the absence of large rounds limited exit opportunities for early-stage investors, leading to several startup failures and down rounds. Despite the downturn, the fund's portfolio showed resilience, with some companies like Moniepoint and Poa demonstrating extraordinary growth in local currencies. The fund's valuations remained steady, with the portfolio's fair value at $125.3 million, representing a 1.68x multiple on invested capital. The fund completed two new investments in the quarter, a $5 million investment in KOKO Networks and a $1.5 million follow-on in mPharma. |

### Portfolio Company Example (Schema A2)

| Field | Value |
|---|---|
| `investment_name` | MPharma |
| `investment_description` | mPharma seeks to provide better access to affordable primary healthcare for African consumers. They do so by owning and operating their own pharmacies, by franchising to third party pharmacists, and by providing a health management programme with access to virtual doctors for customers (mutti). |
| `investment_update` | mPharma's Q4 was focused on rightsizing the business after securing a last-minute internal round. The company laid off over 300 staff, shut down its wholesale and diagnostics units, and rationalized its franchise portfolio, resulting in a 62% decline in Q4 revenues. However, these measures improved gross margins significantly and reduced monthly cash burn, positioning the company to target positive EBITDA and cash flow in 2024. |
| `investment_geography` | Ghana |
| `investment_first_investment_date` | 03-05-2019 |
| `investment_ownership` | 10.14 |
| `investment_total_cost` | 13500028 |
| `investment_realized` | null |
| `investment_unrealized` | 15257460 |
| `investment_industry` | Pharmaceutical |
| `investment_irr` | null |
| `investment_exit_date` | null |
| `investment_currency` | USD |
| `investment_revenue` | 3347856 |
| `investment_ebitda` | -1616907 |
| `investment_cash` | 4611569 |
| `investment_fte` | 711 |
