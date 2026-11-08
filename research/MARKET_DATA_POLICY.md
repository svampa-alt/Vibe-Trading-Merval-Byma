# Market data policy for Bolsa research

Effective 2026-11-08 across Bolsa experiments and tools in this repository.

## Canonical daily series

Yahoo Finance is the primary source for historical daily price bars and closing-price analysis when its rows pass validation. Download with `auto_adjust=True` and keep that split/dividend-adjusted basis consistent. If a Yahoo date is missing or invalid, fill that date from IOL only when the IOL row independently passes validation and is adjustment-compatible; otherwise search for another independent, verified source. Record source and adjustment per ticker/date, preserve raw inputs, and never mix adjustment bases without explicit normalization.

Before analysis, validate each source row: OHLC values must be finite and positive, dates unique, and high/low must contain open and close. Exclude malformed rows and report them. Keep Yahoo wherever its row is valid; use a verified, compatible fallback only for the individual missing/invalid Yahoo date. If no source passes, mark that date unavailable; do not invent or forward-fill. The predeclared minimum still applies after fallback.

## Separate intraday quotes and actual transactions

IOL may supply current intraday bid/ask, depth and timestamps for an explicitly intraday execution-feasibility check. Keep those observations separate from the Yahoo daily close series; they must not overwrite or be mixed into daily history. Actual fills and costs come from the broker's execution records.

## Required application and reporting

This rule covers randomized, cross-asset, event, sector, hypothesis, portfolio research and every market-data tool used for Bolsa. Every output must identify the Yahoo ticker, source, adjustment caliber, date range and validation outcome. Existing artifacts remain historical evidence; new analyses use this rule and clearly mark incompatible legacy results as superseded. Research findings remain exploratory and are never buy/sell recommendations.
