# Fund Report — Full Extraction & Markdown Generation Prompt

> **Purpose:** A single, end-to-end instruction for any LLM. This prompt applies to **each PDF individually**. When given one or more PDFs, process each one independently and produce **one `.md` output file per PDF**. Each output file is named after its source PDF (same filename, `.md` extension). The LLM will:
> 1. Identify which schema(s) the document matches.
> 2. Enhance the baseline text extraction with rich Markdown formatting and structural navigation tags.
> 3. Extract the structured schema data.
> 4. Write a Document Navigator — a structural and contextual guide that helps an LLM reader quickly locate key information.
> 5. Produce **one `.md` output file per PDF**, named identically to the source PDF (e.g. `Q4_2023_Report.pdf` → `Q4_2023_Report.md`).

---

## ⚡ SINGLE INSTRUCTION TO THE LLM

You are a meticulous financial document processing agent. You will receive one or more financial documents — these may include fund reports, capital call notices, distribution notices, financial statements, limited partnership agreements, **press releases, investor presentations, pitch decks, prospectuses, offering memoranda, term sheets, excel financial models, portfolio company updates, board packs, co-investment memos, deal tear sheets, due diligence reports, side letters, annual audits, valuation reports, or any other document related to investing in a company or a fund.** **Process each document independently** — carry out all stages below for each document in sequence and produce **one `.md` output file per document**. Do NOT produce JSON. Do NOT produce plain text. Each output file must be valid Markdown, saved with the **same filename as its source document** but with a `.md` extension.

---

## STAGE 1 — Identify the Document Schema

> 🔴 **IMPORTANT — BEFORE READING THE DOCUMENT, IDENTIFY WHICH SCHEMA IT BELONGS TO.**
> Review all schemas listed below (A through G). Once you have identified the correct schema(s) for this document, state that identification at the very top of your output file (see Stage 4 for the exact format).
> **If the document does not match any of the predefined schemas A–G**, apply **Schema H — General Financial Document (Auto-Detected)**. In this mode, you will dynamically identify and extract the most relevant fields based on the document's actual content. See Schema H for full instructions.

The following schemas are available. A document may match **one primary schema** (for its fund-level data) and one **portfolio-level schema** (for its investment data). Identify the best match for each. If none of the predefined schemas (A–G) fit, use Schema H.

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
| `fund_capitalinvested` | Cumulative capital invested into all companies (active + exited). NOT capital called or committed. Often labeled "Invested Cost" or "Total Cost." If multiple numbers are provided, use the more precise number (e.g., prefer `74419805` over `74.4M`). |
| `fund_contributions` | Total capital called from investors since inception. Also called "Capital Contributions." Include both GP and LP. |
| `fund_distributions` | Cumulative distributions to all partners since inception. Found in Statement of Changes in Partners' Capital. DO NOT use portfolio-level "Realized Proceeds" or "Exit Value." |
| `fund_nav` | Net Asset Value = Total Assets − Total Liabilities. Also called "Partners' Capital" or "Total Partners' Equity." Found at bottom of Balance Sheet. |
| `fund_investment_assets` | Fair value of assets invested in portfolio companies as of report date. Usually "Investments at Fair Value." |
| `fund_letterupdate` | 3–6 sentence summary of the manager's letter or quarterly update. Focus on performance, strategy, market outlook. Support with figures. |

#### A2: Portfolio Company Fields

| Field | Definition |
|---|---|
| `investment_name` | Name exactly as stated. Use holding company name if both holding and operating names appear. Ignore parenthetical qualifiers (e.g., in "Delta Company (held via Argonaut)", capture only "Argonaut" if Argonaut is the holding entity). **Fuzzy deduplication:** carefully check for company names that are similar (e.g., "Charlie Company" vs. "Charlie Company Ltd", or "Sangri la Management" vs. "Sangrila") and treat them as the same entity — use the most formal/complete name. |
| `investment_description` | 1–2 sentences: sector, industry, core activities, business model (e.g. SaaS, marketplace). |
| `investment_update` | 2–3 sentences on the company's progress, challenges, or key events for the current reporting period. |
| `investment_geography` | Primary country of operation. Full country name. NOT city-level. |
| `investment_first_investment_date` | Earliest recorded investment date. Format: `DD-MM-YYYY`. |
| `investment_ownership` | Fund's fully diluted ownership % of the company's equity. NOT a partner's share of the fund. |
| `investment_total_cost` | Cumulative investment cost. Labeled "Cost" or "Invested Capital." If a company appears multiple times (e.g., different security types: Common, Preferred, Seed, Series A), sum all associated cost values. Prefer fund currency. |
| `investment_unrealized_cost` | The unrealized cost basis — the original cost of the portion of the investment that has NOT been sold, exited, or written off. Found in "Schedule of Investments" or "Portfolio Metrics" tables. If a company has multiple entries (different security types or rounds), sum all unrealized cost values. If a number appears with large spaces (e.g., "5 34,567"), interpret it correctly as a monetary value. |
| `investment_realized` | Total amount realized from the company (partial or full exits). If a company has multiple entries (different security types or rounds), sum all realized values. |
| `investment_unrealized` | Current fair value ("Fair Value," "FMV," "Carrying Value"). Prefer fund currency. If multiple values exist for the same investment (different security types or rounds), sum the values. |
| `investment_industry` | Industry or sector label exactly as written. |
| `investment_irr` | Investment-level IRR (not fund-level). Expressed as a percentage. Not MOIC or MOI. |
| `investment_exit_date` | Date of full exit or write-off. Format: `DD-MM-YYYY`. |
| `investment_currency` | Currency in which the portfolio company reports its financials. May be explicitly labeled, or inferred from column headers (e.g., "(in USD)", "Figures in INR"). 3-letter ISO code. |
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

### Schema H — General Financial Document (Auto-Detected)

This schema applies to **any financial document that does not match schemas A–G**. Examples include but are not limited to: press releases, investor presentations, pitch decks, prospectuses, offering memoranda, term sheets, excel financial models, portfolio company updates, board packs, co-investment memos, deal tear sheets, due diligence reports, side letters, annual audits, valuation reports, AGM minutes, subscription agreements, placement agent reports, and any other investment-related document.

> 🔴 **AUTO-DETECT MODE:** When you identify a document as Schema H, you must **dynamically construct an appropriate extraction schema** based on the document's actual content. Do NOT leave Section 1 empty. Instead, scan the entire document and extract every investment-relevant data point you can identify, organizing them into the two tables below.

#### H1: Document Metadata & Key Figures (Always extract these if present)

| Field | Definition |
|---|---|
| `document_type` | Classify the document (e.g., "Press Release", "Prospectus", "Investor Presentation", "Term Sheet", "Financial Model", "Board Pack", "Due Diligence Report", "Valuation Report", "Side Letter", "Co-Investment Memo", "Deal Tear Sheet", "AGM Minutes", "Subscription Agreement", or describe it). |
| `document_title` | The title or header of the document exactly as written. |
| `document_date` | The date of the document (issuance, publication, or effective date). Format: `DD-MM-YYYY`. |
| `entity_name` | The primary company, fund, or entity the document relates to. Return exactly as written. |
| `counterparty_name` | If applicable, the other party (e.g., acquirer in an M&A deal, lead investor in a round, LP in a side letter). Null if not applicable. |
| `currency` | The primary currency used in the document. 3-letter ISO 4217 code. |
| `document_summary` | A 3–6 sentence summary of the document's purpose, key conclusions, and most important figures. Written for an investment professional. |

#### H2: Auto-Detected Fields (Dynamically generated based on document content)

Scan the document and extract **every quantitative and qualitative data point that an investment professional would find relevant**. For each data point you identify, create a row in the extraction table using a descriptive field name and a precise definition. Use the style and rigor of the predefined schemas above.

**Categories to scan for (extract all that are present in the document):**

**Valuation & Pricing:**
`pre_money_valuation`, `post_money_valuation`, `share_price`, `price_per_share`, `implied_ev`, `ev_ebitda_multiple`, `ev_revenue_multiple`, `price_earnings_ratio`, `discount_rate`, `terminal_value`, `enterprise_value`, `equity_value`, `offer_price`, `ipo_price_range`, `dcf_valuation`, `comparable_valuation`, `precedent_transaction_valuation`

**Deal & Transaction Terms:**
`transaction_type` (e.g., Series A, M&A, IPO, Secondary, Buyout, Restructuring), `round_size`, `total_raise`, `deal_value`, `acquisition_price`, `equity_stake_offered`, `dilution_percentage`, `option_pool`, `liquidation_preference`, `anti_dilution_provision`, `drag_along_rights`, `tag_along_rights`, `right_of_first_refusal`, `board_seat_allocation`, `investor_rights`, `vesting_schedule`, `lock_up_period`, `break_fee`, `exclusivity_period`, `closing_conditions`, `regulatory_approvals_required`

**Financial Metrics (Company-Level):**
`revenue`, `revenue_growth_yoy`, `revenue_growth_qoq`, `gross_profit`, `gross_margin`, `ebitda`, `ebitda_margin`, `net_income`, `net_margin`, `free_cash_flow`, `operating_cash_flow`, `capex`, `total_assets`, `total_liabilities`, `total_equity`, `total_debt`, `net_debt`, `cash_and_equivalents`, `working_capital`, `accounts_receivable`, `accounts_payable`, `inventory`, `burn_rate`, `runway_months`, `arr` (Annual Recurring Revenue), `mrr` (Monthly Recurring Revenue), `ltv` (Customer Lifetime Value), `cac` (Customer Acquisition Cost), `ltv_cac_ratio`, `churn_rate`, `nrr` (Net Revenue Retention), `gmv` (Gross Merchandise Value), `take_rate`, `aum` (Assets Under Management)

**Fund & LP-Specific Metrics:**
`tvpi`, `dpi`, `rvpi`, `moic`, `net_irr`, `gross_irr`, `pme` (Public Market Equivalent), `j_curve_position`, `fund_size`, `capital_called_percentage`, `unfunded_commitment`, `management_fee_rate`, `carry_rate`, `hurdle_rate`, `gp_commitment_amount`, `fund_term_remaining`

**Operational & Market Data:**
`total_customers`, `new_customers`, `customer_retention_rate`, `headcount`, `headcount_growth`, `market_size_tam`, `market_size_sam`, `market_share`, `geographic_breakdown`, `revenue_by_segment`, `revenue_by_geography`, `key_customers`, `customer_concentration`, `competitive_landscape`, `regulatory_status`, `patent_portfolio`, `technology_stack`

**Projections & Forecasts:**
`revenue_forecast`, `ebitda_forecast`, `cash_flow_forecast`, `growth_rate_assumption`, `exit_multiple_assumption`, `base_case_irr`, `upside_case_irr`, `downside_case_irr`, `expected_exit_year`, `expected_exit_type` (IPO, Trade Sale, Secondary, etc.)

> **Instructions for auto-detected fields:**
> - Only extract fields that are **actually present** in the document. Do NOT fabricate values.
> - Use the exact field names above when they match. If a data point does not fit any of the names above, create a new descriptive `snake_case` field name.
> - For each field, provide both the **value** and a brief note on **where in the document** it was found (e.g., "Page 3, Summary Table").
> - If the document contains **projection models or scenario analyses** (base/bull/bear cases), extract each scenario as a separate set of fields with a suffix (e.g., `revenue_forecast_base`, `revenue_forecast_bull`, `revenue_forecast_bear`).
> - If the document contains **time-series data** (e.g., 5-year revenue history), extract each period as a separate row or use a compact table format.
> - Apply all monetary, date, and scale rules from the Extraction Rules section below.

---

### Extraction Rules (All Schemas including Auto-Detected)

1. **Exact extraction** — Extract data as specified. Do not infer or calculate unless a rule explicitly permits it.
2. **Missing values** — Use `""` for missing strings, `null` for missing numbers.
3. **Monetary values** — Full numbers, no currency symbols or commas (e.g. `$1.5M` → `1500000`).
4. **Scale indicators** — Apply stated scale ("in thousands" → multiply by 1,000).
5. **Dates** — `DD-MM-YYYY` format (e.g. `Mar 2021` → `01-03-2021`).
6. **Portfolio companies** — Extract ALL unique direct investments (active, exited, partial exits, write-offs, companies mentioned in passing, new investments, follow-on investments, and any entity the fund has ever directly invested in). Include investments in other funds (e.g., LP interests). Exclude indirect/underlying investments. One entry per company; use the most complete data across all sections.
7. **Currency** — Use fund reporting currency. No conversions unless an explicit exchange rate is provided. If consolidating multiple vehicles, only sum figures that share the same reporting currency.
8. **Ownership** — Fund's stake in the company, not a partner's stake in the fund.
9. **Multi-entry summing** — When a company appears multiple times in a table (e.g., different security types: Common, Preferred, Seed, Series A), sum all associated values (cost, realized, unrealized) for that company into a single entry.
10. **Fuzzy name deduplication** — Carefully check for company names that are similar (e.g., "Charlie Company" vs. "Charlie Company Ltd", or "Sangri la Management" vs. "Sangrila"). Treat them as the same entity and use the most formal/complete version of the name.
11. **Malformed numbers** — If a number appears with unexpected large spaces (e.g., "5 34,567"), interpret it correctly as a single monetary value ($534,567). PDF extraction artifacts must not cause incorrect parsing.
12. **Definition priority** — When a conflict exists between a field's definition in this prompt and any schema description metadata, follow the field definition in this prompt.
13. **Precision** — If both a rounded number and a more precise figure are available for the same data point, always use the more precise number (e.g., prefer `2456000` over `2.4M` or `2,456 (in thousands)`).
14. **Multi-vehicle consolidation** — When a document covers multiple fund vehicles, prioritize consolidated fund-level figures. Only sum figures across vehicles if they share the same reporting currency.

---

## STAGE 2 — Generate Structural Tags (JSON)

> 🔴 **NON-DESTRUCTIVE MODE: You are no longer responsible for rewriting the document body.**
> The baseline text provided to you will be used as the final document body completely unmodified to guarantee zero data loss.
> Your role is to generate a list of structural tags that the Python pipeline will mechanically inject into the baseline text.

Produce a JSON array of tags and the exact text snippet indicating where they should be inserted.

### Tag Types to Generate:
1. `<!-- TABLE-START: <title> | rows:<N> | cols:<N> | has_merged_cells:<yes/no> | has_subtotals:<yes/no> | data_type:<type> -->` (and `<!-- TABLE-END: <title> -->`)
2. `<!-- CHART-START: <title> -->` (and `<!-- CHART-END: <title> -->`)
3. `<!-- PORTFOLIO-COMPANY: <name> -->`
4. `<!-- FUND-LEVEL -->`
5. `<!-- FINANCIALS -->`
6. `<!-- KPI: <metric> -->`
7. `<!-- EXIT: <company> -->` / `<!-- NEW-INVESTMENT: <company> -->`

### JSON Patch Format:
For every tag, generate a JSON object:
```json
{
  "tag": "<!-- THE EXACT TAG -->",
  "insert_before_exact_string": "A 10-20 word snippet of text directly from the baseline immediately FOLLOWING where the tag should be placed"
}
```

**CRITICAL:** The `insert_before_exact_string` must be a verbatim, exact copy-paste from the baseline text. If it doesn't match perfectly, the tag will fail to inject. Do not invent tags for content that doesn't exist in the baseline.

---

## STAGE 3 — Extract Schema Data

Using the schema you identified in Stage 1, extract all relevant fields from the document. If no schema matched, skip this stage entirely and proceed to Stage 4.

---

## STAGE 3.5 — Write the Document Navigator

After completing Stage 3, write a **Document Navigator** — a structural and contextual guide designed to help an LLM reader quickly understand what this document contains and where to find specific information.

> 🔴 **CRITICAL: The Document Navigator is purely descriptive and structural. It does NOT provide investment advice, subjective assessments, or buy/hold/sell analysis. Its purpose is to be a map of the document that helps a reader (human or LLM) navigate efficiently.**

### Document Overview
Write 2–3 sentences describing what this document is, who produced it, and what period it covers.

### Section Index
List every major section of the document with its page range. Use the `<!-- PAGE: N -->` markers from Section 2 as references. This should read like a detailed table of contents.

### Table Index
Create a reference table listing every table found in Section 2:

| # | Table Title | Page | Key Data Available |
|---|---|---|---|
| 1 | *(title from TABLE-START tag)* | *(page number)* | *(brief description of what data this table contains)* |

### Chart Index
Create a reference table listing every chart found in Section 2:

| # | Chart Title | Page | Type | Key Insight |
|---|---|---|---|---|
| 1 | *(title from CHART-START tag)* | *(page number)* | *(chart type)* | *(one-line description of what the chart shows)* |

### Key Entities
List the companies, funds, people, and organizations mentioned in the document with page references where they first appear or are most discussed.

### Key Metrics Quick Reference
Create a reference table listing the most important numerical data points found in the document:

| Metric | Value | Location |
|---|---|---|
| *(metric name, e.g. NAV, Revenue, Fund Size)* | *(the value)* | *(Page N, Section/Table name)* |

This table should surface the "headline numbers" so an LLM reader can get key facts without scanning the entire document.

### Navigation Tips
Provide 3–5 bullet points guiding an LLM reader on the most efficient way to consume this document:
- Where to find financial statements
- Where to find portfolio company details
- Which tables contain the most comprehensive data
- Which sections contain forward-looking information
- Which content is repetitive and can be skipped (tagged with `<!-- REPEATED-* -->`)

**Formatting rules:**
- Tag the section with `<!-- NAVIGATOR-START -->` and `<!-- NAVIGATOR-END -->`.
- Be precise with page references — always use the page numbers from Section 2.
- Focus on being useful to a machine reader: concise, structured, scannable.

---

## STAGE 4 — Compile the Output `.md` File

Produce a single `.md` file structured exactly as follows:

---

```
# [Entity Name] — Extracted Report
> Generated by AI extraction pipeline | Source: [source filename or "uploaded document"] | Extraction date: [today's date]

---

> 🟢 **DOCUMENT SCHEMA IDENTIFICATION:**
> This document has been identified as: **[Schema Name and Letter, e.g. "Schema A — Fund Report (Quarterly / Annual)" or "Schema H — General Financial Document (Auto-Detected)"]**
> Primary Schema: **[e.g. A1: Fund-Level Fields, or H1: Document Metadata]** | Secondary Schema: **[e.g. A2: Portfolio Company Fields, H2: Auto-Detected Fields, or "N/A"]**
> Document Type: **[e.g. "Quarterly Fund Report", "Press Release", "Prospectus", "Financial Model", etc.]**
> This document contains **two complementary data sources**: (1) Extracted Schema Data and (2) Full Document Content with structural navigation tags. Consult the Document Navigator (Section 0) for a structural guide to the document.

---

> 📅 **DOCUMENT DATE IDENTIFICATION:**
>
> The following dates were identified in the source document. These are listed in order of priority — the highest-priority date available should be treated as the **canonical document date** for any downstream system that needs a single reference date.
>
> | Date Key | Value | Description |
> |---|---|---|
> | `reporting_date` | **[DD-MM-YYYY or "Not found"]** | The reporting period end date (e.g., "As of December 31, 2023", "For the Quarter Ended September 30, 2024"). This is the most authoritative date for financial reports, fund reports, financial statements, and capital account statements. |
> | `publication_date` | **[DD-MM-YYYY or "Not found"]** | The date the document was published, issued, or released (e.g., press release date, prospectus date, letter date, notice date). This is the most authoritative date for press releases, notices, presentations, and memos. |
> | `metadata_date` | **[DD-MM-YYYY or "Not found"]** | A fallback date sourced from the document's metadata, headers, footers, cover page, or any other implicit date indicator (e.g., "Last updated: March 2024", copyright year, file creation date visible in the document). Use this only if neither `reporting_date` nor `publication_date` could be identified. |
>
> **Canonical Document Date:** **[DD-MM-YYYY]** *(Use `reporting_date` if found; otherwise `publication_date`; otherwise `metadata_date`. If none could be identified, state "Unknown".)*
>
> 🔴 **Instructions for identifying these dates:**
> - **`reporting_date`**: Look for phrases like "As of", "For the period ended", "For the quarter ended", "For the year ended", "Report Date", "Valuation Date". This is NOT the date the report was written or sent — it is the financial cut-off date.
> - **`publication_date`**: Look for the date on the cover page, the date in the letterhead, "Date:", "Issued:", "Published:", press release line (e.g., "NEW YORK, March 15, 2024 —"), or notice date fields.
> - **`metadata_date`**: Look for "Last updated", "Prepared on", copyright notices with a year, revision dates in footers, or any other date that indicates when the document was last produced.

---

> 🔴 **LLM READING INSTRUCTIONS:**
> This document contains two complementary data layers that should be read together:
>
> **Step 1 — Read the Document Navigator (Section 0):** Contains a structural and contextual guide to the document. Scan this first to understand what the document contains, where key tables and charts are located, and what the most important data points are. Use this as your roadmap.
>
> **Step 2 — Read the Extracted Schema (Section 1):** Contains structured, field-level data extracted from the source document. Use this for quick quantitative facts.
>
> **Step 3 — Read the Full Document Content (Section 2):** Contains the complete text of the source document. The text was extracted via Python converters and algorithmically enhanced with your structural navigation tags. Use the inline tags (`<!-- TAG -->`) to navigate to specific data points quickly.
>
> **Conflict Resolution:** When a data point conflicts between sections, apply this priority order:
> 1. Values tagged with `<!-- FINANCIALS -->` in Section 2 (highest authority — direct from source)
> 2. Extracted Schema (Section 1)
> 3. Document Navigator (Section 0) — descriptive references only
>
> **Cross-Reference Mandate:** Do NOT rely on any single section alone. The Schema may miss contextual nuance found in the full text. The full text may bury critical figures in dense prose that the Schema has surfaced. Always cross-reference for the most accurate and complete picture.

---

# SECTION 0 — DOCUMENT NAVIGATOR
<!-- NAVIGATOR-START -->

## Document Overview
*[2–3 sentences: what this document is, who produced it, and what period it covers.]*

## Section Index
*[List every major section with page ranges from the <!-- PAGE: N --> markers.]*

## Table Index

| # | Table Title | Page | Rows × Cols | Data Type | Key Data Available |
|---|---|---|---|---|---|
| *(list every table from Section 2 with its TABLE-START tag title, page number, dimensions, data type, and a brief description of what data it contains)* | | | | | |

## Chart Index

| # | Chart Title | Page | Type | Key Insight |
|---|---|---|---|---|
| *(list every chart from Section 2 with its CHART-START tag title, page, type, and one-line description)* | | | | |

## Key Entities
*[Companies, funds, people, and organizations with page references.]*

## Key Metrics Quick Reference

| Metric | Value | Location |
|---|---|---|
| *(headline numbers from the document — NAV, Revenue, Fund Size, etc.)* | | |

## Navigation Tips
*[3–5 bullet points guiding the reader to the most important sections, tables, and data.]*

<!-- NAVIGATOR-END -->

---

# SECTION 1 — EXTRACTED SCHEMA DATA
<!-- SCHEMA-START -->

## Report Metadata

| Field | Value |
|---|---|
| *(fields from the matched schema go here)* | |

---

## Key Figures — LLM-Detected

> 🔴 **Instructions:** After extracting the schema fields above, scan the ENTIRE document and extract **every significant key figure** that an investment professional would want at a glance. These are the headline numbers that define this document's value. Organize them into the table below.
>
> **Detection Rules:**
> - Extract ALL significant monetary values, percentages, dates, and counts found anywhere in the document.
> - For each figure, provide the exact label used in the source, the value, the unit/currency, and where it was found.
> - If the document is a **fund report**, prioritize: NAV, Total Commitments, Capital Called, Distributions, TVPI, DPI, RVPI, Net IRR, Gross IRR, Number of Portfolio Companies, Fund Size, Vintage Year.
> - If the document is a **capital call or distribution notice**, prioritize: Call Amount, Distribution Amount, Unfunded Commitment, Payment Due Date, Net Amount.
> - If the document is a **financial statement**, prioritize: Total Assets, Total Liabilities, Net Assets, Investment Income, Realized Gains/Losses, Unrealized Gains/Losses, Management Fees, Fund Expenses.
> - If the document is a **capital account statement**, prioritize: Beginning Balance, Contributions, Distributions, Ending Balance, Total Commitment, Unfunded Commitment.
> - If the document is an **LPA**, prioritize: Fund Size, Management Fee Rate, Carry Rate, Preferred Return, GP Commitment, Fund Term, Investment Period.
> - If the document is a **company-level document** (pitch deck, board pack, due diligence), prioritize: Revenue, EBITDA, Cash, Headcount, Valuation, Round Size, Ownership.
> - Include any other figure that appears prominent in the document (large font, bold, in a summary table, or in the executive summary).
> - Do NOT fabricate values. Only extract what is explicitly stated.

| # | Label (as written in source) | Value | Unit / Currency | Page | Source Context (table name, section, paragraph) |
|---|---|---|---|---|---|
| 1 | *(e.g. "Net Asset Value")* | *(e.g. 128592553)* | *(e.g. USD)* | *(e.g. 5)* | *(e.g. "Balance Sheet, Statement of Assets and Liabilities")* |
| 2 | ... | ... | ... | ... | ... |

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

# SECTION 3 — STRUCTURAL TAGS

> 🔴 **INSTRUCTIONS:** Output the JSON array of tags as defined in Stage 2. This must be valid JSON wrapped in a code block.

```json
[
  {
    "tag": "<!-- EXAMPLE-TAG -->",
    "insert_before_exact_string": "example verbatim text from the baseline"
  }
]
```

---

## Output Rules

- **One file per PDF:** Each PDF is processed independently. Produce one `.md` output file per source PDF — do not combine multiple PDFs into a single file.
- **Output format:** `.md` file only. No JSON. No plain text. No additional commentary outside the `.md` structure above.
- **Naming:** The output file must use the **exact same filename as the source PDF**, with the extension changed to `.md` (e.g. `Q4_2023_NovastarIII.pdf` → `Q4_2023_NovastarIII.md`). Do not rename based on fund name or report date.
- **Output validation:** The LLM output MUST contain exactly Section 0, Section 1, and Section 3 (JSON tags). Do NOT output Section 2 (the full text). The system will compile the final file.
- **Schema identification first:** The schema identification statement always appears before Section 1. If no schema matched, omit it entirely.
- **Section ordering:** Section 0 (Document Navigator) → Section 1 (Schema) → Section 3 (Structural Tags).
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
