import hashlib
import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from market_data_policy import yahoo_adjusted_close
from scipy.stats import ttest_ind

REQUEST_PATH = Path("research/hypothesis_search_request.json")
REGISTRY_PATH = Path("research/hypothesis_search_registry.json")
UNIVERSE = {
    "PAMP.BA": "PAMP", "ALUA.BA": "ALUA", "BMA.BA": "BMA",
    "GGAL.BA": "GGAL", "SUPV.BA": "SUPV", "^MERV": "Merval",
    "BZ=F": "Brent", "GC=F": "Gold", "SPY": "S&P 500 ETF",
    "EWZ": "Brazil ETF",
}
THRESHOLDS = (1.5, 3.0, 5.0, 7.0, 9.0)
HORIZONS = (2, 4, 10)
TRAIN_CUTOFF = pd.Timestamp("2020-12-31")
MIN_TRAIN_EVENTS = 20
MIN_TEST_EVENTS = 10
MIN_BASELINE = 50


def candidate_id(src, dst, direction, threshold, horizon):
    raw = f"{src}|{dst}|{direction}|{threshold:.1f}|{horizon}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def main():
    request = json.loads(REQUEST_PATH.read_text())
    registry = json.loads(REGISTRY_PATH.read_text())
    run_key = str(request["run_key"])
    if run_key in registry.get("processed_run_keys", []):
        raise RuntimeError(f"Duplicate request run_key: {run_key}")

    pool = []
    for src in UNIVERSE:
        for dst in UNIVERSE:
            if src == dst:
                continue
            for direction in ("up", "down"):
                for threshold in THRESHOLDS:
                    for horizon in HORIZONS:
                        pool.append({
                            "candidate_id": candidate_id(src, dst, direction, threshold, horizon),
                            "source": src, "target": dst, "direction": direction,
                            "threshold_pct": threshold, "horizon_sessions": horizon,
                        })
    seen = {r["candidate_id"] for r in registry.get("records", [])}
    untried = [c for c in pool if c["candidate_id"] not in seen]
    if not untried:
        raise RuntimeError("Candidate pool exhausted; no repeat was made.")
    rng = random.Random(str(request["seed"]))
    candidate = rng.choice(untried)
    record = {
        **candidate,
        "run_key": run_key,
        "seed": str(request["seed"]),
        "selected_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_source": "Yahoo Finance adjusted daily Close (auto_adjust=True); OHLC-validated",
    }

    try:
        series = {}
        for ticker in (candidate["source"], candidate["target"]):
            close = yahoo_adjusted_close(ticker, start="2010-01-01")
            series[ticker] = close.rename(ticker)

        pair = pd.concat(series.values(), axis=1, join="inner").dropna().sort_index()
        if len(pair) < 250:
            raise RuntimeError(f"Only {len(pair)} aligned observations for this pair")

        dates = pd.Series(pair.index, index=pair.index)
        source_returns = pair[candidate["source"]].pct_change(fill_method=None)
        target_forward = (
            pair[candidate["target"]].shift(-candidate["horizon_sessions"])
            / pair[candidate["target"]] - 1
        )
        end_dates = dates.shift(-candidate["horizon_sessions"])
        if candidate["direction"] == "up":
            signal = source_returns > candidate["threshold_pct"] / 100
            condition = f'rises more than {candidate["threshold_pct"]:.1f}%'
        else:
            signal = source_returns < -candidate["threshold_pct"] / 100
            condition = f'falls more than {candidate["threshold_pct"]:.1f}%'

        train_ok = (dates <= TRAIN_CUTOFF) & (end_dates <= TRAIN_CUTOFF) & target_forward.notna() & signal.notna()
        test_ok = (dates > TRAIN_CUTOFF) & end_dates.notna() & target_forward.notna() & signal.notna()
        train_event, train_base = train_ok & signal, train_ok & ~signal
        test_event, test_base = test_ok & signal, test_ok & ~signal
        train_event_values, train_base_values = target_forward.loc[train_event], target_forward.loc[train_base]
        test_event_values, test_base_values = target_forward.loc[test_event], target_forward.loc[test_base]

        record.update({
            "aligned_start": str(pair.index.min().date()),
            "aligned_end": str(pair.index.max().date()),
            "hypothesis": (
                f'If {UNIVERSE[candidate["source"]]} {condition}, '
                f'{UNIVERSE[candidate["target"]]} return over the next '
                f'{candidate["horizon_sessions"]} aligned sessions differs from its non-event baseline.'
            ),
            "train_event_n": int(train_event.sum()),
            "train_baseline_n": int(train_base.sum()),
            "test_event_n": int(test_event.sum()),
            "test_baseline_n": int(test_base.sum()),
        })

        if len(train_event_values) < MIN_TRAIN_EVENTS or len(train_base_values) < MIN_BASELINE:
            record.update({
                "status": "failed_insufficient_training_sample",
                "failure_reason": "Training events or baseline are below the predeclared minimum.",
            })
        elif len(test_event_values) < MIN_TEST_EVENTS or len(test_base_values) < MIN_BASELINE:
            record.update({
                "status": "failed_insufficient_holdout_sample",
                "failure_reason": "Holdout events or baseline are below the predeclared minimum.",
            })
        else:
            p_train = float(ttest_ind(train_event_values, train_base_values, equal_var=False, nan_policy="omit").pvalue)
            p_test = float(ttest_ind(test_event_values, test_base_values, equal_var=False, nan_policy="omit").pvalue)
            train_edge = float((train_event_values.mean() - train_base_values.mean()) * 100)
            test_edge = float((test_event_values.mean() - test_base_values.mean()) * 100)
            # A summable alpha-spending rule limits false positives across repeated daily searches.
            test_index = int(registry.get("prior_confirmatory_tests", 0)) + len(registry.get("records", [])) + 1
            alpha_boundary = 0.05 / (test_index * (test_index + 1))
            same_sign = (train_edge > 0) == (test_edge > 0)
            passed = math.isfinite(p_test) and p_test <= alpha_boundary and same_sign
            record.update({
                "status": "passed_sequential_holdout_rule" if passed else "failed_holdout_rule",
                "train_event_mean_pct": float(train_event_values.mean() * 100),
                "train_baseline_mean_pct": float(train_base_values.mean() * 100),
                "train_edge_pct": train_edge,
                "train_p_raw": p_train if math.isfinite(p_train) else None,
                "test_event_mean_pct": float(test_event_values.mean() * 100),
                "test_baseline_mean_pct": float(test_base_values.mean() * 100),
                "test_edge_pct": test_edge,
                "test_p_raw": p_test if math.isfinite(p_test) else None,
                "test_index_for_alpha_spending": test_index,
                "alpha_spending_boundary": alpha_boundary,
                "same_edge_sign_train_test": same_sign,
                "failure_reason": None if passed else "Did not meet the predeclared sequential holdout threshold and same-sign rule.",
            })
    except Exception as exc:
        record.update({
            "status": "failed_data_or_execution",
            "failure_reason": str(exc),
        })

    registry.setdefault("records", []).append(record)
    registry.setdefault("processed_run_keys", []).append(run_key)
    registry["last_run_key"] = run_key
    registry["last_updated_utc"] = datetime.now(timezone.utc).isoformat()
    registry["candidate_pool_size"] = len(pool)
    registry["candidate_pool_remaining"] = max(0, len(untried) - 1)
    registry["method"] = (
        "Random selection without replacement from a predeclared pool. "
        "Every outcome, including failures, is stored. Holdout p-values use "
        "alpha spending 0.05/[i(i+1)] and must retain the training edge sign."
    )
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2))
    result = {
        "run_key": run_key,
        "candidate": record,
        "candidate_pool_size": len(pool),
        "candidate_pool_remaining": registry["candidate_pool_remaining"],
        "caveat": (
            "Exploratory research only. Prices are nominal; horizons are aligned "
            "market observations, not exact calendar days; Welch tests do not fully "
            "model serial dependence or market regimes."
        ),
    }
    Path("random_hypothesis_result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
