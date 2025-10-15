#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
project_inspector.py
Запустить из КОРНЯ репозитория. Печатает подробный отчёт
и (опционально) сохраняет снапшоты контекста.

Опции:
  --save  : дополнительно сгенерировать CONTEXT_SNAPSHOT.md, .env.sample, ci_summary.md
"""

from __future__ import annotations

import ast
import datetime as dt
import fnmatch
import io
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path.cwd()


# --------- helpers ---------
def hr(title: str, ch: str = "─", width: int = 80) -> str:
    pad = max(0, width - len(title) - 2)
    return f"{title} {ch*pad}"


def read_text_safe(p: Path, limit: int = 20000) -> str:
    try:
        data = p.read_text(encoding="utf-8", errors="replace")
        if len(data) > limit:
            return data[:limit] + f"\n\n... [truncated, total {len(data)} bytes]"
        return data
    except Exception as e:
        return f"<<cannot read: {e}>>"


def file_meta(p: Path) -> str:
    try:
        stat = p.stat()
        size = stat.st_size
        mtime = dt.datetime.fromtimestamp(stat.st_mtime).isoformat(sep=" ", timespec="seconds")
        return f"path: {p}\nexists: True\nsize: {size} bytes\nmodified: {mtime}"
    except FileNotFoundError:
        return f"path: {p}\nexists: False"


def try_import_yaml():
    try:
        import yaml  # type: ignore

        return yaml
    except Exception:
        return None


def try_parse_yaml(text: str) -> Optional[Dict[str, Any]]:
    y = try_import_yaml()
    if not y:
        return None
    try:
        obj = y.safe_load(text)
        if isinstance(obj, dict):
            return obj
        return None
    except Exception:
        return None


def try_parse_toml(text: str) -> Optional[Dict[str, Any]]:
    # Python 3.11+: tomllib в stdlib
    try:
        import tomllib  # type: ignore

        return tomllib.loads(text)
    except Exception:
        pass
    # простой «poor-man» парсер ключ=значение для верхнего уровня
    data: Dict[str, Any] = {}
    current = data
    tables: Dict[str, Dict[str, Any]] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            name = line.strip("[]").strip()
            current = tables.setdefault(name, {})
            data[name] = current
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            data_or_tbl = current if current is not data else data
            data_or_tbl[k.strip()] = v.strip().strip('"').strip("'")
    return data


def short(obj: Any, n: int = 80) -> str:
    s = repr(obj)
    return s if len(s) <= n else s[:n] + "…"


def discover_files(patterns: List[str]) -> List[Path]:
    found: List[Path] = []
    for pat in patterns:
        if any(ch in pat for ch in "*?[]"):
            for p in ROOT.rglob("*"):
                rel = p.relative_to(ROOT).as_posix()
                if fnmatch.fnmatch(rel, pat):
                    found.append(p)
        else:
            p = ROOT / pat
            if p.exists():
                found.append(p)
    # de-dup, keep order
    seen = set()
    uniq = []
    for p in found:
        if p not in seen:
            uniq.append(p)
            seen.add(p)
    return uniq


# --------- Python AST analyzers ----------
class PyAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.classes: List[Tuple[str, List[str], Optional[str]]] = []  # (name, bases, doc)
        self.urlpatterns: List[Dict[str, Any]] = []
        self.assigns: Dict[str, Any] = {}

    def visit_ClassDef(self, node: ast.ClassDef):
        bases = []
        for b in node.bases:
            bases.append(self._base_name(b))
        doc = ast.get_docstring(node)
        self.classes.append((node.name, bases, doc))
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        # capture simple constants for DEBUG, ALLOWED_HOSTS etc.
        for tgt in node.targets:
            if isinstance(tgt, ast.Name):
                name = tgt.id
                val = self._literal_or_repr(node.value)
                self.assigns[name] = val
        self.generic_visit(node)

    def visit_List(self, node: ast.List):
        self.generic_visit(node)

    def _literal_or_repr(self, node: ast.AST) -> Any:
        try:
            return ast.literal_eval(node)
        except Exception:
            return self._expr_to_str(node)

    def _expr_to_str(self, node: ast.AST) -> str:
        try:
            return ast.unparse(node)  # py3.9+ via backport, py3.10+ std
        except Exception:
            return node.__class__.__name__

    def _base_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._base_name(node.value)}.{node.attr}"
        if isinstance(node, ast.Subscript):
            return self._base_name(node.value)
        return self._expr_to_str(node)


def analyze_python_file(p: Path) -> Dict[str, Any]:
    out: Dict[str, Any] = {"path": str(p), "exists": p.exists()}
    if not p.exists():
        return out
    src = p.read_text(encoding="utf-8", errors="replace")
    out["size"] = p.stat().st_size
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        out["syntax_error"] = str(e)
        out["preview"] = src[:4000]
        return out
    analyzer = PyAnalyzer()
    analyzer.visit(tree)
    out["classes"] = [
        {"name": name, "bases": bases, "doc": (doc or "").splitlines()[0] if doc else None}
        for (name, bases, doc) in analyzer.classes
    ]
    out["assigns"] = analyzer.assigns

    # extract urlpatterns manually from AST (simple cases)
    urlpatterns = []
    try:
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == "urlpatterns":
                        lst = node.value
                        items = []
                        if isinstance(lst, (ast.List, ast.Tuple)):
                            items = lst.elts
                        else:
                            # Could be router.urls; we'll capture repr
                            urlpatterns.append({"raw": analyzer._expr_to_str(lst)})
                            continue
                        for el in items:
                            entry = {"raw": analyzer._expr_to_str(el)}
                            if (
                                isinstance(el, ast.Call)
                                and isinstance(el.func, ast.Name)
                                and el.func.id in {"path", "re_path"}
                            ):
                                if (
                                    el.args
                                    and isinstance(el.args[0], ast.Constant)
                                    and isinstance(el.args[0].value, str)
                                ):
                                    entry["pattern"] = el.args[0].value
                                # name kw
                                for kw in el.keywords or []:
                                    if kw.arg == "name":
                                        val = analyzer._literal_or_repr(kw.value)
                                        entry["name"] = val
                            urlpatterns.append(entry)
        if urlpatterns:
            out["urlpatterns"] = urlpatterns
    except Exception:
        pass

    # Celery config hints
    if p.name == "celery.py":
        # naive detection of broker/result
        broker = re.findall(r"broker_url\s*=\s*[\"']([^\"']+)[\"']", src)
        result = re.findall(r"result_backend\s*=\s*[\"']([^\"']+)[\"']", src)
        out["celery_hints"] = {
            "broker_url": broker[0] if broker else None,
            "result_backend": result[0] if result else None,
        }
    return out


# --------- domain-specific parsers ----------
def summarize_dockerfile(p: Path) -> Dict[str, Any]:
    info: Dict[str, Any] = {"path": str(p), "exists": p.exists()}
    if not p.exists():
        return info
    txt = p.read_text(encoding="utf-8", errors="replace")
    info["preview"] = txt[:4000]
    info["from"] = first_match(txt, r"^\s*FROM\s+(.+)$", flags=re.M)
    info["cmd"] = first_match(txt, r"^\s*CMD\s+(.+)$", flags=re.M)
    info["entrypoint"] = first_match(txt, r"^\s*ENTRYPOINT\s+(.+)$", flags=re.M)
    expose = re.findall(r"^\s*EXPOSE\s+(.+)$", txt, flags=re.M)
    if expose:
        info["expose"] = expose
    return info


def summarize_docker_compose(p: Path) -> Dict[str, Any]:
    info: Dict[str, Any] = {"path": str(p), "exists": p.exists()}
    if not p.exists():
        return info
    text = p.read_text(encoding="utf-8", errors="replace")
    info["preview"] = text[:6000]
    y = try_parse_yaml(text)
    if y:
        services = y.get("services") or {}
        sv = {}
        for name, svc in services.items():
            if not isinstance(svc, dict):
                continue
            sv[name] = {
                "image": svc.get("image"),
                "build": svc.get("build"),
                "ports": svc.get("ports"),
                "env_file": svc.get("env_file"),
                "environment": svc.get("environment"),
                "depends_on": svc.get("depends_on"),
            }
        info["services"] = sv
        info["version"] = y.get("version")
    else:
        # fallback: grab service names under 'services:'
        services = []
        if "services:" in text:
            block = text.split("services:", 1)[1]
            for line in block.splitlines():
                if re.match(r"^\s{2,}[a-zA-Z0-9_\-]+:\s*$", line):
                    services.append(line.strip().rstrip(":"))
        info["services_fallback"] = services
    return info


def summarize_yaml_file(p: Path) -> Dict[str, Any]:
    info: Dict[str, Any] = {"path": str(p), "exists": p.exists()}
    if not p.exists():
        return info
    text = p.read_text(encoding="utf-8", errors="replace")
    info["preview"] = text[:6000]
    y = try_parse_yaml(text)
    if y:
        info["keys"] = list(y.keys())
        if "openapi" in y:
            paths = y.get("paths") or {}
            info["openapi"] = {
                "version": y.get("openapi"),
                "paths_count": len(paths),
                "info": y.get("info"),
            }
    else:
        # minimalistic openapi hints
        m = re.search(r"^\s*openapi:\s*([^\n\r]+)", text, flags=re.M)
        if m:
            info["openapi"] = {"version": m.group(1).strip()}
        info["paths_count_guess"] = len(re.findall(r"^\s{0,2}/[^:\n]+:\s*$", text, flags=re.M))
    return info


def summarize_precommit(p: Path) -> Dict[str, Any]:
    return summarize_yaml_file(p)


def summarize_pyproject(p: Path) -> Dict[str, Any]:
    info: Dict[str, Any] = {"path": str(p), "exists": p.exists()}
    if not p.exists():
        return info
    text = p.read_text(encoding="utf-8", errors="replace")
    info["preview"] = text[:6000]
    data = try_parse_toml(text)
    if data:
        # poetry & project formats
        meta = {}
        for sect in ("tool.poetry", "project"):
            d = data.get(sect, {})
            if isinstance(d, dict):
                meta[sect] = {
                    "name": d.get("name"),
                    "version": d.get("version"),
                    "description": d.get("description"),
                    "dependencies": (
                        list((d.get("dependencies") or {}).keys())
                        if isinstance(d.get("dependencies"), dict)
                        else d.get("dependencies")
                    ),
                }
        fmt = {}
        for tool in ("tool.black", "tool.isort", "tool.pytest.ini_options", "tool.coverage.run"):
            fmt[tool] = data.get(tool)
        info["meta"] = meta
        info["tools"] = fmt
    return info


def summarize_pytest_ini(p: Path) -> Dict[str, Any]:
    info = {"path": str(p), "exists": p.exists()}
    if not p.exists():
        return info
    text = p.read_text(encoding="utf-8", errors="replace")
    info["preview"] = text[:4000]
    markers = re.findall(r"^\s*markers\s*=\s*(.+)$", text, flags=re.M)
    addopts = re.findall(r"^\s*addopts\s*=\s*(.+)$", text, flags=re.M)
    testpaths = re.findall(r"^\s*testpaths\s*=\s*(.+)$", text, flags=re.M)
    info["markers"] = markers
    info["addopts"] = addopts
    info["testpaths"] = testpaths
    return info


def summarize_coverage_xml(p: Path) -> Dict[str, Any]:
    info = {"path": str(p), "exists": p.exists()}
    if not p.exists():
        return info
    try:
        tree = ET.parse(p)
        root = tree.getroot()
        totals = root.find("counter[@type='LINE']")
        cov = root.attrib.get("line-rate") or root.attrib.get("branch-rate")
        info["coverage_attr"] = cov
        if totals is not None:
            info["lines_covered"] = totals.attrib.get("covered")
            info["lines_missed"] = totals.attrib.get("missed")
    except Exception as e:
        info["error"] = str(e)
    return info


def summarize_github_actions() -> Dict[str, Any]:
    base = ROOT / ".github" / "workflows"
    info: Dict[str, Any] = {"base": str(base), "exists": base.exists(), "workflows": []}
    if not base.exists():
        return info
    for yml in sorted(base.glob("*.yml")) + sorted(base.glob("*.yaml")):
        entry = {"file": str(yml)}
        text = yml.read_text(encoding="utf-8", errors="replace")
        data = try_parse_yaml(text)
        if data:
            entry["name"] = data.get("name")
            entry["on"] = (
                list(data.get("on", {}).keys())
                if isinstance(data.get("on"), dict)
                else data.get("on")
            )
            jobs = data.get("jobs", {})
            if isinstance(jobs, dict):
                entry["jobs"] = list(jobs.keys())
        else:
            # fallback
            entry["name_guess"] = first_match(text, r"^\s*name:\s*(.+)$", flags=re.M)
        info["workflows"].append(entry)
    return info


def first_match(text: str, pattern: str, flags=0) -> Optional[str]:
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None


# --------- domain output builders ----------
def print_section(title: str):
    print(hr(f" {title} "))


def print_file_report(p: Path, parser=None, show_content=False, content_limit=2000):
    print_section(str(p))
    print(file_meta(p))
    if not p.exists():
        print()
        return
    if parser:
        data = parser(p) if callable(parser) else None
        if data:
            print("\nParsed:")
            print(indent_json(data))
    if show_content:
        print("\nContent (truncated):")
        print(read_text_safe(p, content_limit))
    print()


def indent_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, default=str)


# --------- environment keys generation ----------
ENV_KEYS = [
    "DJANGO_SETTINGS_MODULE",
    "SECRET_KEY",
    "DATABASE_URL",
    "REDIS_URL",
    "ALLOWED_HOSTS",
    "DEBUG",
    "CELERY_BROKER_URL",
    "CELERY_RESULT_BACKEND",
    "SENTRY_DSN",
]


def build_env_placeholders(settings_detect: Dict[str, Any]) -> Dict[str, str]:
    # Default placeholders; try to guess better from compose/settings
    defaults = {
        "DJANGO_SETTINGS_MODULE": "src.config.settings.dev",
        "SECRET_KEY": "changeme-in-prod",
        "DATABASE_URL": "postgresql://user:password@db:5432/mini_crm_base",
        "REDIS_URL": "redis://redis:6379/0",
        "ALLOWED_HOSTS": "localhost,127.0.0.1",
        "DEBUG": "True",
        "CELERY_BROKER_URL": "redis://redis:6379/1",
        "CELERY_RESULT_BACKEND": "redis://redis:6379/2",
        "SENTRY_DSN": "",
    }
    # try to refine from settings.py assigns
    for k in ("DEBUG", "ALLOWED_HOSTS"):
        v = settings_detect.get(k)
        if v is not None:
            if isinstance(v, list):
                defaults[k] = ",".join(map(str, v))
            else:
                defaults[k] = str(v)
    # Celery hints
    for k in ("CELERY_BROKER_URL", "CELERY_RESULT_BACKEND"):
        hv = settings_detect.get(k) or settings_detect.get(k.lower())
        if hv:
            defaults[k] = str(hv)
    return defaults


# --------- main runner ----------
def main(save: bool = False):
    print(hr(" PROJECT INSPECTOR REPORT "))
    print(f"root: {ROOT}")
    print(f"generated: {dt.datetime.now().isoformat(sep=' ', timespec='seconds')}\n")

    # 1) Docker & compose
    print_section("Docker")
    compose = ROOT / "docker-compose.yml"
    dockerfile = ROOT / "Dockerfile"
    entrypoint = ROOT / "docker" / "entrypoint.sh"
    print_file_report(compose, parser=summarize_docker_compose, show_content=False)
    print_file_report(dockerfile, parser=summarize_dockerfile, show_content=False)
    print_file_report(entrypoint, parser=None, show_content=True, content_limit=4000)

    # 2) Django settings + urls + celery
    print_section("Django config")
    settings_dir = ROOT / "src" / "config" / "settings"
    base_py = settings_dir / "base.py"
    dev_py = settings_dir / "dev.py"
    prod_py = settings_dir / "prod.py"
    urls_py = ROOT / "src" / "config" / "urls.py"
    celery_py = ROOT / "src" / "config" / "celery.py"

    base_info = analyze_python_file(base_py)
    dev_info = analyze_python_file(dev_py)
    prod_info = analyze_python_file(prod_py)
    urls_info = analyze_python_file(urls_py)
    celery_info = analyze_python_file(celery_py)

    for pth, info in [(base_py, base_info), (dev_py, dev_info), (prod_py, prod_info)]:
        print_section(str(pth))
        print(file_meta(pth))
        print("\nAST summary:")
        print(
            indent_json(
                {
                    "classes": info.get("classes"),
                    "assigns": {
                        k: short(v)
                        for k, v in (info.get("assigns") or {}).items()
                        if k
                        in {
                            "DEBUG",
                            "ALLOWED_HOSTS",
                            "DATABASES",
                            "CELERY_BROKER_URL",
                            "CELERY_RESULT_BACKEND",
                            "SENTRY_DSN",
                        }
                    },
                }
            )
        )
        print()

    print_section(str(urls_py))
    print(file_meta(urls_py))
    print("\nURL patterns (best-effort):")
    print(indent_json(urls_info.get("urlpatterns") or urls_info))
    print()

    print_section(str(celery_py))
    print(file_meta(celery_py))
    print("\nCelery hints:")
    print(indent_json(celery_info.get("celery_hints") or {}))
    print()

    # 3) apps: clients & deals (models, serializers, views)
    print_section("Apps: clients & deals")
    app_specs = [
        ("clients", ["models.py", "serializers.py", "views.py"]),
        ("deals", ["models.py", "serializers.py", "views.py"]),
    ]
    for app, files in app_specs:
        print(hr(f" [{app}] "))
        for fname in files:
            p = ROOT / "src" / app / fname
            info = analyze_python_file(p)
            print_section(f"{app}/{fname}")
            print(file_meta(p))
            print("\nClasses:")
            print(indent_json(info.get("classes") or []))
            if fname == "views.py":
                # guess ViewSets to mention endpoints
                viewsets = [
                    c
                    for c in (info.get("classes") or [])
                    if "ViewSet" in " ".join(c.get("bases", []))
                ]
                if viewsets:
                    print("\nViewSets (guess):")
                    print(indent_json(viewsets))
            print()

    # 4) core/pagination.py, core/tasks.py
    print_section("Core")
    for rel in ["src/core/pagination.py", "src/core/tasks.py"]:
        p = ROOT / rel
        info = analyze_python_file(p)
        print_section(rel)
        print(file_meta(p))
        print("\nClasses/Assigns:")
        print(indent_json({"classes": info.get("classes"), "assigns": info.get("assigns")}))
        print()

    # 5) pre-commit, pyproject, pytest, coverage
    print_section("Tooling")
    print_file_report(ROOT / ".pre-commit-config.yaml", parser=summarize_precommit)
    print_file_report(ROOT / "pyproject.toml", parser=summarize_pyproject)
    print_file_report(ROOT / "pytest.ini", parser=summarize_pytest_ini)
    print_file_report(ROOT / "coverage.xml", parser=summarize_coverage_xml)

    # 6) CI
    print_section("GitHub Actions")
    print(indent_json(summarize_github_actions()))
    print()

    # 7) OpenAPI schema
    print_section("OpenAPI schema")
    print_file_report(ROOT / "src" / "schema.yaml", parser=summarize_yaml_file, show_content=False)

    # 8) Environment keys (placeholders)
    print_section("Environment placeholders")
    # try detect from settings (prefer dev.py then base.py)
    settings_detect: Dict[str, Any] = {}
    for src_info in (dev_info, base_info, prod_info, celery_info):
        for k, v in (src_info.get("assigns") or {}).items():
            settings_detect[k] = v
        for k, v in (src_info.get("celery_hints") or {}).items():
            if v:
                settings_detect[k.upper()] = v
    env = build_env_placeholders(settings_detect)
    print(indent_json(env))
    print()

    # 9) Extra: summarize routers if present in urls.py (best-effort)
    try:
        urls_txt = (ROOT / "src" / "config" / "urls.py").read_text(
            encoding="utf-8", errors="replace"
        )
        if "DefaultRouter" in urls_txt or "SimpleRouter" in urls_txt:
            print_section("Router hints from urls.py (raw)")
            for m in re.finditer(r"router\.(register|include)\((.+?)\)", urls_txt, flags=re.S):
                print(f"- router.{m.group(1)}({m.group(2).strip()})")
            print()
    except Exception:
        pass

    # 10) Optionally save snapshot files
    if save:
        save_artifacts(env)


def save_artifacts(env: Dict[str, str]):
    snapshot_path = ROOT / "CONTEXT_SNAPSHOT.md"
    env_sample = ROOT / ".env.sample"
    ci_summary = ROOT / "ci_summary.md"

    # CONTEXT_SNAPSHOT.md: краткий обзор проекта для «введения в контекст»
    parts = []
    parts.append(f"# Context Snapshot — {ROOT.name}\n")
    parts.append("Этот файл создан автоматически `project_inspector.py --save`.\n")
    parts.append("## Сервисы (docker-compose)\n")
    dc = ROOT / "docker-compose.yml"
    if dc.exists():
        data = summarize_docker_compose(dc)
        services = data.get("services") or {}
        if services:
            for name, svc in services.items():
                parts.append(
                    f"- **{name}**: image={svc.get('image')}, "
                    f"build={svc.get('build')}, ports={svc.get('ports')}\n"
                )
    parts.append("## Django настройки\n")
    parts.append("- Базовый модуль:  'src.config.settings'\n")
    parts.append(f"- Ключевые env: {', '.join(ENV_KEYS)}\n")
    parts.append("## API схема\n")
    sch = summarize_yaml_file(ROOT / "src" / "schema.yaml")
    if sch.get("openapi"):
        oi = sch["openapi"]
        parts.append(
            f"- OpenAPI: v{oi.get('version')}, "
            f"paths≈{oi.get('paths_count') or sch.get('paths_count_guess')}\n"
        )
    parts.append("## Тесты и покрытие\n")
    cov = summarize_coverage_xml(ROOT / "coverage.xml")
    cov_info = (
        f"coverage={cov.get('coverage_attr')}, "
        f"covered={cov.get('lines_covered')}, "
        f"missed={cov.get('lines_missed')}"
    )
    parts.append(f"- Coverage: {cov_info}\n")
    snapshot_path.write_text("\n".join(parts), encoding="utf-8")

    # .env.sample
    with io.StringIO() as buf:
        for k in ENV_KEYS:
            buf.write(f"{k}={env.get(k,'')}\n")
        env_sample.write_text(buf.getvalue(), encoding="utf-8")

    # ci_summary.md
    ci = summarize_github_actions()
    ci_text = ["# CI Summary\n"]
    if ci.get("workflows"):
        for wf in ci["workflows"]:
            ci_text.append(
                f"- **{Path(wf['file']).name}**: "
                f"name={wf.get('name') or wf.get('name_guess')}, "
                f"on={wf.get('on')}, jobs={wf.get('jobs')}\n"
            )
    else:
        ci_text.append("_No workflows found._\n")
    ci_summary.write_text("\n".join(ci_text), encoding="utf-8")

    print(hr(" ARTIFACTS WRITTEN "))
    print(f"- {snapshot_path}")
    print(f"- {env_sample}")
    print(f"- {ci_summary}")
    print()


# --------- entry ----------
if __name__ == "__main__":
    save = "--save" in sys.argv
    main(save=save)
