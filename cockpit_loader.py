"""Safe loader for cockpit_core submodule across local and Streamlit Cloud deployments."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

_COCKPIT_REPO = "https://github.com/shin7965977/lakehouse-cockpit-core.git"


def ensure_cockpit_core_on_path() -> None:
    """Ensure a populated cockpit_core submodule is importable even if uninitialized on Cloud."""
    repo_root = Path(__file__).resolve().parent
    local_target = repo_root / "cockpit_core" / "components" / "text_to_chart.py"
    if local_target.exists():
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        return

    cache_root = Path(tempfile.gettempdir()) / "cockpit_core_cache"
    cached_pkg = cache_root / "cockpit_core"
    if not (cached_pkg / "components" / "text_to_chart.py").exists():
        cache_root.mkdir(parents=True, exist_ok=True)
        if not cached_pkg.exists():
            subprocess.run(
                ["git", "clone", "--depth", "1", _COCKPIT_REPO, str(cached_pkg)],
                check=True,
                capture_output=True,
                text=True,
            )

    if str(cache_root) not in sys.path:
        sys.path.insert(0, str(cache_root))

    # Clear any empty namespace package cached from an uninitialized submodule dir
    for mod_name in list(sys.modules):
        if mod_name == "cockpit_core" or mod_name.startswith("cockpit_core."):
            sys.modules.pop(mod_name, None)


def load_ai_chart_engine() -> tuple[Any, Any]:
    """Return `(generate_ai_chart_config, render_ai_dynamic_chart)` from `cockpit_core`."""
    ensure_cockpit_core_on_path()
    from cockpit_core.components.text_to_chart import (
        generate_ai_chart_config,
        render_ai_dynamic_chart,
    )

    return generate_ai_chart_config, render_ai_dynamic_chart


def load_interactive_nl2chart_studio() -> Any:
    """Return fragment-isolated 2-step HITL NL2Chart Studio from `cockpit_core`."""
    ensure_cockpit_core_on_path()
    from cockpit_core.components.text_to_chart import render_interactive_nl2chart_studio

    return render_interactive_nl2chart_studio
