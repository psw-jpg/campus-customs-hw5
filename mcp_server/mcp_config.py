"""Load .mcp.json with paths relative to the project folder.

.mcp.json stores the server command as relative paths (.venv/bin/python,
mcp_server/server.py) so the repo works wherever it is cloned. This turns them
into absolute paths for the project the file lives in.
"""

import json
from pathlib import Path


def load_mcp_config(project: Path) -> dict:
    config = json.loads((project / ".mcp.json").read_text())
    for server in config["mcpServers"].values():
        cmd = Path(server["command"])
        if not cmd.is_absolute() and (project / cmd).exists():
            server["command"] = str(project / cmd)
        server["args"] = [str(project / a) if not Path(a).is_absolute() and (project / a).exists() else a
                          for a in server.get("args", [])]
        server.setdefault("cwd", str(project))
    return config
