"""Run the server-side diagnostic pipeline manually without a web route."""

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.ai import AISettings, generate_diagnostic_check


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Generate one Growup classroom diagnostic check.")
    parser.add_argument("--mode", choices=["deterministic", "llm", "hybrid"], default=None)
    parser.add_argument("--provider", choices=["openai", "gemini", "nvidia"], default=None)
    parser.add_argument("--title", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--source-id", required=True)
    args = parser.parse_args()
    settings = AISettings.from_env()
    settings = replace(settings, mode=args.mode or settings.mode, provider=args.provider or settings.provider)
    result = generate_diagnostic_check(teaching_context={"title": args.title, "text": args.text, "sourceId": args.source_id}, settings=settings)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
