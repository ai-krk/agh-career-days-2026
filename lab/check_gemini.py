"""One-request readiness check. No key in code, files, output or exceptions."""
import argparse
from getpass import GetPassWarning, getpass
import importlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sys
import warnings


EXPECTED_SDK = "2.28.0"


def local_check():
    """Check the actual workshop folder and interpreter before asking for a key."""
    if sys.version_info < (3, 11):
        return None, None, "python_too_old"
    try:
        folder = Path(__file__).resolve().parent
        for name in ("01_Agent_Gemini.ipynb", "cases.json"):
            json.loads((folder / name).read_text(encoding="utf-8"))
        for module in ("jupyterlab", "ipykernel", "lab_runtime", "live_lab",
                       "investigation", "challenge_lab", "gemini_provider"):
            importlib.import_module(module)
        from google import genai
        from gemini_provider import DEFAULT_MODEL
        if version("google-genai") != EXPECTED_SDK:
            return None, DEFAULT_MODEL, "sdk_version_mismatch"
        return genai, DEFAULT_MODEL, "ok"
    except Exception:
        return None, None, "local_setup_error"


def read_key():
    # If hidden input is unavailable, stop before getpass can fall back to echo.
    with warnings.catch_warnings():
        warnings.simplefilter("error", GetPassWarning)
        return getpass("Wklej klucz API (znaki sa ukryte) i nacisnij Enter: ").strip()


def probe(genai, model, api_key):
    """At most one request, with no retries; do not expose provider diagnostics."""
    client = None
    try:
        client = genai.Client(api_key=api_key, vertexai=False, http_options={
            "timeout": 30_000,
            "retry_options": {"attempts": 1},
        })
        response = client.models.generate_content(
            model=model,
            contents="Reply with exactly: OK",
            config={
                "automatic_function_calling": {"disable": True},
                "max_output_tokens": 512,
                "thinking_config": {"thinking_level": "LOW", "include_thoughts": False},
            },
        )
        blocked = getattr(getattr(response, "prompt_feedback", None), "block_reason", None)
        if getattr(blocked, "value", blocked) not in (None, "", "BLOCK_REASON_UNSPECIFIED"):
            return "FAILED", "no_text_response"
        candidates = getattr(response, "candidates", None) or []
        if len(candidates) == 1:
            candidate = candidates[0]
            reason = getattr(candidate, "finish_reason", None)
            reason = getattr(reason, "value", reason)
            parts = getattr(getattr(candidate, "content", None), "parts", None) or []
            if reason == "STOP" and any(
                isinstance(getattr(part, "text", None), str)
                and part.text.strip()
                and not getattr(part, "thought", False)
                for part in parts
            ):
                return "PASSED", "ok"
        return "FAILED", "no_text_response"
    except Exception as error:
        from gemini_provider import _error_code
        if getattr(error, "code", None) == 402:
            return "FAILED", "billing_required"
        return "FAILED", _error_code(error)
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass


def show_result(status, code):
    print(f"Gemini: {status}")
    print(f"Code: {code}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="AGH: local setup and one Gemini request.")
    parser.add_argument("--local-only", action="store_true",
                        help="Check local setup only. No key and no API call.")
    args = parser.parse_args(argv)
    print(f"System: {platform.system()}")
    print(f"Python: {platform.python_version()}")
    genai, model, code = local_check()
    print(f"Model: {model or 'not_checked'}")
    print(f"Local: {'PASSED' if code == 'ok' else 'FAILED'}")
    if code != "ok":
        show_result("NOT_RUN", code)
        print("Sprawdz krok 4 w 02_Przygotowanie.md. Nie wysylaj klucza.")
        return 1
    if args.local_only:
        show_result("NOT_RUN", "local_only")
        return 0

    print("\nTest wysle jedno krotkie zadanie do Gemini. Nie sprawdza planu rozliczen.")
    print("Nie wlaczaj platnosci. Uzyj tylko projektu, do ktorego masz prawo.")
    request_started = False
    try:
        consent = input("Znasz i akceptujesz zasady dostepu/rozliczenia projektu? Wpisz TAK: ")
        if consent.strip().upper() != "TAK":
            show_result("NOT_RUN", "not_confirmed")
            return 1
        key = read_key()
        if not key or len(key) > 512 or any(ch.isspace() for ch in key):
            show_result("NOT_RUN", "invalid_key_input")
            return 1
        print("Laczenie... (limit czasu zadania: 30 sekund)")
        try:
            request_started = True
            status, code = probe(genai, model, key)
        finally:
            key = None
        show_result(status, code)
        if status == "PASSED":
            print("Polaczenie dziala. Teraz otworz notebook zgodnie z krokiem 6.")
        else:
            print("Sprawdz tabele pomocy w instrukcji. Nie powtarzaj testu w petli.")
        return 0 if status == "PASSED" else 1
    except GetPassWarning:
        show_result("NOT_RUN", "hidden_input_unavailable")
        return 1
    except (EOFError, KeyboardInterrupt):
        print()
        show_result("INCOMPLETE" if request_started else "NOT_RUN",
                    "interrupted_request" if request_started else "cancelled")
        return 1
    except OSError:
        show_result("NOT_RUN", "hidden_input_unavailable")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
