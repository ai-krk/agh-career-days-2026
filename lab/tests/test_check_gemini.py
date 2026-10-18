"""Offline readiness checks: no credentials and no real network client."""

from contextlib import redirect_stdout
from enum import Enum
import io
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import warnings

import check_gemini


FAKE_KEY = "fake-private-key-never-send"
RAW_ERROR = "provider diagnostics containing " + FAKE_KEY
MODEL = "gemini-3.5-flash-lite"


def response(*parts, finish="STOP"):
    return SimpleNamespace(candidates=[SimpleNamespace(
        finish_reason=finish,
        content=SimpleNamespace(parts=list(parts)),
    )])


def text_part(text="OK", thought=False):
    return SimpleNamespace(text=text, thought=thought)


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        self.sdk = SimpleNamespace(Client=Mock(return_value=self.client))

    def run_probe(self, reply=None, error=None):
        self.client.models.generate_content.return_value = reply
        self.client.models.generate_content.side_effect = error
        captured = io.StringIO()
        with redirect_stdout(captured):
            result = check_gemini.probe(self.sdk, MODEL, FAKE_KEY)
            check_gemini.show_result(*result)
        self.assertNotIn(FAKE_KEY, captured.getvalue())
        self.assertNotIn(RAW_ERROR, captured.getvalue())
        return result

    def test_success_requires_one_completed_request_and_closes_client(self):
        self.assertEqual(self.run_probe(response(text_part())), ("PASSED", "ok"))
        self.sdk.Client.assert_called_once_with(
            api_key=FAKE_KEY, vertexai=False,
            http_options={"timeout": 30_000, "retry_options": {"attempts": 1}},
        )
        self.client.models.generate_content.assert_called_once()
        request = self.client.models.generate_content.call_args.kwargs
        self.assertEqual(request["model"], MODEL)
        self.assertNotIn(FAKE_KEY, str(request))
        self.client.close.assert_called_once_with()

    def test_finish_reason_enum_and_final_non_thought_text_are_accepted(self):
        class FinishReason(Enum):
            STOP = "STOP"

        reply = response(text_part("internal", thought=True), text_part("OK"),
                         finish=FinishReason.STOP)
        self.assertEqual(self.run_probe(reply), ("PASSED", "ok"))

    def test_missing_blocked_partial_or_thought_only_responses_fail(self):
        replies = {
            "no response": None,
            "no candidates attribute": SimpleNamespace(),
            "no candidates": SimpleNamespace(candidates=[]),
            "blocked": SimpleNamespace(candidates=[], prompt_feedback="SAFETY"),
            "multiple candidates": SimpleNamespace(candidates=[
                response(text_part()).candidates[0], response(text_part()).candidates[0],
            ]),
            "missing content": SimpleNamespace(candidates=[SimpleNamespace(finish_reason="STOP")]),
            "missing parts": SimpleNamespace(candidates=[SimpleNamespace(
                finish_reason="STOP", content=SimpleNamespace(),
            )]),
            "no parts": response(),
            "no text": response(SimpleNamespace()),
            "empty text": response(text_part("")),
            "whitespace": response(text_part(" \n\t")),
            "nonstring text": response(text_part(123)),
            "thought only": response(text_part(thought=True)),
            "partial answer": response(text_part(), finish="MAX_TOKENS"),
            "safety finish": response(text_part(), finish="SAFETY"),
            "missing finish": response(text_part(), finish=None),
        }
        for name, reply in replies.items():
            with self.subTest(name=name):
                self.client.reset_mock()
                self.assertEqual(self.run_probe(reply), ("FAILED", "no_text_response"))
                self.client.models.generate_content.assert_called_once()
                self.client.close.assert_called_once_with()

    def test_provider_statuses_are_sanitized_and_never_retried(self):
        statuses = {
            400: "request_rejected", 401: "access_denied", 402: "billing_required",
            403: "access_denied", 404: "model_unavailable", 429: "rate_limited",
            500: "service_unavailable",
        }
        for status, expected in statuses.items():
            with self.subTest(status=status):
                self.client.reset_mock()
                error = RuntimeError(RAW_ERROR)
                error.code = status
                self.assertEqual(self.run_probe(error=error), ("FAILED", expected))
                self.client.models.generate_content.assert_called_once()
                self.client.close.assert_called_once_with()

    def test_timeout_and_unknown_errors_are_sanitized(self):
        for error, expected in (
            (TimeoutError(RAW_ERROR), "timeout"),
            (RuntimeError(RAW_ERROR), "connection_or_sdk_error"),
        ):
            with self.subTest(expected=expected):
                self.client.reset_mock()
                self.assertEqual(self.run_probe(error=error), ("FAILED", expected))
                self.client.models.generate_content.assert_called_once()
                self.client.close.assert_called_once_with()

    def test_client_construction_failure_is_not_success(self):
        self.sdk.Client.side_effect = RuntimeError(RAW_ERROR)
        self.assertEqual(self.run_probe(), ("FAILED", "connection_or_sdk_error"))
        self.client.models.generate_content.assert_not_called()
        self.client.close.assert_not_called()

    def test_close_error_does_not_leak_or_replace_successful_request(self):
        self.client.close.side_effect = RuntimeError(RAW_ERROR)
        self.assertEqual(self.run_probe(response(text_part())), ("PASSED", "ok"))
        self.client.close.assert_called_once_with()


class MainTests(unittest.TestCase):
    def setUp(self):
        self.sdk = SimpleNamespace(Client=Mock())
        self.patches = [
            patch.object(check_gemini, "local_check", return_value=(self.sdk, MODEL, "ok")),
            patch("builtins.input", return_value="TAK"),
            patch.object(check_gemini, "read_key", return_value=FAKE_KEY),
            patch.object(check_gemini, "probe", return_value=("PASSED", "ok")),
        ]
        self.local, self.consent, self.read_key, self.probe = [p.start() for p in self.patches]
        for patcher in self.patches:
            self.addCleanup(patcher.stop)

    def run_main(self, argv=None):
        captured = io.StringIO()
        with redirect_stdout(captured):
            exit_code = check_gemini.main([] if argv is None else argv)
        output = captured.getvalue()
        self.assertNotIn(FAKE_KEY, output)
        self.assertNotIn(RAW_ERROR, output)
        self.sdk.Client.assert_not_called()
        return exit_code, output

    def assert_not_run(self, code, argv=None):
        exit_code, output = self.run_main(argv)
        self.assertIn("Gemini: NOT_RUN", output)
        self.assertIn("Code: " + code, output)
        self.assertNotIn("Gemini: PASSED", output)
        self.probe.assert_not_called()
        return exit_code

    def test_local_only_never_prompts_for_consent_key_or_calls_api(self):
        self.assertEqual(self.assert_not_run("local_only", ["--local-only"]), 0)
        self.consent.assert_not_called()
        self.read_key.assert_not_called()

    def test_local_failure_stops_before_consent_or_key(self):
        self.local.return_value = (None, None, "local_setup_error")
        self.assertEqual(self.assert_not_run("local_setup_error"), 1)
        self.consent.assert_not_called()
        self.read_key.assert_not_called()

    def test_missing_consent_stops_before_key_or_api(self):
        for consent in ("", "NIE", "yes"):
            with self.subTest(consent=consent):
                self.consent.return_value = consent
                self.assertEqual(self.assert_not_run("not_confirmed"), 1)
                self.read_key.assert_not_called()

    def test_hidden_input_warning_stops_before_api(self):
        self.read_key.side_effect = check_gemini.GetPassWarning(RAW_ERROR)
        self.assertEqual(self.assert_not_run("hidden_input_unavailable"), 1)

    def test_invalid_keys_never_call_api(self):
        for key in ("", " ", "key with whitespace", "x" * 513):
            with self.subTest(key_length=len(key)):
                self.read_key.return_value = key
                self.assertEqual(self.assert_not_run("invalid_key_input"), 1)

    def test_cancelled_input_never_calls_api(self):
        for error in (EOFError(RAW_ERROR), KeyboardInterrupt()):
            with self.subTest(error_type=type(error).__name__):
                self.read_key.side_effect = error
                self.assertEqual(self.assert_not_run("cancelled"), 1)

    def test_success_follows_probe_result(self):
        exit_code, output = self.run_main()
        self.assertEqual(exit_code, 0)
        self.assertIn("Gemini: PASSED", output)
        self.probe.assert_called_once_with(self.sdk, MODEL, FAKE_KEY)

    def test_failed_probe_is_not_reported_as_ready(self):
        self.probe.return_value = ("FAILED", "rate_limited")
        exit_code, output = self.run_main()
        self.assertEqual(exit_code, 1)
        self.assertIn("Gemini: FAILED", output)
        self.assertIn("Code: rate_limited", output)
        self.assertNotIn("Polaczenie dziala", output)
        self.probe.assert_called_once_with(self.sdk, MODEL, FAKE_KEY)


class HiddenInputTests(unittest.TestCase):
    def test_getpass_warning_raises_before_echo_fallback(self):
        fallback = Mock()

        def unavailable_hidden_input(prompt):
            warnings.warn(RAW_ERROR, check_gemini.GetPassWarning)
            fallback()
            return FAKE_KEY

        with patch.object(check_gemini, "getpass", side_effect=unavailable_hidden_input):
            with self.assertRaises(check_gemini.GetPassWarning):
                check_gemini.read_key()
        fallback.assert_not_called()

    def test_key_is_read_only_through_getpass_and_trimmed(self):
        with patch.object(check_gemini, "getpass", return_value="  " + FAKE_KEY + "  ") as hidden:
            self.assertEqual(check_gemini.read_key(), FAKE_KEY)
        hidden.assert_called_once()


if __name__ == "__main__":
    unittest.main()
