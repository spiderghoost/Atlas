import re
from typing import Tuple

ECONOMIC_KEYWORDS = [
    r'\bgdp\b', r'\binflation\b', r'\binterest rate', r'\bcentral bank\b', r'\bdebt\b',
    r'\bcurrency\b', r'\bdevaluation\b', r'\bexchange rate\b', r'\bfx\b', r'\btariff',
    r'\bsanction', r'\btrade war\b', r'\bexport\b', r'\bimport\b', r'\bgrain\b',
    r'\bwheat\b', r'\boil\b', r'\bcrude\b', r'\bgas\b', r'\benergy\b', r'\bfood\b',
    r'\bfamine\b', r'\bdrought\b', r'\bblockade\b', r'\bport\b', r'\bshipping\b',
    r'\bcanal\b', r'\bdefault\b', r'\bimf\b', r'\bworld bank\b', r'\bbanking crisis\b',
    r'\bbailout\b', r'\bfiscal\b', r'\breserves\b', r'\bcommodity\b', r'\bsupply chain\b'
]

GEOPOLITICAL_KEYWORDS = [
    r'\bwar\b', r'\bconflict\b', r'\bmissile\b', r'\bstrike\b', r'\bmilitary\b',
    r'\btreaty\b', r'\belection\b', r'\bcoup\b', r'\bprotest\b', r'\bunrest\b',
    r'\bsummit\b', r'\bdiplomat', r'\bgeopolitic'
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in ECONOMIC_KEYWORDS + GEOPOLITICAL_KEYWORDS]


def evaluate_relevance(title: str, summary: str = "") -> Tuple[bool, str]:
    """
    Stage 0 Relevance Gate: Filters headlines to determine if they contain actionable
    macroeconomic or geopolitical shock signals.
    
    Returns:
        (is_relevant, topic_cluster)
    """
    text = f"{title} {summary}"
    
    matches = []
    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            matches.append(pattern.pattern.replace(r'\b', '').replace('\\', ''))
            
    if not matches:
        return False, "Unrelated"
        
    # Classify into primary cluster
    text_lower = text.lower()
    if any(k in text_lower for k in ['grain', 'wheat', 'food', 'drought', 'fertilizer', 'famine']):
        cluster = "Food Security & Agriculture"
    elif any(k in text_lower for k in ['oil', 'crude', 'gas', 'brent', 'opec', 'energy', 'pipeline']):
        cluster = "Energy & Commodities"
    elif any(k in text_lower for k in ['tariff', 'trade', 'export', 'import', 'port', 'canal', 'shipping', 'supply chain']):
        cluster = "Trade & Supply Chains"
    elif any(k in text_lower for k in ['inflation', 'debt', 'imf', 'currency', 'interest rate', 'default', 'reserves', 'bank']):
        cluster = "Macroeconomic & Financial"
    else:
        cluster = "Geopolitical & Conflict"
        
    return True, cluster
