from datetime import datetime, timezone
from typing import Dict, Any, List
import yfinance as yf
from apps.realtime.models import CommodityLivePrice

TICKERS = [
    {"symbol": "GC=F", "name": "Gold Spot", "currency": "USD"},
    {"symbol": "BZ=F", "name": "Brent Crude Oil", "currency": "USD"},
    {"symbol": "CL=F", "name": "WTI Crude Oil", "currency": "USD"},
    {"symbol": "EURUSD=X", "name": "EUR / USD", "currency": "USD"},
    {"symbol": "EGP=X", "name": "USD / EGP", "currency": "EGP"},
    {"symbol": "TRY=X", "name": "USD / TRY", "currency": "TRY"},
]


def ingest_commodity_prices() -> Dict[str, Any]:
    """
    Fetches real-time market prices for benchmark commodities and key currency pairs.
    Saves snapshot observations in CommodityLivePrice.
    """
    stats = {"success": 0, "failed": 0, "tickers": []}

    for item in TICKERS:
        sym = item["symbol"]
        try:
            ticker = yf.Ticker(sym)
            fast_info = getattr(ticker, 'fast_info', None)
            
            price = None
            prev_close = None
            if fast_info and hasattr(fast_info, 'last_price') and fast_info.last_price is not None:
                price = float(fast_info.last_price)
                prev_close = getattr(fast_info, 'previous_close', None)
            else:
                hist = ticker.history(period="2d")
                if not hist.empty:
                    price = float(hist['Close'].iloc[-1])
                    if len(hist) > 1:
                        prev_close = float(hist['Close'].iloc[-2])

            if price is not None:
                change_pct = None
                if prev_close and prev_close > 0:
                    change_pct = round(((price - prev_close) / prev_close) * 100, 2)

                CommodityLivePrice.objects.create(
                    symbol=sym,
                    name=item["name"],
                    price=round(price, 4),
                    currency=item["currency"],
                    change_24h_pct=change_pct,
                    timestamp=datetime.now(timezone.utc)
                )
                stats["success"] += 1
                stats["tickers"].append({"symbol": sym, "price": price, "change_pct": change_pct})
            else:
                stats["failed"] += 1
        except Exception as e:
            stats["failed"] += 1
            stats[f"err_{sym}"] = str(e)

    return stats
