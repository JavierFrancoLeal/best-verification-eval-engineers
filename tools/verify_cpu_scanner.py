#!/usr/bin/env python3
"""Tier A deterministic CPU verification pre-scanner for best-verification-eval-engineers.

ECOSYSTEM_CONTRACT v1.2.0 | suite_id: verification-eval
Constraints:
  - Python 3.9+ standard library ONLY (zero network imports).
  - Exact 7 canonical Tier A rules in RULE_META (HR-2).
  - Disjoint files_scanned / files_skipped telemetry in JSON and SARIF 2.1.0 (HR-6).
  - Exit codes: 0 = clean, 1 = MAJOR findings only, 2 = BLOCKER findings present.
"""
from __future__ import annotations

import argparse
import ast
import dataclasses
import hashlib
import json
import os
import pathlib
import re
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple

SCANNER_NAME = "verify_cpu_scanner"
SCANNER_VERSION = "1.2.0"
SARIF_SCHEMA_URI = (
    "https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/os/schemas/sarif-schema-2.1.0.json"
)
MAX_FILE_BYTES_DEFAULT = 1_048_576  # 1 MiB
MAX_SKIP_SAMPLES = 20

# Single source of truth validated bijectively against modules/*/VERIFY.md by validators/validate_repo.py
RULE_META: Dict[str, Dict[str, Any]] = {
    "VER-TAU-NOASSERT-001": {
        "canonical_id": "verification-eval:assertion-mutation-strength:VER-TAU-NOASSERT-001",
        "module_id": "assertion-mutation-strength",
        "severity": "BLOCKER",
        "sarif_level": "error",
        "short_description": "Assertion-free test function provides no executable oracle.",
    },
    "VER-TAU-CONST-001": {
        "canonical_id": "verification-eval:assertion-mutation-strength:VER-TAU-CONST-001",
        "module_id": "assertion-mutation-strength",
        "severity": "BLOCKER",
        "sarif_level": "error",
        "short_description": "Tautological or constant-true assertion cannot detect faults.",
    },
    "VER-TAU-SWALLOW-001": {
        "canonical_id": "verification-eval:assertion-mutation-strength:VER-TAU-SWALLOW-001",
        "module_id": "assertion-mutation-strength",
        "severity": "BLOCKER",
        "sarif_level": "error",
        "short_description": "Exception-swallowing handler inside test masks failures.",
    },
    "VER-FLK-NONDET-001": {
        "canonical_id": "verification-eval:determinism-flakiness-isolation:VER-FLK-NONDET-001",
        "module_id": "determinism-flakiness-isolation",
        "severity": "MAJOR",
        "sarif_level": "warning",
        "short_description": "Non-deterministic sleep or unseeded randomness hazard inside test.",
    },
    "VER-GOV-SKIP-001": {
        "canonical_id": "verification-eval:anti-tampering-eval-governance:VER-GOV-SKIP-001",
        "module_id": "anti-tampering-eval-governance",
        "severity": "MAJOR",
        "sarif_level": "warning",
        "short_description": "Silenced/skipped test or continue-on-error bypass lacks tracked issue and expiry.",
    },
    "VER-GOV-TAMPER-001": {
        "canonical_id": "verification-eval:anti-tampering-eval-governance:VER-GOV-TAMPER-001",
        "module_id": "anti-tampering-eval-governance",
        "severity": "BLOCKER",
        "sarif_level": "error",
        "short_description": "Test runner, coverage/mutation threshold, Clean-Room read-only posture, or exit tampering detected.",
    },
    "VER-EVAL-UNCAL-001": {
        "canonical_id": "verification-eval:llm-rag-evalops-calibration:VER-EVAL-UNCAL-001",
        "module_id": "llm-rag-evalops-calibration",
        "severity": "MAJOR",
        "sarif_level": "warning",
        "short_description": "Uncalibrated accuracy/precision claim missing holdout CI metadata.",
    },
}

SKIP_DIRS: Set[str] = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache",
    ".pytest_cache", "dist", "build", "target", ".tox", "mutants", ".next",
}
ISSUE_TICKET_RE = re.compile(r"(?:^|[^A-Za-z0-9_])([A-Z]{2,10}-\d+|#\d+)\b")
ISO_DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")

FORBIDDEN_AUDITOR_WRITE_TOOLS = {
    "write", "edit", "write_file", "edit_file", "write_to_file",
    "replace_file_content", "multi_replace_file_content", "apply_patch", "bash",
}

CLIKES_TOKEN_RE = re.compile(
    r"""
      (?P<BLOCK_COMMENT>/\*[\s\S]*?\*/)
    | (?P<LINE_COMMENT>//[^\n]*)
    | (?P<TEMPLATE>`(?:\\[\s\S]|[^`\\])*`)
    | (?P<DSTRING>"(?:\\.|[^"\\\n])*")
    | (?P<SSTRING>'(?:\\.|[^'\\\n])*')
    | (?P<IDENT>[A-Za-z_$][A-Za-z0-9_$]*)
    | (?P<NUMBER>\d+(?:\.\d+)?)
    | (?P<PUNCT>[(){}\[\].,;:=!?<>+\-/*&|])
    | (?P<NEWLINE>\n)
    """,
    re.VERBOSE,
)

TEST_GATE_CMD_RE = re.compile(
    r"\b(?:pytest|vitest|jest|go\s+test|npm\s+(?:run\s+)?test|pnpm\s+test|yarn\s+test|"
    r"node\s+--test|unittest|coverage|mutmut|stryker|gremlins|"
    r"check\.(?:sh|ps1)|(?:test|verify|eval)[-_][a-z0-9_-]+)\b",
    re.IGNORECASE,
)

TAMPER_CLI_PATTERNS = [
    (re.compile(r"--pass-?with-?no-?tests\b(?!\s*=\s*false)", re.IGNORECASE), "--passWithNoTests enabled"),
    (re.compile(r"\bpytest\b[^\n]*--no-cov\b"), "pytest --no-cov bypass"),
    (re.compile(r"--cov-fail-under(?:=|\s+)0(?:\.0+)?\b"), "--cov-fail-under=0 threshold bypass"),
    (re.compile(r"--coverage(?:=|\s+)false\b"), "coverage disabled via CLI flag"),
]

SHELL_EXIT_MASK_RE = re.compile(r"\|\|\s*true\b|;\s*true\b")

MASS_PRAGMA_RE = re.compile(
    r"(pragma:\s*no\s+(?:cover|mutate)|istanbul\s+ignore\s+file|c8\s+ignore\s+start|LCOV_EXCL_START)",
    re.IGNORECASE,
)

UNCALIBRATED_CLAIM_RE = re.compile(
    r"\b(?:production\s+accuracy|verified\s+\d{2,3}%\s+(?:production\s+)?accuracy|"
    r"100%\s+production\s+(?:accuracy|precision|recall)|guaranteed\s+accuracy)\b",
    re.IGNORECASE,
)
CALIBRATION_GUARD_RE = re.compile(
    r"\b(?:wilson|rogan_gladen|ci_95|confidence_interval|holdout_n_pos|youden_j|production_claim_prohibited)\b",
    re.IGNORECASE,
)


@dataclasses.dataclass(frozen=True)
class Finding:
    rule_id: str
    file_path: str
    line: int
    column: int
    message: str
    symbol: str = ""

    def fingerprint(self) -> str:
        raw = f"{self.rule_id}|{self.file_path}|{self.line}|{self.symbol}|{self.message}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


@dataclasses.dataclass
class SkipTelemetry:
    oversized_count: int = 0
    binary_or_decode_count: int = 0
    os_error_count: int = 0
    python_syntax_error_count: int = 0
    oversized_samples: List[str] = dataclasses.field(default_factory=list)
    binary_or_decode_samples: List[str] = dataclasses.field(default_factory=list)
    os_error_samples: List[str] = dataclasses.field(default_factory=list)
    python_syntax_error_samples: List[str] = dataclasses.field(default_factory=list)

    def record(self, bucket: str, rel_path: str) -> None:
        count_attr = f"{bucket}_count"
        samples_attr = f"{bucket}_samples"
        setattr(self, count_attr, getattr(self, count_attr) + 1)
        samples: List[str] = getattr(self, samples_attr)
        if len(samples) < MAX_SKIP_SAMPLES:
            samples.append(rel_path)

    @property
    def total(self) -> int:
        return (
            self.oversized_count
            + self.binary_or_decode_count
            + self.os_error_count
            + self.python_syntax_error_count
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "oversized_count": self.oversized_count,
            "oversized_sample": sorted(self.oversized_samples)[:MAX_SKIP_SAMPLES],
            "binary_or_decode_count": self.binary_or_decode_count,
            "binary_or_decode_sample": sorted(self.binary_or_decode_samples)[:MAX_SKIP_SAMPLES],
            "os_error_count": self.os_error_count,
            "os_error_sample": sorted(self.os_error_samples)[:MAX_SKIP_SAMPLES],
            "python_syntax_error_count": self.python_syntax_error_count,
            "python_syntax_error_sample": sorted(self.python_syntax_error_samples)[:MAX_SKIP_SAMPLES],
        }


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def _is_pure_expr(node: ast.AST) -> bool:
    if isinstance(node, (ast.Name, ast.Constant)):
        return True
    if isinstance(node, ast.Attribute):
        return _is_pure_expr(node.value)
    if isinstance(node, ast.Subscript):
        return _is_pure_expr(node.value) and _is_pure_expr(node.slice)
    return False


def _is_tautology(expr: ast.AST) -> Optional[str]:
    if isinstance(expr, ast.Constant) and bool(expr.value) is True:
        return "constant-true assertion"
    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
        if isinstance(expr.operand, ast.Constant) and bool(expr.operand.value) is False:
            return "negated constant-false assertion"
    if isinstance(expr, ast.Compare) and len(expr.ops) == 1 and len(expr.comparators) == 1:
        op, left, right = expr.ops[0], expr.left, expr.comparators[0]
        if isinstance(op, (ast.Eq, ast.Is, ast.LtE, ast.GtE)):
            if _is_pure_expr(left) and _is_pure_expr(right):
                if ast.dump(left, include_attributes=False) == ast.dump(right, include_attributes=False):
                    return "reflexive identity assertion (x == x)"
        if (
            isinstance(op, ast.GtE)
            and isinstance(left, ast.Call)
            and _call_name(left.func) == "len"
            and isinstance(right, ast.Constant)
            and right.value == 0
        ):
            return "tautological len(x) >= 0 assertion"
    return None


def _has_tracked_skip_reason(text: str) -> bool:
    return bool(ISSUE_TICKET_RE.search(text) and ISO_DATE_RE.search(text))


def _decorator_reason_text(dec: ast.AST) -> str:
    parts: List[str] = []
    for node in ast.walk(dec):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            parts.append(node.value)
    return " ".join(parts)


def scan_python_test(source: str, rel_path: str) -> List[Finding]:
    tree = ast.parse(source, filename=rel_path)
    findings: List[Finding] = []

    helper_has_oracle: Set[str] = set()
    module_has_seed = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node.func) in ("random.seed", "np.random.seed"):
            module_has_seed = True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("test_"):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Assert) or (
                    isinstance(sub, ast.Call) and "assert" in _call_name(sub.func).lower()
                ):
                    helper_has_oracle.add(node.name)
                    break

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            cname = _call_name(node.func)
            if cname in ("sys.exit", "os._exit"):
                if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == 0:
                    findings.append(
                        Finding(
                            "VER-GOV-TAMPER-001", rel_path, node.lineno, node.col_offset + 1,
                            f"Zero-exit call {cname}(0) inside test module can fabricate passing runs.", cname
                        )
                    )

    # Check uncalibrated production accuracy overclaims in Python eval scripts
    if not CALIBRATION_GUARD_RE.search(source):
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if UNCALIBRATED_CLAIM_RE.search(node.value):
                    findings.append(
                        Finding(
                            "VER-EVAL-UNCAL-001", rel_path, getattr(node, "lineno", 1),
                            getattr(node, "col_offset", 0) + 1,
                            "Uncalibrated production accuracy claim in Python eval script lacks holdout CI metadata.",
                            "eval_claim",
                        )
                    )
                    break

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test_"):
            continue

        for dec in node.decorator_list:
            dec_name = _call_name(dec.func if isinstance(dec, ast.Call) else dec)
            if dec_name in (
                "pytest.mark.skip", "mark.skip", "unittest.skip", "skip",
                "pytest.mark.xfail", "mark.xfail",
            ):
                reason = _decorator_reason_text(dec)
                is_strict_xfail = False
                if isinstance(dec, ast.Call) and dec_name.endswith("xfail"):
                    for kw in dec.keywords:
                        if kw.arg == "strict" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                            is_strict_xfail = True
                if not is_strict_xfail and not _has_tracked_skip_reason(reason):
                    findings.append(
                        Finding(
                            "VER-GOV-SKIP-001", rel_path, dec.lineno, dec.col_offset + 1,
                            f"Untracked {dec_name} on '{node.name}' lacks issue ticket and YYYY-MM-DD expiry.",
                            node.name,
                        )
                    )

        has_oracle = False
        for sub in ast.walk(node):
            if isinstance(sub, ast.Assert):
                has_oracle = True
                taut = _is_tautology(sub.test)
                if taut:
                    findings.append(
                        Finding(
                            "VER-TAU-CONST-001", rel_path, sub.lineno, sub.col_offset + 1,
                            f"Tautological assertion ({taut}) in '{node.name}'.", node.name
                        )
                    )
            elif isinstance(sub, (ast.With, ast.AsyncWith)):
                for item in sub.items:
                    ctx_name = _call_name(
                        item.context_expr.func if isinstance(item.context_expr, ast.Call) else item.context_expr
                    )
                    if ctx_name in (
                        "pytest.raises", "raises", "pytest.warns", "warns",
                        "self.assertRaises", "self.assertWarns", "self.assertLogs",
                    ):
                        has_oracle = True
            elif isinstance(sub, ast.Call):
                cname = _call_name(sub.func)
                if (
                    cname.startswith("self.assert")
                    or cname.endswith(
                        (".assert_called", ".assert_called_once", ".assert_called_with",
                         ".assert_called_once_with", ".assert_not_called", ".assert_any_call")
                    )
                    or cname in ("pytest.fail", "pytest.raises", "pytest.approx", "assert_frame_equal")
                    or (isinstance(sub.func, ast.Name) and sub.func.id in helper_has_oracle)
                ):
                    has_oracle = True
                if cname == "pytest.skip":
                    reason = _decorator_reason_text(sub)
                    if not _has_tracked_skip_reason(reason):
                        findings.append(
                            Finding(
                                "VER-GOV-SKIP-001", rel_path, sub.lineno, sub.col_offset + 1,
                                f"Imperative pytest.skip() in '{node.name}' lacks tracked issue and expiry.",
                                node.name,
                            )
                        )
                if cname in ("time.sleep", "asyncio.sleep"):
                    is_zero = (
                        len(sub.args) == 1
                        and isinstance(sub.args[0], ast.Constant)
                        and sub.args[0].value == 0
                    )
                    if not is_zero:
                        findings.append(
                            Finding(
                                "VER-FLK-NONDET-001", rel_path, sub.lineno, sub.col_offset + 1,
                                f"Wall-clock sleep {cname}() inside '{node.name}' introduces async-wait flakiness.",
                                node.name,
                            )
                        )
                if (
                    not module_has_seed
                    and cname.startswith("random.")
                    and cname not in ("random.seed", "random.Random")
                ):
                    findings.append(
                        Finding(
                            "VER-FLK-NONDET-001", rel_path, sub.lineno, sub.col_offset + 1,
                            f"Unseeded global PRNG call {cname}() inside '{node.name}'.", node.name
                        )
                    )
            elif isinstance(sub, ast.ExceptHandler):
                is_broad = sub.type is None or _call_name(sub.type) in ("Exception", "BaseException")
                if is_broad and len(sub.body) == 1:
                    stmt = sub.body[0]
                    is_noop = isinstance(stmt, (ast.Pass, ast.Continue)) or (
                        isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
                    )
                    if is_noop:
                        findings.append(
                            Finding(
                                "VER-TAU-SWALLOW-001", rel_path, sub.lineno, sub.col_offset + 1,
                                f"Broad exception-swallowing handler in '{node.name}' silently hides failures.",
                                node.name,
                            )
                        )

        if not has_oracle:
            findings.append(
                Finding(
                    "VER-TAU-NOASSERT-001", rel_path, node.lineno, node.col_offset + 1,
                    f"Test function '{node.name}' contains no assertion or expected-exception oracle.",
                    node.name,
                )
            )

    findings.extend(scan_suppression_pragmas(source, rel_path))
    return findings


def _lex_clike_tokens(src: str) -> List[Tuple[str, str, int]]:
    line = 1
    tokens: List[Tuple[str, str, int]] = []
    for m in CLIKES_TOKEN_RE.finditer(src):
        kind = m.lastgroup or ""
        val = m.group()
        if kind == "NEWLINE":
            line += 1
        elif kind == "BLOCK_COMMENT":
            line += val.count("\n")
        elif kind == "LINE_COMMENT":
            continue
        elif kind == "TEMPLATE":
            tokens.append(("STRING", val, line))
            line += val.count("\n")
        elif kind in ("DSTRING", "SSTRING"):
            tokens.append(("STRING", val, line))
        else:
            tokens.append((kind, val, line))
    return tokens


_JS_ASSERT_IDENTS = frozenset({"assert", "expect", "should", "fail"})
_JS_TEARDOWN_IDENTS = frozenset(
    {
        "kill",
        "rmSync",
        "rmdirSync",
        "unlinkSync",
        "unlink",
        "rm",
        "close",
        "destroy",
        "disconnect",
        "terminate",
        "cleanup",
        "abort",
        "end",
        "unref",
        "clearTimeout",
        "clearInterval",
        "removeAllListeners",
    }
)
_JS_POLL_PROBE_IDENTS = frozenset(
    {
        "fetch",
        "request",
        "connect",
        "get",
        "head",
        "ping",
        "health",
        "ready",
        "statSync",
        "readFileSync",
        "parse",
    }
)
_JS_REAL_IO_RE = re.compile(
    r"\b(?:spawn|execFile|createServer|fetch|http\.request|WebSocket|puppeteer|playwright|chromium)\b"
)


def _extract_try_body_before_catch(tokens: List[Tuple[str, str, int]], catch_idx: int) -> Tuple[int, List[Tuple[str, str, int]]]:
    """Return (try_idx, body_tokens) for the try { ... } immediately preceding catch_idx, or (-1, [])."""
    if catch_idx <= 0 or tokens[catch_idx - 1][1] != "}":
        return -1, []
    depth = 0
    k = catch_idx - 1
    body_start = -1
    while k >= 0:
        tval = tokens[k][1]
        if tval == "}":
            depth += 1
        elif tval == "{":
            depth -= 1
            if depth == 0:
                body_start = k
                break
        k -= 1
    if body_start > 0 and tokens[body_start - 1][0] == "IDENT" and tokens[body_start - 1][1] == "try":
        return body_start - 1, tokens[body_start + 1 : catch_idx - 1]
    return -1, []


_JS_UNIT_FRAMEWORK_RE = re.compile(
    r"""(?:from\s+["'](?:vitest|jest|@jest/globals|mocha)["']|require\s*\(\s*["'](?:vitest|jest|mocha)["']|\bvi\.|\bjest\.)"""
)


def _enclosing_block_kind(tokens: List[Tuple[str, str, int]], pos: int) -> Optional[str]:
    """Return 'finally', 'loop', or None for the innermost brace block structurally enclosing `pos`."""
    depth = 0
    k = pos - 1
    while k >= 0:
        tval = tokens[k][1]
        if tval == "}":
            depth += 1
        elif tval == "{":
            if depth == 0:
                prev = k - 1
                if prev >= 0 and tokens[prev][0] == "IDENT" and tokens[prev][1] == "finally":
                    return "finally"
                if prev >= 0 and tokens[prev][1] == ")":
                    pdepth = 0
                    m = prev
                    while m >= 0:
                        if tokens[m][1] == ")":
                            pdepth += 1
                        elif tokens[m][1] == "(":
                            pdepth -= 1
                            if pdepth == 0:
                                if m > 0 and tokens[m - 1][0] == "IDENT" and tokens[m - 1][1] in ("while", "for"):
                                    return "loop"
                                break
                        m -= 1
                return None
            depth -= 1
        k -= 1
    return None


def _is_benign_js_empty_catch(tokens: List[Tuple[str, str, int]], catch_idx: int, close_brace_idx: int) -> bool:
    """Return True only for empty catch {} structurally inside finally/teardown or a retry/polling loop (never around assertions)."""
    try_idx, body = _extract_try_body_before_catch(tokens, catch_idx)
    if try_idx < 0:
        return False
    body_idents = {val for kind, val, _ in body if kind == "IDENT"}
    if body_idents & _JS_ASSERT_IDENTS:
        return False
    if body_idents & _JS_TEARDOWN_IDENTS:
        return True
    enclosing = _enclosing_block_kind(tokens, try_idx)
    if enclosing == "finally":
        return True
    if enclosing == "loop":
        suffix_end = min(len(tokens), close_brace_idx + 25)
        suffix_idents = {val for kind, val, _ in tokens[close_brace_idx + 1 : suffix_end] if kind == "IDENT"}
        has_poll_wait = bool(suffix_idents & {"setTimeout", "sleep", "delay", "wait"})
        if has_poll_wait or bool(body_idents & _JS_POLL_PROBE_IDENTS):
            return True
    return False


def scan_js_ts_test(source: str, rel_path: str) -> List[Finding]:
    tokens = _lex_clike_tokens(source)
    n = len(tokens)
    has_fake_timers = any(t[1] == "useFakeTimers" for t in tokens)
    has_unit_framework = bool(_JS_UNIT_FRAMEWORK_RE.search(source))
    is_real_io_integration = (not has_unit_framework) and bool(_JS_REAL_IO_RE.search(source))
    findings: List[Finding] = []
    i = 0
    while i < n:
        kind, val, line = tokens[i]
        if kind == "IDENT" and val in ("xit", "xtest", "xdescribe") and i + 1 < n and tokens[i + 1][1] == "(":
            title = tokens[i + 2][1] if i + 2 < n and tokens[i + 2][0] == "STRING" else ""
            if not _has_tracked_skip_reason(title):
                findings.append(
                    Finding("VER-GOV-SKIP-001", rel_path, line, 1, f"Untracked {val}() bypass.", val)
                )
        elif (
            kind == "IDENT" and val in ("it", "test", "describe")
            and i + 2 < n and tokens[i + 1][1] == "." and tokens[i + 2][1] == "skip"
        ):
            title = tokens[i + 4][1] if i + 4 < n and tokens[i + 4][0] == "STRING" else ""
            if not _has_tracked_skip_reason(title):
                findings.append(
                    Finding("VER-GOV-SKIP-001", rel_path, line, 1, f"Untracked {val}.skip() bypass.", f"{val}.skip")
                )

        if kind == "IDENT" and val == "Math" and i + 2 < n and tokens[i + 1][1] == "." and tokens[i + 2][1] == "random":
            findings.append(
                Finding("VER-FLK-NONDET-001", rel_path, line, 1, "Unmocked Math.random() in JS/TS test.", "Math.random")
            )
        if not has_fake_timers and not is_real_io_integration and kind == "IDENT" and val == "setTimeout" and i + 1 < n and tokens[i + 1][1] == "(":
            findings.append(
                Finding("VER-FLK-NONDET-001", rel_path, line, 1, "Wall-clock setTimeout() without fake timers.", "setTimeout")
            )
        if (
            kind == "IDENT" and val == "process" and i + 5 < n
            and tokens[i + 1][1] == "." and tokens[i + 2][1] == "exit"
            and tokens[i + 3][1] == "(" and tokens[i + 4][1] == "0" and tokens[i + 5][1] == ")"
        ):
            findings.append(
                Finding("VER-GOV-TAMPER-001", rel_path, line, 1, "process.exit(0) in JS/TS test.", "process.exit")
            )

        if kind == "IDENT" and val == "expect" and i + 8 < n and tokens[i + 1][1] == "(":
            if tokens[i + 3][1] == ")" and tokens[i + 4][1] == ".":
                lhs = tokens[i + 2][1]
                matcher = tokens[i + 5][1]
                if matcher in ("toBe", "toEqual", "toStrictEqual") and tokens[i + 6][1] == "(":
                    if tokens[i + 7][1] == lhs and tokens[i + 8][1] == ")":
                        findings.append(
                            Finding(
                                "VER-TAU-CONST-001", rel_path, line, 1,
                                f"Tautological expect({lhs}).{matcher}({lhs}).", "expect"
                            )
                        )
                elif matcher == "toBeTruthy" and lhs == "true":
                    findings.append(
                        Finding("VER-TAU-CONST-001", rel_path, line, 1, "Tautological expect(true).toBeTruthy().", "expect")
                    )

        if kind == "IDENT" and val == "catch":
            j = i + 1
            if j < n and tokens[j][1] == "(":
                while j < n and tokens[j][1] != ")":
                    j += 1
                j += 1
            if j + 1 < n and tokens[j][1] == "{" and tokens[j + 1][1] == "}":
                if not _is_benign_js_empty_catch(tokens, i, j + 1):
                    findings.append(
                        Finding("VER-TAU-SWALLOW-001", rel_path, line, 1, "Empty catch {} block inside test.", "catch")
                    )

        if kind == "IDENT" and val in ("it", "test") and i + 1 < n and tokens[i + 1][1] == "(":
            j = i + 2
            depth = 1
            body_start = -1
            while j < n and depth > 0:
                tval = tokens[j][1]
                if tval == "(":
                    depth += 1
                elif tval == ")":
                    depth -= 1
                elif tval == "{" and depth == 1:
                    body_start = j
                    break
                j += 1
            if body_start != -1:
                bdepth = 0
                k = body_start
                has_oracle = False
                while k < n:
                    tkind, tval, _ = tokens[k]
                    if tval == "{":
                        bdepth += 1
                    elif tval == "}":
                        bdepth -= 1
                        if bdepth == 0:
                            break
                    elif tkind == "IDENT" and tval in (
                        "expect", "assert", "should", "rejects", "resolves", "toThrow", "fail"
                    ):
                        has_oracle = True
                    k += 1
                if not has_oracle:
                    findings.append(
                        Finding(
                            "VER-TAU-NOASSERT-001", rel_path, line, 1,
                            f"JS/TS {val}() block has no expect/assert oracle.", val
                        )
                    )
        i += 1
    findings.extend(scan_suppression_pragmas(source, rel_path))
    return findings


def scan_go_test(source: str, rel_path: str) -> List[Finding]:
    tokens = _lex_clike_tokens(source)
    findings: List[Finding] = []
    n = len(tokens)
    i = 0
    while i < n:
        kind, val, line = tokens[i]
        if kind == "IDENT" and val == "time" and i + 2 < n and tokens[i + 1][1] == "." and tokens[i + 2][1] == "Sleep":
            findings.append(
                Finding("VER-FLK-NONDET-001", rel_path, line, 1, "Wall-clock time.Sleep() in Go test.", "time.Sleep")
            )
        if kind == "IDENT" and val in ("Skip", "Skipf", "SkipNow") and i > 0 and tokens[i - 1][1] == ".":
            reason = tokens[i + 2][1] if i + 2 < n and tokens[i + 2][0] == "STRING" else ""
            if not _has_tracked_skip_reason(reason):
                findings.append(
                    Finding("VER-GOV-SKIP-001", rel_path, line, 1, f"Untracked Go t.{val}() skip.", val)
                )
        if kind == "IDENT" and val == "func" and i + 2 < n and tokens[i + 1][1].startswith("Test"):
            fn_name = tokens[i + 1][1]
            j = i + 2
            while j < n and tokens[j][1] != "{":
                j += 1
            if j < n:
                bdepth = 0
                k = j
                has_oracle = False
                while k < n:
                    tkind, tval, _ = tokens[k]
                    if tval == "{":
                        bdepth += 1
                    elif tval == "}":
                        bdepth -= 1
                        if bdepth == 0:
                            break
                    elif tkind == "IDENT" and tval in (
                        "Error", "Errorf", "Fatal", "Fatalf", "Fail", "FailNow",
                        "assert", "require", "Equal", "NoError", "ErrorIs",
                    ):
                        has_oracle = True
                    k += 1
                if not has_oracle:
                    findings.append(
                        Finding("VER-TAU-NOASSERT-001", rel_path, line, 1, f"Go '{fn_name}' lacks failure/assert oracle.", fn_name)
                    )
        i += 1
    findings.extend(scan_suppression_pragmas(source, rel_path))
    return findings


def _scan_json_thresholds(obj: Any, rel_path: str, path_prefix: str = "") -> List[Finding]:
    findings: List[Finding] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = k.lower()
            child = f"{path_prefix}.{k}" if path_prefix else k
            if kl == "fail_under" and isinstance(v, (int, float)) and v == 0:
                findings.append(
                    Finding("VER-GOV-TAMPER-001", rel_path, 1, 1, f"Coverage threshold '{child}' zeroed to 0.", child)
                )
            elif kl == "break" and ("stryker" in path_prefix.lower() or "thresholds" in path_prefix.lower()):
                if v is None or (isinstance(v, (int, float)) and v == 0):
                    findings.append(
                        Finding("VER-GOV-TAMPER-001", rel_path, 1, 1, f"Stryker mutation break '{child}' disabled ({v}).", child)
                    )
            elif kl in ("branches", "lines", "statements", "functions") and "coveragethreshold" in path_prefix.lower():
                if isinstance(v, (int, float)) and v == 0:
                    findings.append(
                        Finding("VER-GOV-TAMPER-001", rel_path, 1, 1, f"Coverage threshold '{child}' zeroed to 0.", child)
                    )
            else:
                findings.extend(_scan_json_thresholds(v, rel_path, child))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            findings.extend(_scan_json_thresholds(item, rel_path, f"{path_prefix}[{idx}]"))
    return findings


def scan_ci_and_config(source: str, rel_path: str) -> List[Finding]:
    findings: List[Finding] = []
    lower = rel_path.lower()
    if lower.endswith(".json"):
        try:
            parsed = json.loads(source)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            findings.extend(_scan_json_thresholds(parsed, rel_path))
            findings.extend(scan_eval_artifact(source, rel_path))
            return findings

    lines = source.splitlines()
    is_ci_workflow = (
        lower.endswith((".yml", ".yaml"))
        and (".github/workflows/" in lower or ("runs-on:" in source and "steps:" in source))
    )
    for idx, raw_line in enumerate(lines, start=1):
        code_line = raw_line.split("#", 1)[0]
        if not code_line.strip():
            continue
        for pat, desc in TAMPER_CLI_PATTERNS:
            if pat.search(code_line):
                findings.append(
                    Finding("VER-GOV-TAMPER-001", rel_path, idx, 1, f"CI/config tamper pattern: {desc}.", "ci_config")
                )
        if SHELL_EXIT_MASK_RE.search(code_line) and TEST_GATE_CMD_RE.search(code_line):
            findings.append(
                Finding(
                    "VER-GOV-TAMPER-001", rel_path, idx, 1,
                    "CI/config tamper pattern: shell exit-code masking (|| true) on test/quality gate.",
                    "ci_config",
                )
            )
        if is_ci_workflow:
            if re.search(r"^\s*continue-on-error\s*:\s*true\b", code_line):
                if not re.search(r"steps\.[A-Za-z0-9_-]+\.outcome", source):
                    findings.append(
                        Finding(
                            "VER-GOV-SKIP-001", rel_path, idx, 1,
                            "CI workflow sets continue-on-error: true without downstream steps.<id>.outcome gate.",
                            "continue-on-error",
                        )
                    )
        if lower.endswith(("pyproject.toml", ".coveragerc", "setup.cfg")):
            if re.search(r"\bfail_under\s*=\s*0(?:\.0+)?\b", code_line):
                findings.append(
                    Finding("VER-GOV-TAMPER-001", rel_path, idx, 1, "Coverage fail_under set to 0.", "fail_under")
                )
        if any(k in lower for k in ("vitest.config", "jest.config")):
            if re.search(r"\b(branches|lines|statements|functions)\s*:\s*0(?:\.0+)?\b", code_line):
                findings.append(
                    Finding("VER-GOV-TAMPER-001", rel_path, idx, 1, "JS coverage threshold zeroed in config.", "threshold")
                )
        if "stryker" in lower and re.search(r'"?break"?\s*:\s*(?:null|0)\b', code_line):
            findings.append(
                Finding("VER-GOV-TAMPER-001", rel_path, idx, 1, "Stryker mutation break threshold disabled.", "break")
            )
    return findings


def scan_auditor_markdown(source: str, rel_path: str) -> List[Finding]:
    """Enforce ECOSYSTEM_CONTRACT v1.2.0 §8.1 read-only allowed-tools on Clean-Room auditor docs."""
    m = re.match(r"^---\n(.*?)\n---", source, re.DOTALL)
    if not m:
        return []
    fm_text = m.group(1)
    is_auditor = bool(
        re.search(r"^\s*role\s*:\s*clean-room-auditor\b", fm_text, re.MULTILINE)
        or re.search(r"^\s*clean_room_required\s*:\s*true\b", fm_text, re.MULTILINE)
        or re.search(r"^\s*name\s*:\s*auditor-[a-z0-9-]+\b", fm_text, re.MULTILINE)
    )
    if not is_auditor:
        return []

    findings: List[Finding] = []
    lines = fm_text.splitlines()
    in_allowed_list = False
    for idx, line in enumerate(lines, start=2):
        stripped = line.strip()
        if re.match(r"^allowed-tools\s*:", stripped):
            val = stripped.split(":", 1)[1].strip()
            if val:
                tokens = [t.strip("[]\"' ").lower() for t in re.split(r"[\s,]+", val) if t.strip("[]\"' ")]
                bad = sorted(t for t in tokens if t in FORBIDDEN_AUDITOR_WRITE_TOOLS)
                if bad:
                    findings.append(
                        Finding(
                            "VER-GOV-TAMPER-001", rel_path, idx, 1,
                            f"Clean-Room auditor declares forbidden write/edit tools in allowed-tools: {bad}.",
                            "allowed-tools",
                        )
                    )
                in_allowed_list = False
            else:
                in_allowed_list = True
        elif in_allowed_list:
            if stripped.startswith("-"):
                tok = stripped.lstrip("-").strip().strip("\"'").lower()
                if tok in FORBIDDEN_AUDITOR_WRITE_TOOLS:
                    findings.append(
                        Finding(
                            "VER-GOV-TAMPER-001", rel_path, idx, 1,
                            f"Clean-Room auditor declares forbidden write/edit tool '{tok}' in allowed-tools.",
                            "allowed-tools",
                        )
                    )
            elif stripped and not stripped.startswith("#"):
                in_allowed_list = False
    return findings


def _parse_flat_eval_yaml(source: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for raw_line in source.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        k, v = [p.strip().strip('"').strip("'") for p in line.split(":", 1)]
        if v.lower() == "true":
            data[k] = True
        elif v.lower() == "false":
            data[k] = False
        elif re.fullmatch(r"\d+", v):
            data[k] = int(v)
        else:
            data[k] = v
    return data


def scan_eval_artifact(source: str, rel_path: str) -> List[Finding]:
    findings: List[Finding] = []
    lower = rel_path.lower()
    if lower.endswith(".json"):
        try:
            data = json.loads(source)
        except json.JSONDecodeError:
            return findings
    elif lower.endswith((".yaml", ".yml")):
        data = _parse_flat_eval_yaml(source)
    else:
        return findings

    if not isinstance(data, dict):
        return findings
    if (
        data.get("evaluation_layer") == "layer_1_synthetic_fixture_regression_floor"
        and data.get("production_claim_prohibited") is True
    ):
        return findings

    claim_keys = {"accuracy", "precision", "recall", "pass_rate", "judge_score", "true_positive_rate"}
    present_claims = claim_keys.intersection(data.keys())
    if present_claims:
        required_cal = {"holdout_n_pos", "holdout_n_neg", "ci_95_low", "ci_95_high", "youden_j", "calibration_method"}
        missing = sorted(required_cal.difference(data.keys()))
        underpowered = (
            isinstance(data.get("holdout_n_pos"), int) and data["holdout_n_pos"] < 100
        ) or (
            isinstance(data.get("holdout_n_neg"), int) and data["holdout_n_neg"] < 100
        )
        if missing or underpowered:
            findings.append(
                Finding(
                    "VER-EVAL-UNCAL-001", rel_path, 1, 1,
                    f"Eval claims {sorted(present_claims)} lack valid Layer 2 holdout calibration "
                    f"(missing={missing}, underpowered_m_lt_100={underpowered}).",
                    "eval_calibration",
                )
            )
    return findings


def scan_suppression_pragmas(source: str, rel_path: str, max_pragmas: int = 3) -> List[Finding]:
    matches = list(MASS_PRAGMA_RE.finditer(source))
    if len(matches) > max_pragmas:
        line = source[: matches[0].start()].count("\n") + 1
        return [
            Finding(
                "VER-GOV-TAMPER-001", rel_path, line, 1,
                f"Excessive coverage/mutation suppression pragmas ({len(matches)} > cap {max_pragmas}).",
                "pragma_suppression",
            )
        ]
    return []


def classify_candidate(rel_path: str, single_file_mode: bool = False) -> Optional[str]:
    low = rel_path.lower()
    name = pathlib.PurePosixPath(low).name
    if low.endswith(".py") and (
        single_file_mode
        or name.startswith("test_")
        or name.endswith("_test.py")
        or "/tests/" in f"/{low}"
    ):
        return "python_test"
    if re.search(r"\.(test|spec)\.(js|jsx|ts|tsx|mjs|cjs)$", low) or re.match(
        r"^test[-_].+\.(js|jsx|ts|tsx|mjs|cjs)$", name
    ):
        return "js_ts_test"
    if low.endswith("_test.go"):
        return "go_test"
    if low.endswith(".md") and ("auditor" in low or single_file_mode):
        return "auditor_md"
    if ".github/workflows/" in low and low.endswith((".yml", ".yaml")):
        return "ci_config"
    if low.endswith((".yml", ".yaml")) and (single_file_mode or "workflow" in name or "ci" in name):
        return "ci_config"
    if name in (
        "pyproject.toml", ".coveragerc", "setup.cfg", "pytest.ini",
        "vitest.config.ts", "vitest.config.js", "jest.config.ts", "jest.config.js",
        "stryker.conf.json", "stryker.config.json", ".gremlins.yaml",
    ):
        return "ci_config"
    if low.endswith(".json") and (
        single_file_mode or any(k in name for k in ("coverage", "threshold", "stryker", "jest", "vitest", "eval", "benchmark", "calibration"))
    ):
        return "ci_config"
    if low.endswith((".yaml", ".yml")) and any(k in name for k in ("eval", "benchmark", "calibration")):
        return "eval_artifact"
    if low.endswith((".py", ".ts", ".tsx", ".js", ".go")):
        return "prod_pragma_only"
    return None


def _scan_one_file(
    full: pathlib.Path,
    rel: str,
    kind: str,
    max_file_bytes: int,
    findings: List[Finding],
    skipped: SkipTelemetry,
) -> bool:
    try:
        st = full.stat()
    except OSError:
        skipped.record("os_error", rel)
        return False
    if st.st_size > max_file_bytes:
        skipped.record("oversized", rel)
        return False
    try:
        raw = full.read_bytes()
    except OSError:
        skipped.record("os_error", rel)
        return False
    if b"\x00" in raw:
        skipped.record("binary_or_decode", rel)
        return False
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        skipped.record("binary_or_decode", rel)
        return False

    if kind == "python_test":
        try:
            findings.extend(scan_python_test(text, rel))
        except (SyntaxError, ValueError):
            skipped.record("python_syntax_error", rel)
            return False
    elif kind == "js_ts_test":
        findings.extend(scan_js_ts_test(text, rel))
    elif kind == "go_test":
        findings.extend(scan_go_test(text, rel))
    elif kind == "ci_config":
        findings.extend(scan_ci_and_config(text, rel))
    elif kind == "auditor_md":
        findings.extend(scan_auditor_markdown(text, rel))
    elif kind == "eval_artifact":
        findings.extend(scan_eval_artifact(text, rel))
    elif kind == "prod_pragma_only":
        findings.extend(scan_suppression_pragmas(text, rel))
    return True


def scan_repository(target: pathlib.Path, max_file_bytes: int = MAX_FILE_BYTES_DEFAULT) -> Dict[str, Any]:
    t0 = time.perf_counter()
    findings: List[Finding] = []
    skipped = SkipTelemetry()
    files_scanned = 0

    if target.is_file():
        rel = target.name
        kind = classify_candidate(rel, single_file_mode=True)
        if kind is not None:
            if _scan_one_file(target, rel, kind, max_file_bytes, findings, skipped):
                files_scanned += 1
    else:
        for dirpath, dirnames, filenames in os.walk(target):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for fname in sorted(filenames):
                full = pathlib.Path(dirpath) / fname
                rel = full.relative_to(target).as_posix()
                kind = classify_candidate(rel, single_file_mode=False)
                if kind is None:
                    continue
                if _scan_one_file(full, rel, kind, max_file_bytes, findings, skipped):
                    files_scanned += 1

    # Single-root-cause deduplication by (rule_id, file_path, line, symbol)
    dedup_map: Dict[Tuple[str, str, int, str], Finding] = {}
    for f in findings:
        key = (f.rule_id, f.file_path, f.line, f.symbol)
        if key not in dedup_map:
            dedup_map[key] = f
    deduped_findings = sorted(dedup_map.values(), key=lambda x: (x.file_path, x.line, x.rule_id))

    counts = {"blocker": 0, "major": 0, "minor": 0}
    finding_dicts: List[Dict[str, Any]] = []
    for f in deduped_findings:
        sev = RULE_META[f.rule_id]["severity"]
        counts[sev.lower()] += 1
        finding_dicts.append(
            {
                "rule_id": f.rule_id,
                "canonical_id": RULE_META[f.rule_id]["canonical_id"],
                "module_id": RULE_META[f.rule_id]["module_id"],
                "severity": sev,
                "file_path": f.file_path,
                "line": f.line,
                "column": f.column,
                "symbol": f.symbol,
                "message": f.message,
                "fingerprint": f.fingerprint(),
            }
        )

    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    scan_coverage = {
        "total_candidate_files": files_scanned + skipped.total,
        "files_scanned": files_scanned,
        "files_skipped": skipped.to_dict(),
        "elapsed_ms": elapsed_ms,
    }
    return {
        "scanner": SCANNER_NAME,
        "version": SCANNER_VERSION,
        "suite_id": "verification-eval",
        "counts": counts,
        "scan_coverage": scan_coverage,
        "findings": finding_dicts,
    }


def to_sarif(report: Dict[str, Any]) -> Dict[str, Any]:
    rules_list = [
        {
            "id": rid,
            "name": rid,
            "shortDescription": {"text": meta["short_description"]},
            "defaultConfiguration": {"level": meta["sarif_level"]},
            "properties": {
                "canonical_id": meta["canonical_id"],
                "module_id": meta["module_id"],
                "severity": meta["severity"],
            },
        }
        for rid, meta in sorted(RULE_META.items())
    ]
    results = [
        {
            "ruleId": item["rule_id"],
            "level": RULE_META[item["rule_id"]]["sarif_level"],
            "message": {"text": item["message"]},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": item["file_path"]},
                        "region": {"startLine": item["line"], "startColumn": item["column"]},
                    }
                }
            ],
            "partialFingerprints": {"primaryLocationLineHash": item["fingerprint"]},
            "properties": {
                "canonical_id": item["canonical_id"],
                "severity": item["severity"],
                "symbol": item["symbol"],
            },
        }
        for item in report["findings"]
    ]
    return {
        "version": "2.1.0",
        "$schema": SARIF_SCHEMA_URI,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": SCANNER_NAME,
                        "version": SCANNER_VERSION,
                        "rules": rules_list,
                    }
                },
                "results": results,
                "properties": {
                    "scan_coverage": report["scan_coverage"],
                },
            }
        ],
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Tier A CPU verification pre-scanner (ECOSYSTEM_CONTRACT v1.2.0)")
    parser.add_argument("target_pos", nargs="?", type=pathlib.Path, default=None, help="File or repository root to scan")
    parser.add_argument("--target", "--root", dest="target_opt", type=pathlib.Path, default=None, help="File or repository root to scan")
    parser.add_argument("--format", choices=["json", "sarif"], default="json", help="Stdout output format when --json-out/--sarif-out omitted")
    parser.add_argument("--json-out", "--json-output", dest="json_out", type=pathlib.Path, default=None)
    parser.add_argument("--sarif-out", "--sarif-output", dest="sarif_out", type=pathlib.Path, default=None)
    parser.add_argument("--max-file-bytes", type=int, default=MAX_FILE_BYTES_DEFAULT)
    args = parser.parse_args(argv)

    target = args.target_opt or args.target_pos or pathlib.Path(".")
    report = scan_repository(target.resolve(), max_file_bytes=args.max_file_bytes)

    if args.json_out:
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.sarif_out:
        args.sarif_out.write_text(json.dumps(to_sarif(report), indent=2) + "\n", encoding="utf-8")
    if not args.json_out and not args.sarif_out:
        payload = to_sarif(report) if args.format == "sarif" else report
        print(json.dumps(payload, indent=2))

    if report["counts"]["blocker"] > 0:
        return 2
    if report["counts"]["major"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
