import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from frontend.services.movers import MarketMoversService


def test_movers():
    print("🚀 Initializing MarketMoversService...")
    try:
        service = MarketMoversService.get_instance()

        categories = [
            "NSE_MAIN",
            "NSE_SME",
            "NSE_FUT",
            "NSE_FO_EQ",
            "NIFTY_50",
            "NIFTY_500",
            "NIFTY_BANK",
        ]

        for cat in categories:
            print(f"\n📊 Fetching movers for category: {cat}")
            result = service.get_movers(cat)

            gainers = result.get("gainers", [])
            losers = result.get("losers", [])

            print(f"   ✅ Received {len(gainers)} gainers and {len(losers)} losers")

            if gainers:
                top = gainers[0]
                print(f"   📈 Top Gainer: {top['symbol']} ({top['pct_change']:.2f}%)")

            if losers:
                top = losers[0]
                print(f"   📉 Top Loser: {top['symbol']} ({top['pct_change']:.2f}%)")

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_movers()
