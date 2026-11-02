# ATLAS — User Actions & Features Catalog

This is the full list of concrete actions a user can take on the platform (~80 actions across 9 areas). Every module/page/button is one "option" — this is what makes ATLAS feel like a dense, professional product rather than a single dashboard.

## 1. Data & Charts
- Browse/query any indicator for any country/region/year
- Filter by income group, region, indicator category
- Switch chart type: line, bar, scatter, heatmap, radar, bubble, area, choropleth map
- Compare up to 5 countries side-by-side on one chart
- Transform data: per capita, % of GDP, log scale, growth rate, index (base year)
- Build custom formulas between indicators ("create indicator X = A / B × 100")
- Animate a chart over years (time playback)
- Overlay trend lines / moving averages
- Zoom and brush time ranges
- Correlation matrix between selected indicators
- Scatter plot with bubble size = population or GDP
- Drill-down: world → region → country → sub-national (pilot)
- Download chart as PNG / SVG / PDF
- Download data as CSV / Excel
- Save the view / load saved views
- Add personal annotations to charts

## 2. Monitoring & Alerts
- Create a country watchlist
- Add/remove countries from a watchlist
- Set alert thresholds ("alert me when food inflation > 10%")
- Choose alert channel (in-app / email)
- Choose frequency (real-time / daily / weekly digest)
- Snooze or pause alerts
- View alert history
- See a country's risk timeline
- Rank countries by risk score
- Compare risk across countries on the map
- One-click "explain this alert" (SHAP why)

## 3. Modeling & Prediction
- Choose a country and a target (GDP, inflation, poverty, crisis risk)
- Choose model type (XGBoost / Random Forest / LASSO / baseline)
- Choose forecast horizon (1 / 3 / 5 years)
- See predictions with uncertainty bands
- View backtest results (was the model right before?)
- View feature importance (what drives the prediction)
- View the walk-forward validation chart
- Change the training window
- Export model outputs to a report

## 4. Analysis & Explanation
- Generate a full country intelligence brief (one click)
- Get SHAP explanation: "why is this country at risk?" (force plot + plain language)
- Counterfactual: "what must change for risk to drop to low?"
- Auto-find peers: "which countries are most similar?"
- Compare selected peers on a scorecard
- Position a country in the development space; play its trajectory over years
- Run a debt sustainability check (official-style thresholds)
- Run a debt stress test (what if interest rates rise 3%?)
- View a country's data-quality report (what's missing/stale)

## 5. Scenarios & Simulation (Shock studio)
- Pick a shock type: drought, port closure, supply disruption, commodity spike, capital flight
- Set the magnitude with a slider
- Apply to one country or many
- See impact on multiple outcomes at once (GDP, inflation, food prices, poverty)
- Compare 2–3 scenarios side-by-side
- Compare a scenario to its historical analog (Ukraine 2022, Suez 2021…)
- Reset to baseline
- Save a scenario and reopen it later
- Export a scenario summary to a memo

## 6. Teaching Lab
- Teacher: pick a real country or create a synthetic economy profile
- Teacher: set the assignment goal and difficulty
- Teacher: assign a challenge from the bank (Ukraine grain, 2008 food crisis, Sri Lanka debt)
- Student: adjust price bars / demand shifts / subsidies / taxes / reserves
- Student: run a step and see the result
- Student: get plain-language feedback on each action
- Student: see the objective score
- Student: restart the challenge
- Teacher: view the whole class's results and scores
- Teacher: compare students' solution paths

## 7. AI Agent (chat)
- Ask questions in natural language ("why is Ghana at risk?")
- Ask follow-up questions
- Ask for a chart with explanation
- Ask for a comparison ("compare Egypt and Kenya")
- Request a country brief
- Ask for a decision memo (Ministry / NGO / Investor template)
- Ask "why" on any number → gets source citation
- Toggle language
- Save/export the conversation

## 8. Reporting & Export
- Build a custom dashboard from widgets (map, chart, table, KPI cards, alert feed)
- Drag-and-drop widget editor
- Generate a PDF memo with your organization's template
- Export data, charts, and reports (CSV / Excel / PDF / PNG / SVG)
- Print-ready formatting

## 9. Account & Collaboration
- Roles: admin / analyst / minister / teacher / student
- Invite team members to an organization
- Share a dashboard or saved view with a link
- Notification preferences
- Activity/audit log (see what the AI agents did)
