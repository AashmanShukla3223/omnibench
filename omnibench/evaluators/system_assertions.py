"""
OmniBench System State Assertion Evaluator.
Verifies task completion via CLI commands, file existence, and API checks.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class AssertionSpec:
    """Specification for a single system state assertion."""

    type: str
    """Assertion type: 'file_exists', 'file_contains', 'cmd_output', 'env_var', 'python_eval'."""

    target: str
    """Primary target: file path, command string, env var name, or Python expression."""

    expected: Optional[Any] = None
    """Expected value for comparison (None = presence check only)."""

    match_mode: str = "exact"
    """Comparison mode: 'exact', 'contains', 'regex', 'gt', 'lt', 'gte', 'lte'."""

    timeout_seconds: float = 10.0
    """Timeout for command-based assertions."""

    description: str = ""
    """Human-readable description of what is being asserted."""


@dataclass
class AssertionResult:
    """Result of a single system assertion evaluation."""

    spec: AssertionSpec
    passed: bool
    actual_value: Any
    error: Optional[str] = None

    @property
    def description(self) -> str:
        return self.spec.description or self.spec.target


class SystemAssertionEvaluator:
    """
    Evaluates system state assertions using CLI, file I/O, and environment checks.
    Supports: file_exists, file_contains, cmd_output, env_var, python_eval.
    """

    def evaluate(self, spec: AssertionSpec) -> AssertionResult:
        """Evaluate a single AssertionSpec and return AssertionResult."""
        try:
            handler = {
                "file_exists": self._check_file_exists,
                "file_contains": self._check_file_contains,
                "cmd_output": self._check_cmd_output,
                "env_var": self._check_env_var,
                "python_eval": self._check_python_eval,
            }.get(spec.type)

            if handler is None:
                return AssertionResult(
                    spec=spec,
                    passed=False,
                    actual_value=None,
                    error=f"Unknown assertion type: '{spec.type}'",
                )
            return handler(spec)

        except Exception as exc:
            logger.error("Assertion evaluation error: %s", exc)
            return AssertionResult(
                spec=spec, passed=False, actual_value=None, error=str(exc)
            )

    def evaluate_all(
        self, specs: List[AssertionSpec]
    ) -> Dict[str, Any]:
        """Evaluate all specs and return summary."""
        results = [self.evaluate(s) for s in specs]
        passed = sum(1 for r in results if r.passed)
        return {
            "passed": passed == len(results),
            "total": len(results),
            "passed_count": passed,
            "failed_count": len(results) - passed,
            "results": results,
        }

    def _check_file_exists(self, spec: AssertionSpec) -> AssertionResult:
        exists = os.path.exists(spec.target)
        return AssertionResult(spec=spec, passed=exists, actual_value=exists)

    def _check_file_contains(self, spec: AssertionSpec) -> AssertionResult:
        try:
            with open(spec.target, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except FileNotFoundError:
            return AssertionResult(
                spec=spec, passed=False, actual_value=None, error="File not found"
            )

        passed = self._compare(content, spec.expected, spec.match_mode)
        return AssertionResult(spec=spec, passed=passed, actual_value=content[:500])

    def _check_cmd_output(self, spec: AssertionSpec) -> AssertionResult:
        try:
            proc = subprocess.run(
                spec.target,
                shell=True,
                capture_output=True,
                text=True,
                timeout=spec.timeout_seconds,
            )
            actual = proc.stdout.strip()
            if spec.expected is None:
                passed = proc.returncode == 0
            else:
                passed = self._compare(actual, spec.expected, spec.match_mode)
            return AssertionResult(spec=spec, passed=passed, actual_value=actual)
        except subprocess.TimeoutExpired:
            return AssertionResult(
                spec=spec, passed=False, actual_value=None, error="Command timed out"
            )

    def _check_env_var(self, spec: AssertionSpec) -> AssertionResult:
        actual = os.environ.get(spec.target)
        if spec.expected is None:
            passed = actual is not None
        else:
            passed = self._compare(actual or "", spec.expected, spec.match_mode)
        return AssertionResult(spec=spec, passed=passed, actual_value=actual)

    def _check_python_eval(self, spec: AssertionSpec) -> AssertionResult:
        try:
            result = eval(spec.target, {"__builtins__": {}}, {})  # noqa: S307
            if spec.expected is None:
                passed = bool(result)
            else:
                passed = self._compare(result, spec.expected, spec.match_mode)
            return AssertionResult(spec=spec, passed=passed, actual_value=result)
        except Exception as exc:
            return AssertionResult(
                spec=spec, passed=False, actual_value=None, error=str(exc)
            )

    def _compare(self, actual: Any, expected: Any, mode: str) -> bool:
        if mode == "exact":
            return str(actual) == str(expected)
        elif mode == "contains":
            return str(expected) in str(actual)
        elif mode == "regex":
            return bool(re.search(str(expected), str(actual)))
        elif mode == "gt":
            return float(actual) > float(expected)
        elif mode == "lt":
            return float(actual) < float(expected)
        elif mode == "gte":
            return float(actual) >= float(expected)
        elif mode == "lte":
            return float(actual) <= float(expected)
        return str(actual) == str(expected)
