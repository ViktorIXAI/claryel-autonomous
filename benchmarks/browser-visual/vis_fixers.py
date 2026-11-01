#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic HTML repair rules for the visual benchmark contour.
Prompt is NEVER changed; we only fix mechanical damage in the model output.
Every applied rule is reported and logged; unverifiable damage -> no fix."""
import re

THREE_VERSION = "0.169.0"
IMPORTMAP = (
    '<script type="importmap">{"imports":{"three":"https://unpkg.com/three@%s/build/three.module.js",'
    '"three/addons/":"https://unpkg.com/three@%s/examples/jsm/"}}</script>' % (THREE_VERSION, THREE_VERSION))

ADDONS = {  # THREE.X -> import { X } from 'three/addons/...'
    "Reflector": "three/addons/objects/Reflector.js",
    "OrbitControls": "three/addons/controls/OrbitControls.js",
    "Sky": "three/addons/objects/Sky.js",
    "Water": "three/addons/objects/Water.js",
}


def fix(html):
    applied = []
    # 1. drop prose before the document start
    m = re.search(r"(?i)<!doctype html|<html[\s>]", html)
    if m and m.start() > 0:
        html = html[m.start():]
        applied.append("strip_prose")
    uses_three = re.search(r"from\s+['\"]three", html) or "THREE." in html
    has_import = re.search(r"<script[^>]*\btype=[\"']module", html)
    has_map = "importmap" in html
    # 2. missing importmap for module pages referencing three
    if has_import and uses_three and not has_map:
        html = html.replace("<head>", "<head>\n" + IMPORTMAP, 1)
        applied.append("add_importmap")
    # 3. addon classes used as THREE.X without an import
    for cls, mod in ADDONS.items():
        if re.search(r"THREE\.%s\b" % cls, html) and not re.search(r"import\s*\{[^}]*\b%s\b" % cls, html):
            if has_import or (uses_three and has_map):
                html = html.replace("<script type=\"module\">",
                                    "<script type=\"module\">\nimport %s from '%s';" % ("{ " + cls + " }", mod), 1)
                html = re.sub(r"THREE\.%s\b" % cls, cls, html)
                applied.append("addon_import_" + cls)
    # 4. whole-object assignment to .position/.rotation (read-only in three)
    m = re.search(r"([\w.\[\]]+)\.position\s*=\s*new THREE\.Vector3\(\s*([\w.+-]+)\s*,\s*([\w.+-]+)\s*,\s*([\w.+-]+)\s*\)", html)
    if m:
        html = re.sub(r"([\w.\[\]]+)\.position\s*=\s*new THREE\.Vector3\(\s*([\w.+-]+)\s*,\s*([\w.+-]+)\s*,\s*([\w.+-]+)\s*\)",
                      r"\1.position.set(\2,\3,\4)", html)
        applied.append("position_set")
    # 5. syntax balance: report only, do not guess
    bad = None
    body = re.sub(r"<script.*?</script>", lambda m: m.group(0), html, flags=re.S)
    for tag in ("script",):
        for mm in re.finditer(r"<script[^>]*>(.*?)</script>", body, re.S):
            s = mm.group(1)
            if s.count("{") != s.count("}") or s.count("(") != s.count(")"):
                bad = "unbalanced_braces"
                break
    return html, applied, bad


if __name__ == "__main__":
    import sys
    src = open(sys.argv[1], encoding="utf-8").read()
    out, ap, bad = fix(src)
    print("applied:", ap, "damage:", bad)
    if ap and len(sys.argv) > 2:
        open(sys.argv[2], "w", encoding="utf-8").write(out)


def fix_merge_geometries(src):
    """BufferGeometry has no .merge(); rewrite X.merge(Y) -> mergeGeometries([X,Y])."""
    import re as _re
    if ".merge(" not in src or "three" not in src:
        return src, []
    applied = []
    if "BufferGeometryUtils" not in src:
        def _add(m):
            return m.group(0)[:-1] + "\n  import * as BufferGeometryUtils from 'three/addons/utils/BufferGeometryUtils.js';\n}"
        src2 = _re.sub(r"(import\s*\{[^}]*\}\s*from\s*'three';)", _add, src, count=1)
        if src2 != src:
            src = src2; applied.append("import_BufferGeometryUtils")
    def _rw(m):
        return "BufferGeometryUtils.mergeGeometries([%s, %s])" % (m.group(1), m.group(2))
    src2 = _re.sub(r"([A-Za-z_$][\w$]*)\.merge\(\s*([A-Za-z_$][\w$]*)\s*\)", _rw, src)
    if src2 != src:
        src = src2; applied.append("mergeGeometries")
    return src, applied
