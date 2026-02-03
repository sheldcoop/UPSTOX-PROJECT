#!/usr/bin/env python3
"""
Data Management Blueprint
Handles data downloads and related endpoints
"""

from flask import Blueprint, jsonify, g, request
from datetime import datetime
from pathlib import Path
import logging

data_bp = Blueprint("data", __name__, url_prefix="/api")

logger = logging.getLogger(__name__)

DB_PATH = "market_data.db"


@data_bp.route("/download/stocks", methods=["POST"])
def download_stocks():
    """
    Download stock OHLC data from Yahoo Finance
    Request body:
    {
        "symbols": ["INFY", "TCS"],
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "interval": "1d",
        "save_db": true,
        "export_format": "parquet"
    }
    """
    try:
        from data_downloader import StockDownloader

        data = request.get_json()
        logger.info(
            f"[TraceID: {g.trace_id}] Stock download requested: {data.get('symbols')}"
        )

        # Validate input
        required = ["symbols", "start_date", "end_date"]
        for field in required:
            if field not in data:
                logger.warning(
                    f"[TraceID: {g.trace_id}] Missing required field: {field}"
                )
                return jsonify({"error": f"Missing required field: {field}"}), 400

        symbols = data["symbols"]
        start_date = data["start_date"]
        end_date = data["end_date"]
        interval = data.get("interval", "1d")
        save_db = data.get("save_db", True)
        export_format = data.get("export_format", "parquet")

        logger.debug(
            f"[TraceID: {g.trace_id}] Params: symbols={symbols}, interval={interval}, save_db={save_db}"
        )

        # Download data
        downloader = StockDownloader(db_path=DB_PATH)
        result = downloader.download_and_process(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            save_db=save_db,
            export_format=export_format,
        )

        logger.info(
            f"[TraceID: {g.trace_id}] Download complete: {result['rows']} rows, {len(result['gaps'])} gaps"
        )

        return jsonify(
            {
                "success": True,
                "trace_id": g.trace_id,
                "rows": result["rows"],
                "filepath": result["filepath"],
                "gaps": result["gaps"],
                "validation_errors": result["validation_errors"],
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] Stock download failed: {e}", exc_info=True
        )
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500


@data_bp.route("/download/history", methods=["GET"])
def download_history():
    """Get list of downloaded files"""
    try:
        logger.debug(f"[TraceID: {g.trace_id}] Fetching download history")

        downloads_dir = Path("downloads")
        if not downloads_dir.exists():
            return jsonify({"files": []})

        files = []
        for file in downloads_dir.iterdir():
            if file.is_file():
                stat = file.stat()
                files.append(
                    {
                        "filename": file.name,
                        "size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "format": file.suffix.lstrip("."),
                    }
                )

        # Sort by creation date (newest first)
        files.sort(key=lambda x: x["created_at"], reverse=True)

        logger.info(f"[TraceID: {g.trace_id}] Found {len(files)} downloaded files")

        return jsonify({"files": files, "total": len(files)})

    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] Failed to fetch download history: {e}",
            exc_info=True,
        )
        return jsonify({"error": str(e)}), 500


@data_bp.route("/download/logs", methods=["GET"])
def download_logs():
    """Get recent download logs"""
    try:
        logger.debug(f"[TraceID: {g.trace_id}] Fetching download logs")

        log_file = Path("logs/data_downloader.log")
        if not log_file.exists():
            return jsonify({"logs": []})

        # Read last 100 lines
        with open(log_file, "r") as f:
            lines = f.readlines()
            recent_logs = lines[-100:] if len(lines) > 100 else lines

        logger.info(f"[TraceID: {g.trace_id}] Returning {len(recent_logs)} log lines")

        return jsonify({"logs": recent_logs, "total_lines": len(recent_logs)})

    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] Failed to fetch logs: {e}", exc_info=True
        )
        return jsonify({"error": str(e)}), 500


@data_bp.route("/options/chain", methods=["GET"])
def get_options_chain():
    """
    Get live options chain data
    Query params:
        symbol: Underlying symbol (NIFTY, BANKNIFTY, RELIANCE, etc.)
        expiry_date: Optional expiry date (YYYY-MM-DD)
    """
    try:
        from options_chain_service import OptionsChainService

        symbol = request.args.get("symbol")
        expiry_date = request.args.get("expiry_date")

        if not symbol:
            logger.warning(f"[TraceID: {g.trace_id}] Missing symbol parameter")
            return jsonify({"error": "Symbol parameter required"}), 400

        logger.info(
            f"[TraceID: {g.trace_id}] Options chain requested: symbol={symbol}, expiry={expiry_date}"
        )

        # Fetch option chain
        service = OptionsChainService(db_path=DB_PATH)
        chain_data = service.get_option_chain(symbol=symbol, expiry_date=expiry_date)

        logger.info(
            f"[TraceID: {g.trace_id}] Returning {len(chain_data['strikes'])} strikes"
        )

        return jsonify(chain_data)

    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] Options chain fetch failed: {e}", exc_info=True
        )
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500


@data_bp.route("/options/market-status", methods=["GET"])
def get_market_status():
    """Check if market is currently open"""
    try:
        from options_chain_service import OptionsChainService

        logger.debug(f"[TraceID: {g.trace_id}] Market status check")

        service = OptionsChainService(db_path=DB_PATH)
        is_open, message = service.is_market_open()

        return jsonify(
            {
                "market_open": is_open,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] Market status check failed: {e}", exc_info=True
        )
        return jsonify({"error": str(e)}), 500


@data_bp.route("/page/downloads", methods=["GET"])
def downloads_page():
    """Render the data downloads page"""
    from flask import render_template

    try:
        logger.debug(f"[TraceID: {g.trace_id}] Rendering downloads page")
        return render_template("downloads_new.html")
    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] Downloads page error: {e}", exc_info=True
        )
        return jsonify({"error": "Failed to load downloads page"}), 500


# ============================================================================
# EXPIRED OPTIONS DATA ENDPOINTS
# ============================================================================


@data_bp.route("/expired/expiries", methods=["GET"])
def get_expired_expiries_list():
    """
    Get available expiry dates for an underlying symbol (Expired Options)
    Query Params: underlying (e.g. NIFTY)
    """
    try:
        from scripts.expired_options_fetcher import get_available_expiries

        underlying = request.args.get("underlying")
        if not underlying:
            return jsonify({"error": "Underlying symbol required"}), 400

        logger.info(f"[TraceID: {g.trace_id}] Fetching expiries for {underlying}")

        expiries = get_available_expiries(underlying)

        return jsonify(
            {"success": True, "underlying": underlying, "expiries": expiries}
        )

    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] Fetching expiries failed: {e}", exc_info=True
        )
        return jsonify({"error": str(e)}), 500


@data_bp.route("/expired/download", methods=["POST"])
def download_expired_data():
    """
    Download and store expired option chain data
    Body: {
        "underlying": "NIFTY",
        "expiries": ["2025-01-22", ...],
        "option_type": "CE" (optional),
        "download_candles": true,
        "interval": "30minute"
    }
    """
    try:
        from scripts.expired_options_fetcher import (
            fetch_expired_option_contracts,
            fetch_expired_future_contracts,
            parse_option_data,
            parse_future_data,
            store_expired_options,
            fetch_expired_historical_candles,
            store_expired_candles,
        )
        from datetime import datetime, timedelta

        data = request.json
        underlying = data.get("underlying")
        expiries = data.get("expiries", [])
        option_type = data.get("option_type")
        download_candles = data.get("download_candles", False)
        fetch_futures = data.get("fetch_futures", False)
        interval = data.get("interval", "day")

        if not underlying or not expiries:
            return jsonify({"error": "Underlying and Expiries list required"}), 400

        logger.info(
            f"[TraceID: {g.trace_id}] Downloading expired for {underlying}, candles={download_candles}, futures={fetch_futures}"
        )

        total_records = 0
        total_candles = 0
        results = []

        for expiry in expiries:
            try:
                # 1. Fetch Options Contracts
                contracts = fetch_expired_option_contracts(
                    underlying, expiry, option_type
                )

                # Parse & Store Options
                parsed_opts = []
                for c in contracts:
                    parsed = parse_option_data(c, underlying, expiry)
                    parsed_opts.append(parsed)

                count = store_expired_options(parsed_opts)
                total_records += count

                # 1.1 Fetch Futures (Optional)
                if fetch_futures:
                    f_contracts = fetch_expired_future_contracts(underlying, expiry)
                    parsed_futs = []
                    for c in f_contracts:
                        parsed = parse_future_data(c, underlying, expiry)
                        parsed_futs.append(parsed)

                    f_count = store_expired_options(parsed_futs)
                    total_records += f_count
                    # Include futures in candle download loop
                    contracts.extend(f_contracts)

                # 2. Download Candles (for Options only likely, unless we extend to futures later)

                # 3. Fetch Candles (if requested)
                candles_status = "skipped"
                candles_count = 0

                if download_candles and contracts:
                    # Determine date range (Expiry Date back 100 days to cover contract life)
                    # Expiry format: YYYY-MM-DD
                    try:
                        exp_dt = datetime.strptime(expiry, "%Y-%m-%d")
                        to_date = expiry
                        from_date = (exp_dt - timedelta(days=120)).strftime("%Y-%m-%d")

                        for contract in contracts:
                            # Construct correct instrument key: "NSE_FO|{token}|{expiry}" or similar
                            # The API expects 'expired_instrument_key'.
                            # Let's check what 'fetch_expired_option_contracts' returns in 'instrument_key'.
                            # In parsed_option_data, we might have it.
                            # Upstox expired key format: NSE_FO|Token|dd-mm-yyyy (Maybe?)
                            # Actually, documentation says: "combination of standard instrument key and expiry date"

                            # Let's trust the instrument_key returned by fetch_expired_option_contracts if available
                            # Usually contract['instrument_key'] is enough? No, for expired it's special.
                            # Docs say: NSE_FO|54452|24-04-2025

                            i_key = contract.get("instrument_key")

                            # If fetched, try to get candles
                            c_data = fetch_expired_historical_candles(
                                i_key, interval, from_date, to_date
                            )
                            if c_data:
                                saved = store_expired_candles(i_key, interval, c_data)
                                candles_count += saved

                        candles_status = f"success ({candles_count})"
                        total_candles += candles_count

                    except Exception as date_e:
                        logger.error(f"Date error for candles: {date_e}")
                        candles_status = "date_error"

                results.append(
                    {
                        "expiry": expiry,
                        "status": "success",
                        "count": count,
                        "candles": candles_status,
                    }
                )

            except Exception as inner_e:
                logger.error(f"Failed for expiry {expiry}: {inner_e}")
                results.append(
                    {"expiry": expiry, "status": "failed", "error": str(inner_e)}
                )

        return jsonify(
            {
                "success": True,
                "total_records": total_records,
                "total_candles": total_candles,
                "results": results,
            }
        )

    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] Expired download failed: {e}", exc_info=True
        )
        return jsonify({"error": str(e)}), 500


@data_bp.route("/market-quote", methods=["POST"])
def get_market_quote():
    """
    Get full market quote (LTP, Depth, OHLC) for list of symbols.
    Request body: { "symbols": ["INFY", "NHPC", "NSE_EQ|..."] }
    """
    try:
        from scripts.market_quote_fetcher import MarketQuoteFetcher

        data = request.json
        symbols = data.get("symbols", [])

        if not symbols:
            return jsonify({"error": "No symbols provided"}), 400

        logger.info(f"[TraceID: {g.trace_id}] Fetching market quotes for: {symbols}")

        fetcher = MarketQuoteFetcher(db_path=DB_PATH)
        quotes = fetcher.fetch_quotes(symbols)

        if "error" in quotes:
            return jsonify(quotes), 400

        return jsonify(
            {
                "status": "success",
                "data": quotes,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Market Quote Error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
