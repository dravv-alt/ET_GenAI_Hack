"""LLM-based plain-English explanations for detected patterns."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional, Tuple

import requests

from dotenv import load_dotenv

_ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(_ENV_PATH)

_EXPLAIN_CACHE: Dict[Tuple[str, ...], Dict[str, Any]] = {}
_EXPLAIN_RATE_LIMIT_SECONDS = 45


def _rule_based_explanation(pattern: Dict[str, Any], backtest: Optional[Dict[str, Any]]) -> str:
	pattern_type = pattern.get("pattern_type", "pattern").replace("_", " ")
	confidence = pattern.get("confidence")
	entry = pattern.get("entry_price")
	stop = pattern.get("stop_loss")
	target = pattern.get("target_price")

	confidence_text = (
		f"Confidence is around {round(confidence * 100, 1)}%."
		if confidence is not None
		else "Confidence is not available."
	)

	backtest_line = "There is no reliable backtest for this pattern yet."
	if backtest:
		sample = backtest.get("sample_count")
		win_rate = backtest.get("win_rate")
		median = backtest.get("median_return_pct")
		if sample and win_rate is not None:
			win_pct = round(win_rate * 100, 1)
			median_text = f"median return around {median}%" if median is not None else "median return is not available"
			backtest_line = (
				f"Historically this setup worked about {win_pct}% of the time "
				f"across {sample} past cases, with {median_text}."
			)

	return (
		f"This looks like a {pattern_type} setup. {confidence_text} "
		f"That suggests a potential move if price holds the key levels.\n\n"
		f"{backtest_line}\n\n"
		f"A simple way to manage risk is to watch the stop level near {stop} and the target near {target}. "
		f"If price falls below support or quickly rejects the breakout zone, the setup weakens."
	)


def _build_prompt(pattern: Dict[str, Any], backtest: Optional[Dict[str, Any]]) -> str:
	pattern_type = pattern.get("pattern_type", "pattern").replace("_", " ")
	name = pattern.get("name") or pattern_type
	detected_on = pattern.get("detected_on")
	confidence = pattern.get("confidence")
	entry = pattern.get("entry_price")
	stop = pattern.get("stop_loss")
	target = pattern.get("target_price")
	key_levels = pattern.get("key_levels")

	metrics = {}
	if backtest:
		metrics = {
			"sample_count": backtest.get("sample_count"),
			"win_rate": backtest.get("win_rate"),
			"avg_gain_pct": backtest.get("avg_gain_pct"),
			"avg_loss_pct": backtest.get("avg_loss_pct"),
			"median_return_pct": backtest.get("median_return_pct"),
			"profit_factor": backtest.get("profit_factor"),
			"expectancy": backtest.get("expectancy"),
			"max_drawdown_pct": backtest.get("max_drawdown_pct"),
			"calmar_ratio": backtest.get("calmar_ratio"),
			"sharpe_ratio": backtest.get("sharpe_ratio"),
			"sortino_ratio": backtest.get("sortino_ratio"),
			"exposure_pct": backtest.get("exposure_pct"),
			"avg_time_in_trade_bars": backtest.get("avg_time_in_trade_bars"),
			"note": backtest.get("note"),
		}

	return (
		"Write a plain-English explanation for a retail investor. "
		"Avoid dumping raw numbers; interpret them in words. "
		"Keep it concise: 3 short paragraphs (2-3 sentences each). "
		"Paragraph 1: what the pattern signals and why it matters now. "
		"Paragraph 2: summarize backtest quality and what it implies (use numbers only if essential). "
		"Paragraph 3: invalidation/risks and what to watch next.\n\n"
		"Do NOT list fields; explain in narrative form.\n\n"
		f"Pattern: {name}\n"
		f"Type: {pattern_type}\n"
		f"Detected on: {detected_on}\n"
		f"Confidence: {confidence}\n"
		f"Entry: {entry}\n"
		f"Stop: {stop}\n"
		f"Target: {target}\n"
		f"Key levels: {key_levels}\n"
		f"Backtest: {metrics}\n"
	)


def _make_cache_key(pattern: Dict[str, Any], backtest: Optional[Dict[str, Any]]) -> Tuple[str, ...]:
	pattern_key = (
		str(pattern.get("pattern_type")),
		str(pattern.get("detected_on")),
		str(pattern.get("entry_price")),
		str(pattern.get("stop_loss")),
		str(pattern.get("target_price")),
	)
	backtest_key = ()
	if backtest:
		backtest_key = (
			str(backtest.get("sample_count")),
			str(backtest.get("win_rate")),
			str(backtest.get("median_return_pct")),
			str(backtest.get("note")),
		)
	return pattern_key + backtest_key


def generate_explanation(pattern: Dict[str, Any], backtest: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
	cache_key = _make_cache_key(pattern, backtest)
	cached = _EXPLAIN_CACHE.get(cache_key)
	if cached and time.time() - cached["ts"] < _EXPLAIN_RATE_LIMIT_SECONDS:
		return {"text": cached["text"], "source": cached["source"]}

	groq_key = (os.getenv("GROQ_API_KEY") or "").strip()
	groq_model = (os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile").strip()
	if groq_key:
		try:
			prompt = _build_prompt(pattern, backtest)
			response = requests.post(
				"https://api.groq.com/openai/v1/chat/completions",
				headers={
					"Authorization": f"Bearer {groq_key}",
					"Content-Type": "application/json",
				},
				json={
					"model": groq_model,
					"messages": [
						{"role": "system", "content": "You are a concise market analyst."},
						{"role": "user", "content": prompt},
					],
					"temperature": 0.4,
					"max_tokens": 500,
				},
				timeout=20,
			)
			response.raise_for_status()
			data = response.json()
			text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
			if text:
				_EXPLAIN_CACHE[cache_key] = {"ts": time.time(), "text": text, "source": "groq"}
				return {"text": text, "source": "groq"}
		except Exception as exc:
			print(f"Groq explain failed: {exc}")

	api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
	if not api_key:
		text = _rule_based_explanation(pattern, backtest)
		_EXPLAIN_CACHE[cache_key] = {"ts": time.time(), "text": text, "source": "fallback"}
		return {"text": text, "source": "fallback"}

	try:
		import google.generativeai as genai

		genai.configure(api_key=api_key)
		model = genai.GenerativeModel("gemini-2.5-flash")
		prompt = _build_prompt(pattern, backtest)
		response = model.generate_content(prompt)
		text = response.text.strip() if hasattr(response, "text") else str(response)
		_EXPLAIN_CACHE[cache_key] = {"ts": time.time(), "text": text, "source": "gemini"}
		return {"text": text, "source": "gemini"}
	except Exception as exc:
		print(f"Gemini explain failed: {exc}")
		text = _rule_based_explanation(pattern, backtest)
		_EXPLAIN_CACHE[cache_key] = {"ts": time.time(), "text": text, "source": "fallback"}
		return {"text": text, "source": "fallback"}
