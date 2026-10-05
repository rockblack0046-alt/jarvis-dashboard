from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import ccxt
import httpx
import os
import time
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Jarvis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

exchange = ccxt.binance()
TWELVE_KEY = os.getenv("TWELVEDATA_API_KEY")
TWELVE_URL = "https://api.twelvedata.com"

# ============ CRYPTO ============
SYMBOLS = {
    "BTC": "BTC/USDT",
    "ETH": "ETH/USDT",
    "SOL": "SOL/USDT",
    "BNB": "BNB/USDT",
}

@app.get("/")
def home():
    return {"status": "Jarvis chal raha hai 🚀"}

@app.get("/api/crypto")
def get_crypto():
    result = []
    for name, symbol in SYMBOLS.items():
        try:
            t = exchange.fetch_ticker(symbol)
            result.append({
                "name": name,
                "symbol": symbol,
                "price": t["last"],
                "change_24h": t["percentage"],
                "high": t["high"],
                "low": t["low"],
                "volume": t["quoteVolume"],
            })
        except Exception as e:
            result.append({"name": name, "error": str(e)})
    return {"data": result}

@app.get("/api/crypto/{coin}")
def get_one_crypto(coin: str):
    symbol = f"{coin.upper()}/USDT"
    t = exchange.fetch_ticker(symbol)
    return {
        "symbol": symbol,
        "price": t["last"],
        "change_24h": t["percentage"],
        "high": t["high"],
        "low": t["low"],
    }

# ============ FOREX + GOLD (with cache) ============
FOREX_SYMBOLS = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"]
GOLD_SYMBOLS = ["XAU/USD"]

_forex_cache = {"data": None, "time": 0}
CACHE_TTL = 60  # 60 seconds

async def fetch_forex_from_api():
    symbols = ",".join(FOREX_SYMBOLS + GOLD_SYMBOLS)
    url = f"{TWELVE_URL}/quote"
    params = {"symbol": symbols, "apikey": TWELVE_KEY}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params, timeout=15)
        data = r.json()

    result = []
    for sym in FOREX_SYMBOLS + GOLD_SYMBOLS:
        item = data.get(sym, {})
        if "code" in item and item["code"] != 200:
            continue
        result.append({
            "symbol": sym,
            "price": float(item.get("close", 0)) if item.get("close") else None,
            "change": float(item.get("change", 0)) if item.get("change") else None,
            "change_pct": float(item.get("percent_change", 0)) if item.get("percent_change") else None,
            "high": float(item.get("high", 0)) if item.get("high") else None,
            "low": float(item.get("low", 0)) if item.get("low") else None,
            "is_gold": sym in GOLD_SYMBOLS,
        })
    return result

@app.get("/api/forex")
async def get_forex():
    if not TWELVE_KEY:
        return {"error": "TWELVEDATA_API_KEY .env mein set nahi hai"}

    now = time.time()
    if _forex_cache["data"] is not None and (now - _forex_cache["time"]) < CACHE_TTL:
        return {"data": _forex_cache["data"], "cached": True}

    try:
        data = await fetch_forex_from_api()
        _forex_cache["data"] = data
        _forex_cache["time"] = now
        return {"data": data, "cached": False}
    except Exception as e:
        if _forex_cache["data"] is not None:
            return {"data": _forex_cache["data"], "cached": True, "note": "stale"}
        return {"error": str(e)}

@app.get("/api/gold")
async def get_gold():
    if not TWELVE_KEY:
        return {"error": "TWELVEDATA_API_KEY .env mein set nahi hai"}
    url = f"{TWELVE_URL}/quote"
    params = {"symbol": "XAU/USD", "apikey": TWELVE_KEY}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params, timeout=15)
        return r.json()

# ============ SAB EK SAATH ============
@app.get("/api/all")
async def get_all():
    crypto = get_crypto()
    forex = await get_forex()
    return {
        "crypto": crypto["data"],
        "forex_gold": forex.get("data", []),
    }

# ============ DASHBOARD SERVE ============
@app.get("/dashboard")
def serve_dashboard():
    return FileResponse("dashboard.html")