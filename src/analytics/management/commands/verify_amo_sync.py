"""
Сверка объёмов между SQLite-дампом (Blondon_memory / RAW_MEM) и PostgreSQL после ETL.

Использование после: sync_amo_transitions, sync_amo_entities на целевой БД.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from analytics.blondon_paths import blondon_memory_dir
from analytics.models import AmoLead, AmoLeadTransition, AmoLink, AmoPipeline, AmoStatus, AmoTask


def _sqlite_count(conn: sqlite3.Connection, table: str) -> int | None:
    try:
        row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        return int(row[0]) if row else 0
    except sqlite3.OperationalError:
        return None


class Command(BaseCommand):
    help = (
        "Compare row counts: SQLite (amo_events.db / amo_entities.db) vs Django analytics tables. "
        "Run after sync_amo_transitions and sync_amo_entities."
    )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--raw-mem",
            action="store_true",
            help="Use Blondon_memory/RAW_MEM/*.db",
        )
        parser.add_argument("--events-db", default=None, help="Path to amo_events.db")
        parser.add_argument("--entities-db", default=None, help="Path to amo_entities.db")
        parser.add_argument(
            "--fail-on-mismatch",
            action="store_true",
            help="Exit with code 1 if any comparable count differs",
        )

    def handle(self, *args, **options):
        root = blondon_memory_dir()
        raw_root = root / "RAW_MEM"
        if options["raw_mem"]:
            ev = Path(options["events_db"] or raw_root / "amo_events.db")
            en = Path(options["entities_db"] or raw_root / "amo_entities.db")
        else:
            ev = Path(options["events_db"] or root / "amo_events.db")
            en = Path(options["entities_db"] or root / "amo_entities.db")

        ev, en = ev.resolve(), en.resolve()
        if not ev.exists():
            raise FileNotFoundError(f"events db not found: {ev}")
        if not en.exists():
            raise FileNotFoundError(f"entities db not found: {en}")

        self.stdout.write(self.style.NOTICE(f"SQLite events:   {ev}"))
        self.stdout.write(self.style.NOTICE(f"SQLite entities: {en}\n"))

        table_names = connection.introspection.table_names()
        if "amo_pipelines" not in table_names:
            raise CommandError(
                "В текущей Django БД нет таблиц приложения analytics (например amo_pipelines). "
                "Сначала выполните: python manage.py migrate\n"
                "Убедитесь, что используете тот же DJANGO_SETTINGS_MODULE, что и для runserver/sync."
            )

        sqlite_ev: dict[str, int | None] = {}
        sqlite_en: dict[str, int | None] = {}

        with sqlite3.connect(str(ev), timeout=120) as conn:
            sqlite_ev["lead_transitions"] = _sqlite_count(conn, "lead_transitions")

        with sqlite3.connect(str(en), timeout=120) as conn:
            for t in ("pipelines", "statuses", "leads", "tasks", "links"):
                sqlite_en[t] = _sqlite_count(conn, t)

        pg = {
            "pipelines": AmoPipeline.objects.count(),
            "statuses": AmoStatus.objects.count(),
            "lead_transitions": AmoLeadTransition.objects.count(),
            "leads": AmoLead.objects.count(),
            "tasks": AmoTask.objects.count(),
            "links": AmoLink.objects.count(),
        }

        rows = [
            ("pipelines", sqlite_en.get("pipelines"), pg["pipelines"]),
            ("statuses", sqlite_en.get("statuses"), pg["statuses"]),
            ("lead_transitions", sqlite_ev.get("lead_transitions"), pg["lead_transitions"]),
            ("leads", sqlite_en.get("leads"), pg["leads"]),
            ("tasks", sqlite_en.get("tasks"), pg["tasks"]),
            ("links", sqlite_en.get("links"), pg["links"]),
        ]

        mismatch = False
        self.stdout.write(f"{'table':<22} {'sqlite':>12} {'django_db':>12} {'ok':>6}")
        for name, sq, pq in rows:
            if sq is None:
                self.stdout.write(f"{name:<22} {'(n/a)':>12} {pq:>12} {'—':>6}")
                continue
            ok = sq == pq
            if not ok:
                mismatch = True
            mark = "yes" if ok else "NO"
            style = self.style.SUCCESS if ok else self.style.ERROR
            self.stdout.write(
                style(f"{name:<22} {sq:>12} {pq:>12} {mark:>6}")
            )

        if mismatch and options["fail_on_mismatch"]:
            self.stdout.write(self.style.ERROR("\nMismatch: re-run sync commands or investigate."))
            sys.exit(1)
        if mismatch:
            self.stdout.write(
                self.style.WARNING(
                    "\nCounts differ (expected until full import or if rows were skipped)."
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("\nAll comparable counts match."))
