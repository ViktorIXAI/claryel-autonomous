#!/usr/bin/env python3
"""JSON/JSONL and schema QA for the repository.

This intentionally uses only the standard library. It validates:
- every tracked/public JSON and JSONL file parses;
- every schema file is parseable and has an object root;
- known public instances satisfy their local schema.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URI_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:.*$")


def iter_files(suffixes: tuple[str, ...]):
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in suffixes:
            yield path


def type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def validate(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    types = schema.get("type")
    if types is not None:
        choices = types if isinstance(types, list) else [types]
        if not any(type_matches(value, choice) for choice in choices):
            errors.append(f"{path}: expected type {types}, got {type(value).__name__}")
            return errors

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value not in enum")

    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required {key}")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    errors.append(f"{path}: additional property {key}")
        for key, child_schema in props.items():
            if key in value and isinstance(child_schema, dict):
                errors.extend(validate(value[key], child_schema, f"{path}.{key}"))

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: fewer than {schema['minItems']} items")
        items = schema.get("items")
        if isinstance(items, dict):
            for i, item in enumerate(value):
                errors.extend(validate(item, items, f"{path}[{i}]"))

    if isinstance(value, str):
        fmt = schema.get("format")
        if fmt == "date" and not DATE_RE.match(value):
            errors.append(f"{path}: expected ISO date")
        if fmt == "uri" and not URI_RE.match(value):
            errors.append(f"{path}: expected URI")
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: shorter than {schema['minLength']}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: longer than {schema['maxLength']}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: less than {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: greater than {schema['maximum']}")

    return errors


def main() -> int:
    failures: list[str] = []

    for path in iter_files((".json", ".jsonl")):
        rel = path.relative_to(ROOT)
        if path.suffix == ".json":
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                failures.append(f"{rel}: invalid JSON: {exc}")
                continue
            if path.name.endswith(".schema.json"):
                if not isinstance(data, dict):
                    failures.append(f"{rel}: schema root must be object")
                elif data.get("type") != "object":
                    failures.append(f"{rel}: public schema root type must be object")
        else:
            for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    json.loads(line)
                except Exception as exc:
                    failures.append(f"{rel}:{lineno}: invalid JSONL line: {exc}")

    schema_path = ROOT / "experiments/pricing/schema.json"
    example_path = ROOT / "examples/price-snapshot-example.json"
    if schema_path.exists() and example_path.exists():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        example = json.loads(example_path.read_text(encoding="utf-8"))
        failures.extend(validate(example, schema, "price_snapshot_example"))

    if failures:
        print("JSON/schema QA failed:")
        for f in failures:
            print(f"- {f}")
        return 1

    print("JSON/schema QA: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
