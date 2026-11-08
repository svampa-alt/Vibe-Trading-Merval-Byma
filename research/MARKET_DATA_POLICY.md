# Market data policy for Bolsa research

Effective 2026-11-08 across Bolsa experiments and tools in this repository.

## Canonical daily series

Yahoo Finance is the required final source for historical daily price bars and closing-price analysis whenever Yahoo returns a usable series. Download with `auto_adjust=True`; this produces a consistent split/dividend-adjusted close series for return calculations. Do not mix it with raw closes or silently replace it with another provider.

Before analysis, validate each Yahoo daily bar: all OHLC values must be finite and positive, dates must be unique, and high/low must contain open and close. Exclude malformed bars and report their count in the workflow log. If Yahoo is unavailable, returns no valid bars, or the remaining sample fails the predeclared minimum, mark the result unavailable/insufficient. Do not fill the gap with IOL or another source.

## Separate intraday quotes and actual transactions

IOL may supply current intraday bid/ask, depth and timestamps for an explicitly intraday execution-feasibility check. Keep those observations separate from the Yahoo daily close series; they must not overwrite or be mixed into daily history. Actual fills and costs come from the broker's execution records.

## Required application and reporting

This rule covers randomized, cross-asset, event, sector, hypothesis, portfolio research and every market-data tool used for Bolsa. Every output must identify the Yahoo ticker, source, adjustment caliber, date range and validation outcome. Existing artifacts remain historical evidence; new analyses use this rule and clearly mark incompatible legacy results as superseded. Research findings remain exploratory and are never buy/sell recommendations.
