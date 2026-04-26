import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
servers_dir = repo_root / "servers"
sys.path.insert(0, str(servers_dir / "lib"))
sys.path.insert(0, str(servers_dir))
