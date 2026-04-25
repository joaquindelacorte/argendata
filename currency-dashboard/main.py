import time
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(title="Currency Dashboard")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CACHE_TTL = 300  # 5 minutes

PAIRS = [
    ("EURUSD=X",  "EUR/USD",  "eu", "eu"),
    ("GBPUSD=X",  "GBP/USD",  "gb", "gb"),
    ("AUDUSD=X",  "AUD/USD",  "au", "au"),
    ("NZDUSD=X",  "NZD/USD",  "nz", "nz"),
    ("USDJPY=X",  "USD/JPY",  "jp", "jp"),
    ("USDCNY=X",  "USD/CNY",  "cn", "cn"),
    ("USDCHF=X",  "USD/CHF",  "ch", "ch"),
    ("USDCAD=X",  "USD/CAD",  "ca", "ca"),
    ("USDMXN=X",  "USD/MXN",  "mx", "mx"),
    ("USDINR=X",  "USD/INR",  "in", "in"),
    ("USDBRL=X",  "USD/BRL",  "br", "br"),
    ("USDRUB=X",  "USD/RUB",  "ru", "ru"),
    ("DX-Y.NYB",  "DXY",      "us", "us"),
    ("USDTRY=X",  "USD/TRY",  "tr", "tr"),
    ("USDSEK=X",  "USD/SEK",  "se", "se"),
    ("USDPLN=X",  "USD/PLN",  "pl", "pl"),
    ("USDNOK=X",  "USD/NOK",  "no", "no"),
    ("USDZAR=X",  "USD/ZAR",  "za", "za"),
    ("USDSGD=X",  "USD/SGD",  "sg", "sg"),
    ("USDCZK=X",  "USD/CZK",  "cz", "cz"),
    ("USDHUF=X",  "USD/HUF",  "hu", "hu"),
    ("USDKRW=X",  "USD/KRW",  "kr", "kr"),
    ("USDARS=X",  "USD/ARS (Oficial)", "ar", "ar"),
]

DOLAR_ENDPOINTS = {
    "USD/ARS (Blue)": "https://dolarapi.com/v1/dolares/blue",
    "USD/ARS (MEP)":  "https://dolarapi.com/v1/dolares/bolsa",
    "USD/ARS (CCL)":  "https://dolarapi.com/v1/dolares/contadoconliqui",
}

# ---------------------------------------------------------------------------
# In-memory cache
# ---------------------------------------------------------------------------

_cache: dict = {}


def _cache_get(key: str):
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        return entry["data"]
    return None


def _cache_set(key: str, data):
    _cache[key] = {"ts": time.time(), "data": data}


# ---------------------------------------------------------------------------
# yfinance helpers
# ---------------------------------------------------------------------------

def _safe_float(val) -> Optional[float]:
    try:
        f = float(val)
        return f if f != 0 else None
    except Exception:
        return None


def _pct(current: float, past: float) -> Optional[float]:
    if past and past != 0:
        return round((current - past) / past * 100, 2)
    return None


def _fetch_pair(ticker: str, label: str, flag: str) -> dict:
    """Fetch one yfinance ticker and compute change percentages."""
    result = {
        "ticker": ticker,
        "label": label,
        "flag": flag,
        "price": None,
        "day_change": None,
        "day_pct": None,
        "week_pct": None,
        "month_pct": None,
        "ytd_pct": None,
        "updated": datetime.now(timezone.utc).isoformat(),
        "is_ars": flag == "ar",
    }

    try:
        tk = yf.Ticker(ticker)

        # Fast path: use info for current price + prev close
        info = tk.fast_info
        price = _safe_float(getattr(info, "last_price", None))
        prev_close = _safe_float(getattr(info, "previous_close", None))

        if price is None:
            return result

        result["price"] = round(price, 6)

        if prev_close:
            result["day_change"] = round(price - prev_close, 6)
            result["day_pct"] = _pct(price, prev_close)

        # Historical percentages via 1-year daily history
        hist = tk.history(period="1y", interval="1d", auto_adjust=True)
        if hist.empty:
            return result

        closes = hist["Close"].dropna()
        if len(closes) < 2:
            return result

        def _hist_price(n_days_ago: int) -> Optional[float]:
            # Walk back through available dates to find the closest past close
            for i in range(n_days_ago, n_days_ago + 5):
                if len(closes) > i:
                    return _safe_float(closes.iloc[-(i + 1)])
            return None

        p7   = _hist_price(7)
        p30  = _hist_price(30)

        # YTD: first trading day of current year
        current_year = datetime.now().year
        ytd_closes = closes[closes.index.year == current_year]
        p_ytd = _safe_float(ytd_closes.iloc[0]) if not ytd_closes.empty else None

        result["week_pct"]  = _pct(price, p7)
        result["month_pct"] = _pct(price, p30)
        result["ytd_pct"]   = _pct(price, p_ytd)

    except Exception as exc:
        log.warning("yfinance error for %s: %s", ticker, exc)

    return result


async def _fetch_dolar_api() -> list[dict]:
    """Fetch ARS blue/MEP/CCL from dolarapi.com."""
    results = []
    async with httpx.AsyncClient(timeout=10) as client:
        for label, url in DOLAR_ENDPOINTS.items():
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                venta = _safe_float(data.get("venta"))
                compra = _safe_float(data.get("compra"))
                if venta:
                    results.append({
                        "ticker": label,
                        "label": label,
                        "flag": "ar",
                        "price": venta,
                        "compra": compra,
                        "day_change": None,
                        "day_pct": None,
                        "week_pct": None,
                        "month_pct": None,
                        "ytd_pct": None,
                        "updated": datetime.now(timezone.utc).isoformat(),
                        "is_ars": True,
                    })
            except Exception as exc:
                log.warning("dolarapi error for %s: %s", label, exc)

    return results


# ---------------------------------------------------------------------------
# Data assembly
# ---------------------------------------------------------------------------

async def _build_rates() -> list[dict]:
    cached = _cache_get("all_rates")
    if cached:
        return cached

    loop = asyncio.get_event_loop()

    # Fetch yfinance pairs concurrently in a thread pool
    tasks = [
        loop.run_in_executor(None, _fetch_pair, ticker, label, flag)
        for ticker, label, flag, _ in PAIRS
    ]
    yf_results = await asyncio.gather(*tasks)
    rates = [r for r in yf_results if r["price"] is not None]

    # Fetch ARS extras
    ars_extra = await _fetch_dolar_api()
    rates.extend(ars_extra)

    _cache_set("all_rates", rates)
    return rates


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.get("/api/rates")
async def get_rates():
    rates = await _build_rates()
    return {
        "data": rates,
        "cached_until": datetime.fromtimestamp(
            _cache.get("all_rates", {}).get("ts", 0) + CACHE_TTL,
            tz=timezone.utc,
        ).isoformat(),
        "count": len(rates),
    }


@app.get("/api/rates/{pair}")
async def get_rate(pair: str):
    rates = await _build_rates()
    pair_lower = pair.lower()
    match = next(
        (r for r in rates if r["label"].lower().replace("/", "") == pair_lower
         or r["ticker"].lower().replace("=x", "") == pair_lower),
        None,
    )
    if not match:
        raise HTTPException(status_code=404, detail=f"Pair '{pair}' not found")
    return match


# ---------------------------------------------------------------------------
# Run instructions
# ---------------------------------------------------------------------------
# pip install -r requirements.txt
# uvicorn main:app --reload --port 8000
# Then open http://localhost:8000
