"""Canonical Yahoo daily price loader and OHLC quality gate for Bolsa research."""
from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf


def _one_column(frame: pd.DataFrame, field: str, ticker: str) -> pd.Series:
    if field not in frame.columns.get_level_values(0):
        raise RuntimeError(f"Yahoo response for {ticker} lacks {field}")
    values = frame[field]
    if isinstance(values, pd.DataFrame):
        if values.shape[1] != 1:
            raise RuntimeError(f"Yahoo returned ambiguous {field} columns for {ticker}")
        values = values.iloc[:, 0]
    return pd.to_numeric(values, errors="coerce")


def yahoo_adjusted_close(ticker: str, *, start: str, end: str | None = None) -> pd.Series:
    """Return Yahoo's adjusted daily close after OHLC validation.

    Yahoo is the primary historical source. Malformed rows are excluded and
    counted in Series.attrs. This loader does not retrieve fallback providers;
    callers must fill Yahoo gaps only from individually validated, adjustment-
    compatible IOL rows or another independent verified source, recording
    provenance. If no source passes validation, the date remains unavailable.
    """
    frame = yf.download(
        ticker,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    if frame.empty:
        raise RuntimeError(f"No Yahoo Finance daily data for {ticker}")

    ohlc = pd.DataFrame(
        {field.lower(): _one_column(frame, field, ticker)
         for field in ("Open", "High", "Low", "Close")}
    )
    ohlc.index = pd.to_datetime(ohlc.index).tz_localize(None).normalize()
    if ohlc.index.has_duplicates:
        duplicates = int(ohlc.index.duplicated(keep=False).sum())
        raise RuntimeError(f"Yahoo returned {duplicates} duplicate daily bars for {ticker}")
    ohlc = ohlc.sort_index()

    values = ohlc.to_numpy(dtype=float)
    valid = np.isfinite(values).all(axis=1) & (values > 0).all(axis=1)
    valid &= ohlc["high"].to_numpy() >= ohlc[["open", "close", "low"]].max(axis=1).to_numpy()
    valid &= ohlc["low"].to_numpy() <= ohlc[["open", "close", "high"]].min(axis=1).to_numpy()
    invalid_count = int((~valid).sum())
    if invalid_count:
        print(f"Yahoo OHLC quality gate: excluded {invalid_count} malformed daily bars for {ticker}")
    if not valid.any():
        raise RuntimeError(f"Yahoo returned no OHLC-valid daily bars for {ticker}")

    close = ohlc.loc[valid, "close"].rename(ticker)
    close.attrs["source"] = "Yahoo Finance"
    close.attrs["adjustment"] = "auto_adjust=True (split/dividend-adjusted)"
    close.attrs["invalid_ohlc_rows_excluded"] = invalid_count
    close.attrs["validated_rows"] = int(valid.sum())
    return close
