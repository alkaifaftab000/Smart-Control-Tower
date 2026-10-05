"""Quick local and optional live smoke checks for the AI pilot.

Run local routing checks with: python test_ai_pilot.py
Run tiny provider checks after rotating/configuring keys with: python test_ai_pilot.py --live
"""

from __future__ import annotations

import argparse
import os
import re
import unittest
from unittest.mock import patch

import ai_local_server as ai


MESSAGES = [{"role": "user", "content": "Reply with OK."}]


def safe_error_detail(message: str) -> str:
    """Show useful provider diagnostics without exposing key-shaped strings."""
    detail = " ".join(str(message).split())
    detail = re.sub(r"(?i)\bbearer\s+\S+", "Bearer [redacted]", detail)
    detail = re.sub(r"\b(?:gsk_[A-Za-z0-9_-]+|sk-[A-Za-z0-9_-]+|xai-[A-Za-z0-9_-]+)\b", "[redacted key]", detail)
    return detail[:240] or "No additional error detail returned."


class RoutingTests(unittest.TestCase):
    def test_missing_openai_key_uses_mistral(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "", "MISTRAL_API_KEY": "test"}):
            with patch.object(ai, "ask_mistral", return_value=("OK", "test-model")) as mistral:
                result = ai.handle_question(MESSAGES)
        self.assertEqual(result["provider"], "mistral")
        self.assertTrue(result["fallback"])
        self.assertIn("not configured", result["fallbackReason"])
        mistral.assert_called_once_with(MESSAGES)

    def test_openai_rate_limit_uses_mistral(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "MISTRAL_API_KEY": "test"}):
            with patch.object(ai, "ask_openai", side_effect=ai.ProviderError(429, "rate limited")):
                with patch.object(ai, "ask_mistral", return_value=("OK", "test-model")) as mistral:
                    result = ai.handle_question(MESSAGES)
        self.assertEqual(result["provider"], "mistral")
        self.assertTrue(result["fallback"])
        self.assertEqual(result["fallbackReason"], "OpenAI rate limit")
        mistral.assert_called_once_with(MESSAGES)

    def test_no_keys_returns_clear_configuration_error(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "", "MISTRAL_API_KEY": "", "GROQ_API_KEY": ""}):
            with self.assertRaises(ai.ProviderError) as caught:
                ai.handle_question(MESSAGES)
        self.assertEqual(caught.exception.status, 503)

    def test_missing_primary_and_mistral_uses_groq(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "", "MISTRAL_API_KEY": "", "GROQ_API_KEY": "test"}):
            with patch.object(ai, "ask_groq", return_value=("OK", "test-model")) as groq:
                result = ai.handle_question(MESSAGES)
        self.assertEqual(result["provider"], "groq")
        self.assertTrue(result["fallback"])
        self.assertIn("not configured", result["fallbackReason"])
        groq.assert_called_once_with(MESSAGES)

    def test_mistral_rate_limit_falls_through_to_groq(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "", "MISTRAL_API_KEY": "test", "GROQ_API_KEY": "test"}):
            with patch.object(ai, "ask_mistral", side_effect=ai.ProviderError(429, "rate limited")):
                with patch.object(ai, "ask_groq", return_value=("OK", "test-model")) as groq:
                    result = ai.handle_question(MESSAGES)
        self.assertEqual(result["provider"], "groq")
        self.assertTrue(result["fallback"])
        self.assertIn("Mistral rate limit", result["fallbackReason"])
        groq.assert_called_once_with(MESSAGES)


def live_checks(provider_filter: str) -> bool:
    ai.load_env_file()
    configured = {
        "OpenAI": bool(ai.key_for("OPENAI_API_KEY")),
        "Mistral": bool(ai.key_for("MISTRAL_API_KEY")),
        "Groq": bool(ai.key_for("GROQ_API_KEY")),
    }
    if not any(configured.values()):
        print("LIVE CHECK: skipped (no provider keys configured).")
        return True

    passed = True
    for label, enabled, call in (
        ("OpenAI", configured["OpenAI"], ai.ask_openai),
        ("Mistral", configured["Mistral"], ai.ask_mistral),
        ("Groq", configured["Groq"], ai.ask_groq),
    ):
        if provider_filter != "both" and label.lower() != provider_filter:
            continue
        if not enabled:
            print(f"{label}: skipped (key not configured).")
            continue
        try:
            answer, model = call(MESSAGES)
            if not answer.strip():
                raise ValueError("empty answer")
            print(f"{label}: PASS (model {model}; received a non-empty response).")
        except ai.ProviderError as error:
            print(f"{label}: FAIL (HTTP {error.status}; {safe_error_detail(error.message)})")
            passed = False
        except Exception:
            print(f"{label}: FAIL (unexpected error; details hidden).")
            passed = False
    return passed


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the local AI pilot.")
    parser.add_argument("--live", action="store_true", help="send one tiny request to each configured provider")
    parser.add_argument("--provider", choices=("both", "openai", "mistral", "groq"), default="both", help="limit the live check to one provider")
    args = parser.parse_args()

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RoutingTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.wasSuccessful()
    if args.live:
        passed = live_checks(args.provider) and passed
    else:
        print("Live API check not run. Use --live to send one small request per configured provider.")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
