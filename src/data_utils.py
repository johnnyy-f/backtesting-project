import os
import time
from datetime import datetime, timedelta

import oandapyV20
import pandas as pd
from dotenv import load_dotenv
from oandapyV20.endpoints.accounts import AccountInstruments
from oandapyV20.endpoints.instruments import InstrumentsCandles

# --- OANDA Client Setup ---


def get_oanda_client():
    """
    Loads environment variables and initializes the OANDA API client.

    Returns:
        oandapyV20.API: The initialized client object.
        str: The account ID.
    """
    # Load .env file (if not loaded globally)
    load_dotenv()

    api_key = os.getenv("OANDA_API_KEY")
    account_id = os.getenv("OANDA_ACCOUNT_ID")

    if not api_key or not account_id:
        raise ValueError(
            "OANDA_API_KEY and OANDA_ACCOUNT_ID must be set in the .env file."
        )

    client = oandapyV20.API(access_token=api_key)
    return client, account_id


def print_acceptable_instruments():
    """
    Connects to OANDA and prints all available trading instruments
    for the configured account.
    """
    client, account_id = get_oanda_client()

    # Define the endpoint request
    r = AccountInstruments(account_id)

    try:
        # Submit the request
        client.request(r)

        print(f"\n--- Acceptable Instruments for Account ID: {account_id} ---")

        # The response is in r.response['instruments']
        for i, instrument_data in enumerate(r.response["instruments"]):
            # Extract key information for a clean output
            name = instrument_data["name"]
            display_name = instrument_data["displayName"]
            type_ = instrument_data["type"]

            print(f"  {i+1}. {name} ({display_name}) [Type: {type_}]")

        print("----------------------------------------------------------")

    except Exception as e:
        print(f"Error fetching instruments: {e}")


def fetch_instrument_candles(
    instrument: str, granularity: str, start: None, end=None, count: int = 5000
) -> pd.DataFrame:
    """
    Fetches historical candle data for a given instrument and granularity.

    Args:
        instrument (str): The instrument name (e.g., 'NATGAS_USD').
        granularity (str): The candle duration (e.g., 'M15', 'H4', 'D').
        count (int): The number of candles to retrieve (max 5000 per request).

    Returns:
        pd.DataFrame: A DataFrame of historical prices, or None on failure.
    """
    client, _ = get_oanda_client()

    try:
        # Handle missing start/end defaults
        if start is None:
            start = datetime.utcnow() - timedelta(days=7)
        if end is None:
            end = datetime.utcnow()

        start_dt = pd.to_datetime(start).tz_localize("UTC")
        end_dt = pd.to_datetime(end).tz_localize("UTC")

        # # Parameters for the API request
        # params = {
        #     "granularity": granularity,
        #     "count": count
        # }

        all_candles = []
        next_from = start_dt
        iteration = 0

        # t0 = time.time()

        save_path = (
            f"../data/{instrument}_{granularity}_{start_dt.date()}_{end_dt.date()}.csv"
        )

        while next_from < end_dt:
            iteration += 1
            req_start = time.time()

            print(f"[{iteration}] Requesting data FROM: {next_from}")

            params = {
                "granularity": granularity,
                "from": next_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "count": 5000,
            }

            try:
                r = InstrumentsCandles(instrument=instrument, params=params)
                data = client.request(r)
            except Exception as e:
                print(f"Request failed: {e}")
                break

            candles = data.get("candles", [])

            req_time = time.time() - req_start
            print(
                f"[{iteration}] Response received in {req_time:.3f}s. "
                f"Candles returned: {len(candles)}"
            )

            if not candles:
                print(f"[{iteration}] No candles returned. Stopping.")
                break

            parsed = [
                {
                    "datetime": candle["time"],
                    "open": float(candle["mid"]["o"]),
                    "high": float(candle["mid"]["h"]),
                    "low": float(candle["mid"]["l"]),
                    "close": float(candle["mid"]["c"]),
                    "volume": candle["volume"],
                }
                for candle in candles
                if candle.get("complete", True)
            ]

            all_candles.extend(parsed)

            last_ts = pd.to_datetime(parsed[-1]["datetime"])
            print(f"[{iteration}] Last candle timestamp: {last_ts}")

            # --- FIX: Detect if the timestamp did not advance ---
            if len(all_candles) > 1 and last_ts <= pd.to_datetime(
                all_candles[-2]["datetime"]
            ):
                print(
                    "Detected timestamp stall. Stopping loop to avoid infinite requests."
                )
                break

            next_from = last_ts + pd.Timedelta(milliseconds=1)

            if next_from >= end_dt:
                print(f"[{iteration}] Reached END date, stopping loop.")
                break

        # Create DataFrame
        df = pd.DataFrame(all_candles)
        if df.empty:
            print("No data returned. Exiting.")
            return df

        # Clean up and format the DataFrame
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.set_index("datetime")

        # TO DO????
        df.to_csv(save_path)
        print(f"Saved {len(df)} candles to {save_path}")

        print(
            f"Successfully fetched {len(df)} candles for {instrument} at {granularity}."
        )
        return df

    except Exception as e:
        print(f"Error fetching candles for {instrument}: {e}")
        return None


import numpy as np
import pandas as pd


def compute_sharpe_metrics(df, start_cash, risk_free_rate=0.0004):
    """
    Computes daily returns, fills missing dates, and calculates annualised
    volatility and Sharpe ratio.

    Parameters:
        df (pd.DataFrame): Must contain columns ['exit_time', 'pnl']
        start_cash (float): Initial capital
        risk_free_rate (float): Annual risk-free rate (default 0.0004)

    Returns:
        daily_returns_complete (pd.DataFrame)
        annual_vol (float)
        annual_sharpe (float)
        mean_daily_return (float)
    """

    # --- Convert exit_time to date and compute daily pnl ---
    df["exit_date"] = pd.to_datetime(df["exit_time"]).dt.date
    daily_pnl = df.groupby("exit_date")["pnl"].sum()

    # Compute daily returns
    daily_returns = daily_pnl / start_cash
    daily_returns = pd.DataFrame(daily_returns)
    daily_returns.columns = ["pnl"]  # ensure consistent naming

    # --- Create full date range ---
    start_date = daily_returns.index.min()
    end_date = daily_returns.index.max()

    full_date_range = pd.date_range(start=start_date, end=end_date, freq="D")

    # --- Reindex + fill missing with 0 ---
    daily_returns_reindexed = daily_returns.reindex(full_date_range)
    daily_returns_complete = daily_returns_reindexed.fillna(0.0)

    # Extract the series
    daily_returns_series = daily_returns_complete["pnl"]

    # --- Compute metrics ---
    daily_vol = daily_returns_series.std()
    annual_vol = daily_vol * np.sqrt(252)

    daily_rf = risk_free_rate / 252
    daily_sharpe = (daily_returns_series.mean() - daily_rf) / daily_vol
    annual_sharpe = daily_sharpe * np.sqrt(252)

    mean_daily_return = daily_returns_series.mean()

    return daily_returns_complete, annual_vol, annual_sharpe, mean_daily_return
