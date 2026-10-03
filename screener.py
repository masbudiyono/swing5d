import json
from datetime import datetime
import pandas as pd
import yfinance as yf

# Daftar ticker liquid IHSG utama
WATCHLIST = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "TLKM.JK",
    "ADRO.JK", "PTBA.JK", "UNTR.JK", "MEDC.JK", "PGAS.JK", "AKRA.JK",
    "MAPI.JK", "ACES.JK", "AMRT.JK", "ICBP.JK", "INDF.JK", "MYOR.JK",
    "CPIN.JK", "JPFA.JK", "KLBF.JK", "INKP.JK", "TKIM.JK", "SMGR.JK",
    "INTP.JK", "ANTM.JK", "INCO.JK", "MDKA.JK", "TINS.JK", "BSSR.JK",
    "BRIS.JK", "BSDE.JK", "CTRA.JK", "PWON.JK", "SMRA.JK", "GOTO.JK"
]

def analyze_ticker(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="60d")
        if len(df) < 25:
            return None

        close = float(df['Close'].iloc[-1])
        vol20 = float(df['Volume'].iloc[-20:].mean())
        val20 = float((df['Close'] * df['Volume']).iloc[-20:].mean())

        # Filter likuiditas minimal Swing5D (Volume >= 1M atau Value >= 10M)
        is_very_liquid = vol20 >= 5_000_000 and val20 >= 25_000_000_000
        is_liquid = vol20 >= 1_000_000 or val20 >= 10_000_000_000
        if not (is_liquid or is_very_liquid):
            return None

        # MA & Sinyal Swing
        ma20 = float(df['Close'].rolling(20).mean().iloc[-1])
        low20 = float(df['Low'].iloc[-20:].min())
        high20 = float(df['High'].iloc[-20:].max())

        # TP / SL calculation (Swing 1-5D)
        sl = round(max(low20, close * 0.95), 0)
        tp = round(min(high20 * 1.05, close * 1.10), 0)
        risk = max(1.0, close - sl)
        reward = max(1.0, tp - close)
        rrr = round(reward / risk, 2)

        # Zona Buy/Hold/Sell/Breakout
        if close > high20 * 0.99:
            zone = "BREAKOUT"
        elif close <= ma20 * 1.02 and close >= ma20 * 0.97:
            zone = "IN_BUY_ZONE"
        elif close > ma20 * 1.02:
            zone = "HOLD"
        else:
            zone = "SELL"

        potensi_naik = round(((tp - close) / close) * 100, 1)
        risiko_turun = round(((close - sl) / close) * 100, 1)

        clean_symbol = ticker.replace(".JK", "")

        return {
            "symbol": clean_symbol,
            "close": int(close),
            "potensi_naik": potensi_naik,
            "risiko_turun": risiko_turun,
            "liquidity": "Very Liquid" if is_very_liquid else "Liquid",
            "zone": zone,
            "pred": "UP" if close >= ma20 else "DOWN",
            "rrr": rrr,
            "tp": int(tp),
            "sl": int(sl)
        }
    except Exception as e:
        return None

def main():
    results = []
    for ticker in WATCHLIST:
        data = analyze_ticker(ticker)
        if data:
            results.append(data)

    # Sort berdasarkan potensi naik & filter buy zone prioritas
    results.sort(key=lambda x: (x['zone'] == 'IN_BUY_ZONE', x['rrr'] >= 1.5, x['potensi_naik']), reverse=True)

    output = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB"),
        "total_screened": len(WATCHLIST),
        "data": results
    }

    with open("data/screener.json", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()
