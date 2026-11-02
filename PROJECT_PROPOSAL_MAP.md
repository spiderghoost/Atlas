# ATLAS — Global Economic Intelligence Platform

**Project title (simple):** ATLAS: An AI Website That Helps Organizations Make Economic Decisions

**Prepared:** August 2026 · **Updated:** October 2026
**Student:** Data Science undergraduate (final senior project)
**Time:** ~12 months (2 semesters)

---

## 1. What is this project?

ATLAS is a large website that organizations use to understand countries' economies. It uses AI to study a huge set of economic data — mainly the World Bank's WDI database (about 1,500 indicators for about 260 countries).

The website lets users:
- **Monitor** — see which countries are in danger of a financial crisis, and get alerts.
- **Analyze** — get early estimates of growth, inflation, and poverty before official numbers come out; get full written reports about any country, generated automatically.
- **Decide** — test "what if" scenarios ("what if a drought destroys part of the food supply?"), and get short reports (memos) that decision-makers can use.
- **Protect (real-time & personal)** — watch a 24/7 geopolitical news feed, see how each event ripples through trade → inflation → prices → a household's wallet, get a smarter monthly shopping basket, and get plain guidance on cash, gold, and bulk buying.

The AI agent can also answer questions in normal language, like "why is Ghana at risk?" — with charts and sources to back up the answer.

---

## 2. Why is this needed?

Today, analyzing a country's economy is slow and expensive:
- The data is spread across many places (World Bank, IMF, FAO, UN, satellites, financial markets).
- Analysts build separate models by hand for each country.
- Writing a single report takes days.

Meanwhile, big institutions (World Bank, IMF, Asian Development Bank) have shown that machine learning can do much of this automatically — and they recently built real systems to prove it. But **no single open system packages all of this into one product**. ATLAS fills that gap.

News moves faster than reports: when a tariff, blockade, or harvest failure hits, institutions publish in days — but prices move in hours. ATLAS closes that gap for organizations **and for the people those decisions affect**, by turning each headline into a traced impact chain and a concrete action plan.

---

## 3. Design rules (the most important ideas)

1. **All numbers are real; the AI only writes words.**
   The machine-learning models (not the chatbot) calculate every number — probabilities, forecasts, scenario impacts. The AI agent only explains results and writes reports. It can never make up numbers. This is why we can safely use a free AI model.

2. **Every model is compared to a baseline.**
   We check our results against official models from the IMF, World Bank, and Asian Development Bank. If we match or beat them, great. If not, we report it honestly. Both results are acceptable — honesty is what matters.

3. **Every number comes with uncertainty.**
   We never say "GDP will fall exactly 4.7%." We say "GDP will likely fall between 3% and 6%." This is called *uncertainty* or a *confidence range*.

4. **Everything is explainable.**
   For every result we show WHY, using a method called SHAP (which shows how much each factor contributed) and plain-language explanations.

5. **No attack planning.**
   The scenario tool is only for *resilience and preparedness* — helping organizations prepare for disasters and disruptions. It is never a tool for planning attacks. The same rule covers the new real-time layer: the pipeline's impact stage assesses *consequences only* — never targeting.

---

## 4. Who uses it? (target users)

| Who | What they use it for |
|---|---|
| Government ministries / central bank research departments | Country risk reports, debt analysis, "what if" policy tests, watchlists |
| Development agencies & NGOs | Food and energy security monitoring, poverty estimates, disaster-preparedness planning |
| Investment and risk teams at banks / asset managers | Country risk ratings, early warnings, comparing countries |
| Researchers and analysts | Exploring data and reproducing model results |
| Universities & teachers | Interactive economics lessons, crisis-solving assignments, simulation sandbox |
| Citizens & households (personal use) | Live geopolitical ripple feed with a personal "Your Pocketbook" breakdown, a smarter monthly shopping basket, and simple guidance on cash, gold, and bulk buying |

---

## 5. Goals

1. Build a clean, versioned data warehouse that combines all public data sources, with a "data quality" layer (is the data complete? fresh? trustworthy?).
2. Build the **core prediction models**: (a) early warning of financial crises (debt, currency, banking, fiscal), and (b) nowcasting (early estimates of GDP growth, inflation, poverty) — tested honestly and compared to institutional baselines.
3. Build **explanation and scenario tools** — SHAP explanations, "what if" counterfactuals, and the Shock & Resilience Studio.
4. Build the **AI agent system** (data, model, explanation, and report agents) using free local AI models, which auto-generates country reports and answers questions with citations.
5. Package everything as a **multi-page website for organizations** (accounts, teams, watchlists, alerts, reports) **plus a teaching mode** for universities (teacher + student roles).
6. Build the **real-time & personal layer** (built first — see §16): a 24/7 geopolitical ripple tracker that turns each headline into a household-level action plan (PocketRipple), a monthly household basket optimizer, and a personal wealth guard with an indicator explainer — all powered by the same free local AI models.

---

## 6. The data (all free and public)

| Dataset | What it contains | How we get it |
|---|---|---|
| **World Bank WDI** (~1,500 indicators) | Main data: economy, health, education, trade, infrastructure, environment | World Bank API |
| IMF WEO / IFS | Macro data cross-checks: debt, reserves, inflation, money | IMF API |
| World Bank Global Debt Database | Country debt numbers (for debt stress tests) | World Bank |
| FAO | Food production, food price indices, agriculture | FAO API |
| UN Comtrade / BACI | Trade between countries (to see how a shock spreads) | public download |
| World Governance Indicators / Polity | Quality of institutions | public download |
| PovcalNet | Poverty rates (to check our poverty estimates) | World Bank |
| WHO / UNESCO | Health, education data | public APIs |
| World Bank Climate Data / NASA | Temperature, disasters, droughts | Google Earth Engine |
| Satellite nightlights | City lights seen from space — a proxy for economic activity | Google Earth Engine |
| FRED / central banks | High-frequency macro and financial data | FRED API |
| Financial markets | Government bond prices, currency rates, oil/food prices | public sources |
| Google Trends | How often people search for things (extra clue for nowcasting) | pytrends |
| **Live news headlines** | Reuters, BBC, Al Jazeera and other RSS feeds — the trigger input for geopolitical ripple analysis | feedparser (every 5–10 min) |
| **Commodity & FX prices** | Gold, crude oil (Brent), USD/EGP and other pairs — live prices for the pocketbook and basket | yfinance (every 5 min) |
| **Weather observations** | Temperature, precipitation, wind per city — context for food/energy and household planning | Open-Meteo (every 30 min) |

**Storage:** everything lives in **one PostgreSQL 16 database** (with an extension called pgvector), managed by **Django's ORM**. This database stores the data tables, the user accounts, and the AI's searchable memory (called vectors / embeddings) — all in one place, so setup stays simple. Django's built-in admin panel gives a ready-made interface for managing all this data during development.

Beyond the macro warehouse, the real-time layer keeps six dedicated tables in the same database: `news_headlines`, `commodity_live_prices`, `weather_observations`, `historical_crises`, `analyses_cache`, and `user_households` (details in §16).

---

## 7. The 16 features of the website (modules)

**Core = must ship (the backbone of the project):** Modules 1, 2, 3, 4, 5, 6, 9, 11, 13, 14, 15, 16.
**Stretch = nice to have if time remains:** Modules 7, 8, 10, 12.

### Monitor (watch the world)
| # | Feature | What it does | Status |
|---|---|---|---|
| 1 | **Crisis Early Warning** | Predicts the risk of debt, currency, banking, and fiscal crises; explains why each country is at risk | Core |
| 2 | **Nowcasting & Forecasting** | Early estimates of GDP growth, inflation, poverty, and food insecurity for countries with weak data | Core |
| 3 | **Food & Energy Security Monitor** | Tracks food price spikes, import dependence, water stress — with alerts | Core |
| 4 | **Watchlists & Alerts** | Organizations save countries they care about and get alerts with explanations when risk changes | Core |

### Analyze (go deep)
| # | Feature | What it does | Status |
|---|---|---|---|
| 5 | **Debt Sustainability Analytics** | Checks if a country's debt is safe, using official-style thresholds and stress tests | Core |
| 6 | **Country Intelligence Briefs** | Automatically writes a full report about a country (in the style of an IMF country report) | Core |
| 7 | **Peer Benchmarking** | Compares countries side by side; finds "who is most similar to this country?" | Stretch |
| 8 | **Development Space** | Puts countries on a map of development dimensions and animates their path over the years | Stretch |

### Decide (take action)
| # | Feature | What it does | Status |
|---|---|---|---|
| 9 | **Shock & Resilience Studio** | Lets users test scenarios: drought, supply disruption, port closure, commodity price spike, capital flight. Shows the impact as a **range** (not a fake precise number) and compares it to real historical events (2022 Ukraine grain shock, 2021 Suez blockage, 2008 food crisis, COVID 2020). Built for disaster-preparedness, not attack planning. | Core (final showcase) |
| 10 | **Policy Counterfactual Studio** | "What if this country raised its reserves to 20% of GDP?" → shows the effect on predicted risk | Stretch |
| 11 | **Ask-the-Agent Chat** | Natural-language questions over all the data, with charts and citations | Core |
| 12 | **Report & Memo Generator** | Produces short PDF decision memos for committees (Ministry / NGO / Investor templates) | Stretch |
| 13 | **Teaching & Simulation Lab** | A professor area: pick a real country or create a synthetic "economy profile" (a simplified set of ~20–30 key parameters), set a crisis for students to solve, and students adjust economic variables in the sandbox (price bars, demand shifts, subsidies). The system explains the economic logic of each action and scores the result on a real objective (e.g., food security without creating a shortage or blowing the budget). Includes a challenge bank of real historical crises (Ukraine grain 2022, 2008 food crisis, Sri Lanka debt crisis). Reuses the Modules 9–11 engines — no new simulation math. | Core (reuses existing engines) |

### Protect (real-time & personal — built first)
| # | Feature | What it does | Status |
|---|---|---|---|
| 14 | **Live Geopolitical Ripple (PocketRipple)** | A 24/7 headline feed with an **"Important for You"** filter based on the user's location; a live bar for **Gold, Crude Oil, and Exchange Rates** with AI commentary linking prices to active headlines. Clicking a headline opens a 3-tab breakdown: (1) **Global Geopolitical Impact** — trigger, ecosystem, asymmetry check, transmission channels, impact matrix, cascading chain; (2) **Your Pocketbook** — location-specific exposure vectors (Transport, Kitchen, Utilities, Tech) plus an action plan with the badges **PRE-EMPT · SUBSTITUTE · ADAPT · PROTECT · ADVOCATE**; (3) **Historical Evidence** — the top-3 retrieved historical crises with similarity scores and what actually happened. A relevance gate screens every headline before the 6-stage AI chain runs. | Core (built first) |
| 15 | **Smart Monthly Household Basket Optimizer** | User enters salary, rent, family size, dietary constraints, and city → ATLAS returns an itemized monthly basket split across **Kitchen, Transport, and Utilities**, with item-level advice tied to local inflation forecasts (e.g., *"Rice: PRE-EMPT — buy a 2-month buffer before the expected 8% tariff hike"*). | Core (built first) |
| 16 | **Personal Wealth Guard & Indicator Explainer** | A **salary-allocation card** (local-currency liquid buffer / gold purchases / essential bulk buying) plus a searchable **"What does this indicator mean?"** drawer explaining technical metrics (FAO Food Price Index, Import Cover Ratio, Nightlight Activity) in plain words: *what it means* and *what could happen to my wallet*. | Core (built first) |

---

## 8. The AI system (agents)

We use **free local AI models** (via a tool called Ollama — the models run on our own computer, no paid API). The system has several specialized agents:

- **Data Agent** — finds, cleans, and validates data; knows how fresh or complete it is.
- **Model Agent** — trains and runs the prediction models; adds uncertainty ranges.
- **Explanation Agent** — explains WHY a result happened (SHAP, counterfactuals).
- **Report Agent** — writes the reports and memos using verified numbers.
- **PocketRipple chain (6 stages)** — first a **relevance gate (Stage 0)** screens every headline (economic/geopolitical topic cluster + source allowlist), then six stages run in order: 1 Trigger (PESTLE, scope, tempo) → 2 Actors & asymmetry → 3 Transmission channels → 4 Impact matrix → 5 Cascade + "Weird Test" → 6 Pocketbook impact (global view + household view with the five action badges). Each stage has its own JSON schema; the orchestrator caches the chain stage-by-stage, so a headline is never analyzed twice.
- **Historical Evidence Agent** — embeds each headline (384 dimensions) and retrieves the **top-3 most similar past crises** from pgvector; the similarity scores and real-world outcomes are injected into the chain as grounding.
- **Orchestrator (the boss)** — plans the work, sends tasks to the right agent, and **checks the results** to reject any made-up number.

Key safety design: the AI chatbot can never calculate. It only writes text. All numbers come from the validated models. Every stage runs through four validators — JSON schema check, the **Mechanism Rule** (a transmission channel must name a plausible mechanism), **data grounding** (any number must match the database), and the **Weird Test** (would an independent reader find this chain plausible?). Failures are rejected and retried.

---

## 9. The website pages (UI)

A multi-page platform (~28 screens), grouped into areas:

- **Accounts**: landing page, login/signup, organization setup, main workspace dashboard (customizable widgets), settings/roles/plans.
- **Data**: Data Explorer (browse and filter all datasets by country/region/indicator/year, make charts, export), Indicator Library (search 1,500+ indicators with definitions and data-quality scores), Data Freshness page (which datasets are up to date).
- **Monitor**: Global Risk Map (world map colored by risk, click a country to drill in), Country Watchlists, Alerts Center, Food & Energy Security dashboard, Climate Impact dashboard.
- **Analyze**: Country Profile, Country Intelligence Brief, Peer Benchmark, Development Space explorer, Forecast/Nowcast page, Debt Sustainability page, Policy Counterfactual Studio, Model Explainer (SHAP charts).
- **Real-time & personal**: **`/ripple`** — the Geopolitical Ripple Dashboard (headline feed with "Important for You" filter, live Gold/Crude/FX bar with AI commentary, and the 3-tab headline modal: Global impact / Your pocketbook / Historical evidence); **`/basket`** — the Household Basket Optimizer; **`/wealth-guard`** — the Wealth Guard + Indicator Explainer. These three pages ship first, inside **one shared layout wrapper** that the macro dashboards (Global Risk Map, Nowcasting, SHAP Explainer, Teaching Lab) later plug into **without touching the new components**.
- **AI**: Ask-the-Agent workspace, Report/Memo generator.
- **Teaching**: Simulation Lab (teacher picks or creates a country/profile, sets a crisis; students solve it in the sandbox; teacher sees results), Challenge bank (real historical crises as puzzles).
- **Utility**: Export Center (CSV/PDF/PNG), Documentation and knowledge base.

**Tools:** React + Next.js + TypeScript, shadcn/ui (clean professional look), Plotly + Mapbox (maps and charts), TanStack Table (data tables). Dark/light mode, saved views, export buttons on every page. Component and integration tests with Vitest + React Testing Library + MSW. The full system diagram lives in **[diagrams/architecture_full.mmd](diagrams/architecture_full.mmd)**.

---

## 10. How we build the models (method)

### 1. Crisis early warning (Module 1)
- **Labels (the answer key):** we use the Laeven–Valencia database of real past crises (1970–2017) — which countries had debt, currency, or banking crises, and when.
- **Models:** XGBoost and Random Forest (popular, strong machine-learning methods) compared against a simple logistic model as the baseline.
- **Testing:** we use *walk-forward validation* — we train on the past and test on the future, one step at a time, so results are honest.
- **Benchmark:** we compare our numbers with the IMF/World Bank and ADB official frameworks.
- **Explainability:** SHAP shows the top reasons a country is at risk (for example: "foreign reserves fell below 3 months of imports").

### 2. Nowcasting (Module 2)
- **Nowcasting = estimating the present** before official data is published.
- We use Dynamic Factor Models, LASSO/Elastic-Net, and Random Forest, plus extra clues like satellite nightlights and Google Trends.
- Poverty: we follow the World Bank's approach (using WDI + PovcalNet data).
- **Testing:** pseudo-real-time backtesting, compared to a simple "random walk" baseline; we use a statistical test (Diebold–Mariano) to check if our improvements are real.

### 3. Scenario engine (Module 9, Shock & Resilience Studio)
- **Step 1 — size the shock with real data:** FAO food balance sheets + satellite drought/yield data tell us how much production or imports a country would actually lose.
- **Step 2 — spread the effect:** a trade-linkage model estimates the impact on GDP, food inflation, and import dependence, including spillover to other countries.
- **Step 3 — anchor to history:** every scenario is compared to a real event (Ukraine grain 2022, Suez 2021, food crisis 2008). Outputs are **ranges with uncertainty**, clearly labeled as estimates, never as exact predictions.

### 4. The AI agent (Modules 6, 11, 12)
- The agent searches documents and past reports using pgvector (semantic search).
- It answers with structured tool-calling, and the orchestrator verifies everything.
- Every action the agent takes is logged (an audit trail), so users can check where every number came from.

### 5. Teaching & Simulation Lab (Module 13)
- **Economic correctness first:** the sandbox clearly distinguishes a *price change* (movement along a curve — which can cause a shortage or surplus) from a *demand shift* (income, subsidies, exports — moves the whole curve). Lowering a price below equilibrium creates a shortage and is scored as a mistake, so students learn real supply-and-demand logic.
- **Synthetic countries:** a teacher can create an "economy profile" — a simplified set of ~20–30 key parameters (GDP, population, food import share, reserves, price levels, supply and demand curves) — without needing all 1,500 indicators.
- **Goals and scoring:** assignments have a real objective (e.g., food security without budget blowout); the score is computed by the deterministic engine and doubles as feedback.
- **Feedback:** the explanation agent converts each student action into plain-language economic reasoning.
- **Challenge bank:** real historical crises (Ukraine grain 2022, 2008 food crisis, Sri Lanka debt crisis) are offered as ready-made puzzles, pre-validated by the Shock & Resilience Studio.

### 6. PocketRipple transmission engine (Module 14)
- **Relevance gate first (Stage 0):** only headlines inside the economic/geopolitical topic cluster and from an allowed source list enter the 6-agent cascade — this keeps a single laptop GPU queue draining in real time.
- **Six chained stages:** Trigger (PESTLE classification, scope, tempo) → Actors & asymmetry → Transmission channels (trade, finance, commodity, confidence) → Impact matrix → Cascade + "Weird Test" → Pocketbook output (global view + household view with the five action badges).
- **Historical evidence (RAG):** every headline is embedded (384-d sentence-transformers) and matched against 50–100 curated historical crises stored in pgvector; the top-3 most similar events — with similarity scores and real-world outcomes — are injected into the chain, so every analysis is anchored to real history (Ukraine grain 2022, Suez 2021, 2008 food crisis, COVID 2020, Sri Lanka 2022, …).
- **Deterministic validation:** JSON schema check, the Mechanism Rule (a channel must name a plausible mechanism), data grounding (numbers must match the database), and the Weird Test (would an independent reader find this chain plausible?). Failures are rejected and retried — **the LLM never computes** (Design Rule 1).
- **Ethics:** Stage 4 assesses *impact only* — no targeting, no attack planning (Design Rule 5 still applies).

### 7. Household basket & wealth allocation (Modules 15–16)
- **Pure, testable logic:** basket construction and salary allocation are plain deterministic functions fed by live prices, local inflation forecasts, and the household profile — no AI computes a single number (Design Rule 1 holds).
- **On-the-fly computation:** baskets and allocations are generated per request (only the household profile persists in `user_households`), so results always reflect the latest prices.
- **Item-level advice** reuses the same inflation signals as the macro models, phrased with the five action badges (PRE-EMPT, SUBSTITUTE, ADAPT, PROTECT, ADVOCATE).

---

## 11. Tools (tech stack)

**Backend (Django):**
- Python 3.11+, Django 5.x — the full backend framework (auth, roles, admin panel, ORM, management commands)
- Django Ninja — fast API layer (Pydantic-based, clean interface for the frontend)
- Celery + Redis — background tasks (ETL jobs, model training, scheduled alerts, report generation)
- **Celery Beat** — the recurring-task scheduler: news every 5–10 min, prices every 5 min, weather every 30 min, plus the embedding job after ingestion
- PostgreSQL 16 + pgvector — the database (Django ORM handles all tables)

**ETL (data pipeline):**
- **Polars** (primary) — fast, clean DataFrame library for all transformations; handles the full data warehouse easily on a single machine
- **pandas** — fallback for quick one-off scripts
- **psycopg2 / Django management commands** — loading data into PostgreSQL (`python manage.py fetch_wdi --year 2024`)
- **feedparser, yfinance, open-meteo** — the real-time ingestion sources (RSS news feeds, gold/crude/FX prices, city weather)
- PySpark — **optional stretch demo** only (e.g., processing satellite raster data at scale to demonstrate big-data skills); not the ETL backbone

**Machine learning:**
- XGBoost, LightGBM — the crisis and nowcasting models
- scikit-learn, statsmodels — baselines, statistical tests
- Mapie — conformal prediction (honest uncertainty ranges)
- SHAP — explainability

**AI agent:**
- Ollama — free local AI models (runs on our machine, no paid API)
- **Qwen 2.5 model chain — auto-detected at first run:** 14B primary if the laptop GPU has ≥12 GB VRAM, 7B primary if 8 GB (7B is always the safe fallback), and 32B only when docked to university GPU hardware
- sentence-transformers (`all-MiniLM-L6-v2`, 384 dimensions) — creates the AI's searchable memory (embeddings for pgvector), used by both the agent and the historical-evidence retrieval

**Visualization & data versioning:**
- Plotly — charts (notebooks + frontend)
- DVC — data versioning (keeping track of dataset versions)
- MLflow — experiment tracking (keeping track of model runs)

**Testing:**
- **pytest + pytest-django** — backend suites: parser, sanity validators, retrieval, basket, RSS ingestion, price logging, API contracts
- **Vitest + React Testing Library + MSW** — frontend component rendering and route integration tests

**Website frontend:**
- Node 20+, Next.js 14 (TypeScript), Tailwind + shadcn/ui, Plotly, Mapbox GL, TanStack Table
- openapi-typescript — generates the TypeScript types from the Django Ninja schemas, so backend and frontend can never drift apart

---

## 12. Ethics

- The scenario tools are **only for resilience and preparedness** — helping organizations prepare for disasters. There is no attack-planning functionality, language, or assets anywhere.
- The PocketRipple chain follows the same rule: its impact stage (Stage 4) assesses consequences for economies and households — never targeting, never tactical detail.
- All data is public with proper licenses. No proprietary data.
- Every result comes with uncertainty and documented limitations. We never pretend to predict precisely.
- Every AI-produced number has a transparent audit trail; every rejected output is logged too.
- Household guidance (basket, allocation) is financial *preparation* advice framed as ranges and options — never a promise of returns.

---

## 13. Plan over 12 months (roadmap)

| Phase | Months | What we do |
|---|---|---|
| **P1** | 1–2 | **The three real-time extensions (built first):** platform foundation (Django + Next.js scaffold, Postgres + pgvector schema, Celery Beat schedules) → PocketRipple engine + relevance gate → RAG historical-crisis corpus → ATLAS Micro (basket + wealth guard) → the `/ripple`, `/basket`, `/wealth-guard` pages with component and integration tests |
| **P2** | 3–4 | Build the data warehouse: download all data sources, clean them, set up the database schema and data-quality checks |
| **P3** | 5–7 | Build the **core models**: Crisis Early Warning + Nowcasting; compare to IMF/ADB/World Bank baselines → first publishable result |
| **P4** | 8–9 | Food & Energy Security, Climate Impact, Debt Sustainability stress tests, SHAP explanation studio |
| **P5** | 10–11 | Build the **AI agent system** (reports, chat, memos) + the macro website pages (risk map, nowcasting, SHAP, Teaching Lab) + organization accounts, watchlists, alerts |
| **P6** | 12 | Shock & Resilience Studio, Teaching & Simulation Lab, final dashboards, PDF memos, 4 demo scenarios (Ministry / NGO / Investor / Classroom), thesis write-up, defense |

**Core (must ship):** Modules 1, 2, 3, 4, 5, 6, 9, 11, 13, 14, 15, 16.
**Stretch (if time remains):** Modules 7, 8, 10, 12.

> **Note (Oct 2026 revision):** the roadmap was re-sequenced so the three real-time extensions ship first (Phase P1). The core crisis and nowcasting models are **not dropped** — their hard freeze gate simply moves from Month 5 to **Month 7**.

---

## 14. Risks and how we handle them

| Risk | What could go wrong | How we prevent it |
|---|---|---|
| The free AI model makes up numbers | Untrustworthy AI answers | All numbers come from validated code; the orchestrator checks and rejects made-up numbers; everything is logged |
| Scenario tool gives fake-precise results | Committee doesn't trust it | We always give ranges with uncertainty; compare to real history; label results as estimates |
| Missing data in poor countries | Weak predictions | Documented imputation rules; data-quality scores shown in the UI; honest benchmarks |
| Too much work for one person | Missed deadline | Core modules are frozen as hard gates (end of Month 4, end of Month 7); stretch work only after cores are done |
| API rate limits (Google Trends, FRED) | Missing data | Download once and cache to disk; offline fallbacks |
| Website gets too big to finish | UI chaos | Real-time pages frozen at Month 2; macro page structure frozen at Month 10; only complete pages for core modules |
| Search speed gets slow | Slow AI answers | Keep the searchable memory small and well-indexed |
| Laptop GPU too small for the free AI model | Slow or failing headline analysis | Auto-detected Qwen chain (14B if ≥12 GB VRAM, else 7B primary; 32B only on university hardware); the Stage 0 relevance gate limits how many headlines enter the chain; stage-level caching means a headline is never analyzed twice |
| Live price / news feed instability | Missing prices or headlines | Failures are logged and skipped (the scheduler never crashes); the UI serves the last good value |
| Headline backlog on a single GPU | Feed falls behind real time | Relevance gate before the expensive chain; the agent worker runs with concurrency 1 (matching the local LLM) |

### Milestone gates (hard rules — the project stays on track)
- **End of Month 2:** the three real-time extensions working end-to-end — pipeline, RAG retrieval, basket, wealth guard, three routes, all 9 test suites green.
- **End of Month 4:** data warehouse live (core sources), database schema + quality layer done.
- **End of Month 7:** Crisis Early Warning + Nowcasting finished, with benchmark tables. No more model changes.
- **End of Month 9:** Security / Debt / Climate / Explanation modules finished.
- **End of Month 11:** website + AI agent finished; only bug fixes and the Shock studio remain.
- **End of Month 12:** Shock & Resilience Studio, demos, thesis, defense.

---

## 15a. User Actions & Features Catalog (appendix)

ATLAS is a dense, action-rich product, not a single dashboard. Users can perform **~80 concrete actions across 9 areas**: data querying and charting (16+ actions), monitoring and alerts (11), modeling and prediction (9), analysis and explanation (9), scenarios and simulation (9), the Teaching Lab (10), the AI agent chat (9), reporting and export (5), and account/collaboration (5).

The full catalog — every action listed with a short description — is documented separately in **[FEATURES.md](FEATURES.md)**. It is used to guide the UI build (each action = a button, filter, menu, or slider) and to demonstrate product depth to reviewers.

> The actions for Modules 14–16 (filtering the ripple feed, opening a headline breakdown, regenerating a basket, tuning an allocation, looking up an indicator) are appended to FEATURES.md in the same update as the UI build.

---

## 16. The real-time & personal layer (the three extensions, built first)

This is the newest part of ATLAS — the layer the project starts with (Phase P1). It adds three routes and one background pipeline to the platform, while **every existing ATLAS macro dashboard stays untouched**.

### The three pages

**1. `/ripple` — Live Geopolitical Ripple Dashboard**
- **Feed layout:** a 24/7 scrolling news feed, plus an **"Important for You"** filtered section based on the user's location.
- **Live commodity bar:** widgets for **Gold, Crude Oil, and Exchange Rates** with AI commentary linking current trends to the active headlines.
- **Interactive headline modal** (click a headline → three tabs):
  - **Tab 1 — Global Geopolitical Impact:** Trigger, Ecosystem, Asymmetry Check, Transmission Channels, Impact Matrix, Cascading Chain.
  - **Tab 2 — Your Pocketbook:** location-specific exposure vectors (Transport, Kitchen, Utilities, Tech) + an action plan with the badges **PRE-EMPT · SUBSTITUTE · ADAPT · PROTECT · ADVOCATE**.
  - **Tab 3 — Historical Evidence:** the top-3 retrieved historical crises with similarity scores and real-world outcomes.

**2. `/basket` — Smart Monthly Household Basket Optimizer**
- **User input card:** salary, rent, family size, dietary constraints, city.
- **Dynamic monthly basket table:** itemized list split across Kitchen, Transport, and Utilities.
- **Smart recommendations engine:** item-level advice based on local inflation forecasts (e.g., *"Rice: PRE-EMPT — buy a 2-month buffer before the expected 8% tariff hike"*).

**3. `/wealth-guard` — Personal Wealth Guard & Indicator Explainer**
- **Salary allocation card:** recommended split between a local-currency liquid buffer, gold purchases, and essential bulk buying.
- **"What Does This Indicator Mean?" drawer:** a searchable list of technical macro metrics (FAO Food Price Index, Import Cover Ratio, Nightlight Activity), each with plain-language *What it means* and *What could happen to my wallet*.

### Storage (the six tables)
| Table | Holds |
|---|---|
| `news_headlines` | headline text, source, location, published time, HNSW-indexed embedding |
| `commodity_live_prices` | gold, crude oil (Brent `BZ=F`), FX pairs with timestamp + index for fast reads |
| `weather_observations` | per-city observations on a 30-min cadence, 7-day retention |
| `historical_crises` | 50–100 curated past crises with embeddings for top-3 similarity retrieval |
| `analyses_cache` | one row per headline: 6 JSONB stage results, `status`, `model_used`, `pipeline_version`, `historical_matches` |
| `user_households` | saved profile (salary, rent, family size, diet, city); baskets & allocations are computed on the fly, not stored |

### Schedule (Celery Beat)
| Job | Cadence |
|---|---|
| RSS headline ingest | every 5–10 min (deduplicated) |
| Commodity & FX price ingest | every 5 min |
| City weather ingest | every 30 min |
| Embedding job | after each ingestion batch |

### Safety & integrity
- **Stage 0 relevance gate** before the 6-stage chain — only economic/geopolitical headlines from allowed sources are analyzed.
- **Concurrency 1** for the agent worker (one local LLM generation at a time), with stage-level caching.
- **Four validators** per stage: JSON schema, Mechanism Rule, data grounding, Weird Test — rejects and retries are logged.
- The LLM never computes a number (Design Rule 1); Stage 4 assesses impact only, never targeting (Design Rule 5).
- **UI build rules:** one shared layout wrapper created once; new components are modular with explicit prop interfaces; component rendering + route integration tests (Vitest + RTL + MSW); the macro dashboards slot in later without modifying these components.

---

## 17. Final deliverables

1. A versioned data warehouse (all public data, tracked with DVC).
2. A reproducible model pipeline with benchmark tables compared to institutional baselines.
3. Explanation artifacts (SHAP charts, counterfactuals) for every model.
4. The AI agent system (free local models) with a full audit trail.
5. The multi-page website for organizations (core modules fully working).
6. The Shock & Resilience Studio, calibrated against real history.
7. The real-time & personal layer: PocketRipple dashboard (`/ripple`), household basket optimizer (`/basket`), and wealth guard (`/wealth-guard`) — engine, background ingestion, API, UI, and their 9 test suites.
8. A thesis with one chapter per module, and a defense demo with 4 real scenarios (Ministry, NGO, Investor, Classroom).
