import sys
import threading
import time
import webbrowser
from pathlib import Path


def open_browser_later(url: str, delay_seconds: float = 1.5) -> None:
    def _open() -> None:
        time.sleep(delay_seconds)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    threading.Thread(target=_open, daemon=True).start()


def main() -> None:
    from streamlit.web import cli as stcli

    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    app_path = base_dir / "app.py"

    if not app_path.exists():
        print(f"[ERROR] app.py not found at: {app_path}")
        sys.exit(1)

    open_browser_later("http://localhost:8501")

    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]
    stcli.main()


if __name__ == "__main__":
    main()
