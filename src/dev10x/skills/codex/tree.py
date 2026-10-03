from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath


@dataclass(frozen=True)
class GeneratedTree:
    output: PurePosixPath
    files: dict[PurePosixPath, str]
    warnings: list[str] = field(default_factory=list)


def is_hidden(relative: PurePosixPath) -> bool:
    return any(part.startswith(".") for part in relative.parts)


def read_tree(root: Path, output: PurePosixPath) -> dict[PurePosixPath, str]:
    output_root = root / output
    if not output_root.is_dir():
        return {}
    tree: dict[PurePosixPath, str] = {}
    for path in sorted(output_root.rglob("*")):
        relative = PurePosixPath(path.relative_to(output_root).as_posix())
        if path.is_file() and not is_hidden(relative):
            tree[output / relative] = path.read_text(encoding="utf-8")
    return tree


def write_tree(root: Path, tree: GeneratedTree) -> Path:
    output = root / tree.output
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        for relative, content in sorted(tree.files.items()):
            destination = staging / relative.relative_to(tree.output)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    staging.chmod(0o755)
    if output.exists():
        shutil.rmtree(output)
    staging.rename(output)
    return output


def stale_paths(root: Path, tree: GeneratedTree) -> list[PurePosixPath]:
    current = read_tree(root, tree.output)
    return sorted(
        path
        for path in current.keys() | tree.files.keys()
        if current.get(path) != tree.files.get(path)
    )
