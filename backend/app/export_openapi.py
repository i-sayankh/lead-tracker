"""Write the OpenAPI spec to backend/openapi.json. Run: `uv run python -m app.export_openapi`."""

import json
from pathlib import Path

from app.main import app

OUTPUT = Path(__file__).resolve().parent.parent / "openapi.json"


def main() -> None:
    spec = app.openapi()
    text = json.dumps(spec, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    # Force LF so the file is byte-identical on Windows and in CI (drift check).
    OUTPUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
