from typing import List, Dict, Any

HISTORICAL_CRISES_DATA: List[Dict[str, Any]] = [
    {
        "crisis_id": "ukraine-grain-2022",
        "name": "Black Sea Grain & Fertilizer Corridor Disruption",
        "year": 2022,
        "region": "Eastern Europe / Global",
        "crisis_types": ["food_security", "supply_chain", "geopolitical"],
        "summary": "Blockade of Ukrainian Black Sea ports halting 20M tonnes of wheat and corn exports.",
        "what_happened": "In February 2022, military conflict halted shipping from Chornomorsk, Odesa, and Pivdennyi ports. Global benchmark wheat futures spiked over 50% in two weeks. Fertilizer input costs doubled, triggering acute food inflation in import-dependent countries across North Africa and the Middle East.",
        "transmission_channels": [
            "Maritime export blockade (Black Sea route)",
            "Fertilizer supply shock (potash and ammonia sanctions)",
            "Global commodity market margin calls and hoarding"
        ],
        "real_world_outcomes": {
            "wheat_futures_spike_pct": 53.0,
            "fao_food_index_peak": 159.7,
            "impacted_regions": ["Middle East", "North Africa", "Horn of Africa"]
        }
    },
    {
        "crisis_id": "suez-blockage-2021",
        "name": "Ever Given Suez Canal Blockage",
        "year": 2021,
        "region": "Middle East / Global Maritime",
        "crisis_types": ["supply_chain", "trade_route", "freight"],
        "summary": "Container ship Ever Given ran aground in the Suez Canal, stranding $9.6B daily in transit.",
        "what_happened": "For six days in March 2021, the single-lane southern section of the Suez Canal was obstructed. Over 360 vessels queued, diverting maritime traffic around the Cape of Good Hope (+14 days sailing time). Spot container freight rates doubled, and European manufacturing faced intermediate input delays.",
        "transmission_channels": [
            "Bottleneck transit failure (12% of global trade volume)",
            "Container repositioning disruption",
            "Bunker fuel consumption and shipping surcharge spikes"
        ],
        "real_world_outcomes": {
            "daily_trade_delay_usd_billions": 9.6,
            "spot_freight_rate_increase_pct": 100.0,
            "transit_delay_days": 14
        }
    },
    {
        "crisis_id": "global-food-crisis-2008",
        "name": "Global Food & Commodity Price Crisis 2007–2008",
        "year": 2008,
        "region": "Global",
        "crisis_types": ["food_security", "inflation", "export_restrictions"],
        "summary": "Record surge in primary agricultural commodities driven by biofuel demand, energy prices, and export bans.",
        "what_happened": "Severe drought in major grain exporters coincided with record crude oil prices ($140/bbl) and export restrictions imposed by over 30 countries (e.g. India and Vietnam rice export bans). Riots erupted across 30+ developing countries as household food budgets exceeded 70% of income.",
        "transmission_channels": [
            "Export tariff and ban contagion",
            "Crude oil input cost passthrough into agrochemicals and diesel",
            "Biofuel feedstock substitution"
        ],
        "real_world_outcomes": {
            "rice_price_surge_pct": 217.0,
            "wheat_price_surge_pct": 136.0,
            "food_riots_countries_count": 30
        }
    },
    {
        "crisis_id": "sri-lanka-default-2022",
        "name": "Sri Lanka Sovereign Debt & Balance of Payments Collapse",
        "year": 2022,
        "region": "South Asia",
        "crisis_types": ["debt_crisis", "currency_devaluation", "balance_of_payments"],
        "summary": "Exhaustion of foreign reserves, overnight currency peg collapse, and sovereign debt default.",
        "what_happened": "Depleted foreign exchange reserves left the government unable to service external debt or finance critical imports (fuel, medicine, cooking gas). The central bank abandoned the USD peg, resulting in an 80% currency depreciation, 70% headline inflation, and power blackouts, culminating in a sovereign default on $51B in external obligations.",
        "transmission_channels": [
            "Foreign exchange reserve depletion",
            "Import compression leading to production halt",
            "Sovereign default rating downgrade locking out capital markets"
        ],
        "real_world_outcomes": {
            "currency_depreciation_pct": 80.0,
            "headline_inflation_peak_pct": 69.8,
            "external_debt_defaulted_usd_billions": 51.0
        }
    },
    {
        "crisis_id": "covid-supply-shock-2020",
        "name": "COVID-19 Global Supply Chain Dislocation & Lockdowns",
        "year": 2020,
        "region": "Global",
        "crisis_types": ["supply_chain", "demand_shock", "transportation"],
        "summary": "Synchronous factory shutdowns and maritime port congestion causing global semiconductor and goods shortages.",
        "what_happened": "Early 2020 lockdowns shuttered factories across Asia and Europe. Sudden shift in consumer demand towards manufactured tech goods collided with port labor shortages, sending container shipping rates from $1,500 to over $10,000 per 40ft container and creating 18-month lead times on industrial chips.",
        "transmission_channels": [
            "Labor restrictions and plant quarantines",
            "Bullwhip inventory effect across tiers",
            "Container equipment imbalances across trade routes"
        ],
        "real_world_outcomes": {
            "container_rate_increase_x": 7.0,
            "gdp_contraction_global_pct": 3.1,
            "semiconductor_shortage_duration_months": 18
        }
    },
    {
        "crisis_id": "asian-financial-crisis-1997",
        "name": "Asian Financial & Currency Contagion",
        "year": 1997,
        "region": "Southeast Asia / East Asia",
        "crisis_types": ["currency_crisis", "banking_crisis", "capital_flight"],
        "summary": "Collapse of the Thai Baht peg triggering regional currency runs, banking insolvencies, and IMF packages.",
        "what_happened": "Speculative pressure on the Thai baht forced the Bank of Thailand to float the currency in July 1997. Heavy unhedged foreign debt in the private sector triggered domino currency devaluations in Indonesia, South Korea, and Malaysia, accompanied by acute capital flight and corporate bankruptcies.",
        "transmission_channels": [
            "Fixed exchange rate peg failure",
            "Unhedged foreign currency debt exposure",
            "Investor panic contagion across emerging market peers"
        ],
        "real_world_outcomes": {
            "thai_baht_depreciation_pct": 52.0,
            "indonesian_rupiah_depreciation_pct": 83.0,
            "regional_gdp_contraction_pct": 8.5
        }
    },
    {
        "crisis_id": "opec-oil-embargo-1973",
        "name": "1973 First OPEC Oil Embargo & Stagflation",
        "year": 1973,
        "region": "Middle East / OECD",
        "crisis_types": ["energy_shock", "stagflation", "geopolitical"],
        "summary": "OAPEC oil production cut and export embargo quadrupling global crude oil prices.",
        "what_happened": "In October 1973, Arab members of OPEC proclaimed an oil embargo against nations supporting Israel during the Fourth Arab-Israeli War. World oil prices quadrupled from $3 to nearly $12 per barrel, sparking unprecedented double-digit inflation and economic stagnation across developed economies.",
        "transmission_channels": [
            "Energy export embargo and production caps",
            "Energy input passthrough across industrial supply chains",
            "Cost-push inflation prompting monetary tightening"
        ],
        "real_world_outcomes": {
            "crude_oil_price_surge_pct": 300.0,
            "oecd_inflation_peak_pct": 13.5,
            "stock_market_drop_pct": 45.0
        }
    }
]
