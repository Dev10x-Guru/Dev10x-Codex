from __future__ import annotations

import pytest

from dev10x.hooks.apply_patch_payload import (
    MalformedPatchError,
    PatchOperation,
    PatchOperationKind,
    parse_apply_patch,
    to_edit_write_payloads,
)


def _patch(*body: str) -> str:
    return "\n".join(["*** Begin Patch", *body, "*** End Patch"])


class TestParseApplyPatch:
    def test_add_file_collects_added_lines_as_content(self) -> None:
        ops = parse_apply_patch(_patch("*** Add File: src/new.py", "+import os", "+x = 1"))

        assert ops == (
            PatchOperation(
                kind=PatchOperationKind.ADD,
                path="src/new.py",
                added_lines=("import os", "x = 1"),
            ),
        )
        assert ops[0].content == "import os\nx = 1"

    def test_update_file_keeps_only_added_lines_across_hunks(self) -> None:
        ops = parse_apply_patch(
            _patch(
                "*** Update File: app.py",
                "@@ def f():",
                "-    pass",
                "+    return 1",
                " context",
                "@@",
                "+tail = True",
                "*** End of File",
            )
        )

        assert ops == (
            PatchOperation(
                kind=PatchOperationKind.UPDATE,
                path="app.py",
                added_lines=("    return 1", "tail = True"),
            ),
        )

    def test_update_without_hunk_header_is_accepted(self) -> None:
        ops = parse_apply_patch(_patch("*** Update File: a.py", " import foo", "+bar"))

        assert ops[0].added_lines == ("bar",)

    def test_delete_file_has_no_content(self) -> None:
        ops = parse_apply_patch(_patch("*** Delete File: old.txt"))

        assert ops == (PatchOperation(kind=PatchOperationKind.DELETE, path="old.txt"),)

    def test_move_records_destination_and_touches_both_paths(self) -> None:
        ops = parse_apply_patch(
            _patch(
                "*** Update File: a/old.py",
                "*** Move to: a/new.py",
                "@@",
                "-x",
                "+y",
            )
        )

        assert ops[0].move_to == "a/new.py"
        assert ops[0].touched_paths() == ("a/old.py", "a/new.py")

    def test_multi_file_patch_preserves_order(self) -> None:
        ops = parse_apply_patch(
            _patch(
                "*** Add File: one.txt",
                "+1",
                "*** Delete File: two.txt",
                "*** Update File: three.txt",
                "@@",
                "+3",
            )
        )

        assert [(op.kind, op.path) for op in ops] == [
            (PatchOperationKind.ADD, "one.txt"),
            (PatchOperationKind.DELETE, "two.txt"),
            (PatchOperationKind.UPDATE, "three.txt"),
        ]

    def test_heredoc_wrapped_patch_is_unwrapped(self) -> None:
        text = "<<'EOF'\n" + _patch("*** Add File: f.txt", "+hi") + "\nEOF\n"

        assert parse_apply_patch(text)[0].path == "f.txt"

    def test_environment_id_preamble_is_skipped(self) -> None:
        ops = parse_apply_patch(
            _patch("*** Environment ID: remote", "*** Add File: hello.txt", "+hello")
        )

        assert ops[0].path == "hello.txt"

    def test_marker_whitespace_is_tolerated(self) -> None:
        text = "  *** Begin Patch \n*** Add File: f.txt\n+hi\n *** End Patch  "

        assert parse_apply_patch(text)[0].path == "f.txt"

    def test_empty_patch_yields_no_operations(self) -> None:
        assert parse_apply_patch(_patch()) == ()

    @pytest.mark.parametrize(
        "text",
        [
            "",
            "not a patch",
            "*** Begin Patch\n*** Add File: f.txt\n+hi",
            _patch("*** Add File: f.txt", "no plus prefix"),
            _patch("*** Update File: empty.py"),
            _patch("*** Delete File: gone.txt", "+unexpected"),
            _patch("stray line"),
            _patch("*** Add File: "),
            _patch("*** Update File: a.py", "@@", "?bogus"),
        ],
        ids=[
            "empty",
            "no-markers",
            "missing-end",
            "add-line-without-plus",
            "empty-update",
            "content-after-delete",
            "line-outside-hunk",
            "empty-path",
            "unknown-update-line",
        ],
    )
    def test_malformed_patch_raises(self, text: str) -> None:
        with pytest.raises(MalformedPatchError):
            parse_apply_patch(text)


class TestToEditWritePayloads:
    def test_add_becomes_write_with_absolute_path_and_content(self) -> None:
        data = {
            "tool_name": "apply_patch",
            "tool_input": {"command": _patch("*** Add File: src/new.py", "+x = 1")},
            "cwd": "/work/repo",
            "session_id": "s1",
        }

        payloads = to_edit_write_payloads(data=data, cwd="/work/repo")

        assert payloads == [
            {
                "tool_name": "Write",
                "tool_input": {"file_path": "/work/repo/src/new.py", "content": "x = 1"},
                "cwd": "/work/repo",
                "session_id": "s1",
            }
        ]

    def test_update_becomes_edit_with_added_lines_as_new_string(self) -> None:
        data = {
            "tool_name": "apply_patch",
            "tool_input": {"command": _patch("*** Update File: a.py", "@@", "-x", "+y")},
        }

        payloads = to_edit_write_payloads(data=data, cwd="/w")

        assert payloads == [
            {
                "tool_name": "Edit",
                "tool_input": {"file_path": "/w/a.py", "new_string": "y"},
            }
        ]

    def test_absolute_paths_are_kept(self) -> None:
        data = {"tool_input": {"command": _patch("*** Delete File: /etc/app/.env")}}

        payloads = to_edit_write_payloads(data=data, cwd="/w")

        assert payloads[0]["tool_input"] == {"file_path": "/etc/app/.env", "new_string": ""}

    def test_move_checks_source_as_edit_and_destination_as_write(self) -> None:
        data = {
            "tool_input": {
                "command": _patch("*** Update File: a.py", "*** Move to: b.py", "@@", "+z")
            }
        }

        payloads = to_edit_write_payloads(data=data, cwd="/w")

        assert [(p["tool_name"], p["tool_input"]["file_path"]) for p in payloads] == [
            ("Edit", "/w/a.py"),
            ("Write", "/w/b.py"),
        ]

    def test_missing_command_is_malformed(self) -> None:
        with pytest.raises(MalformedPatchError):
            to_edit_write_payloads(data={"tool_input": {}}, cwd="/w")

    def test_non_dict_tool_input_is_malformed(self) -> None:
        with pytest.raises(MalformedPatchError):
            to_edit_write_payloads(data={"tool_input": "oops"}, cwd="/w")
