from __future__ import annotations

import sqlite3
from pathlib import Path

from django.core.management.base import BaseCommand

from analytics.blondon_paths import blondon_memory_dir


def _count(conn: sqlite3.Connection, table: str) -> int | None:
    try:
        row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        return int(row[0]) if row else 0
    except sqlite3.OperationalError:
        return None


class Command(BaseCommand):
    help = (
        "Print row counts for key tables in amo_events.db / amo_entities.db "
        "(Blondon_memory or Blondon_memory/RAW_MEM). Read-only; no Django DB writes."
    )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--raw-mem",
            action="store_true",
            help="Use Blondon_memory/RAW_MEM/*.db",
        )
        parser.add_argument(
            "--events-db",
            default=None,
            help="Path to amo_events.db",
        )
        parser.add_argument(
            "--entities-db",
            default=None,
            help="Path to amo_entities.db",
        )

    def handle(self, *args, **options):
        default_root = blondon_memory_dir()
        raw_root = default_root / "RAW_MEM"
        if options["raw_mem"]:
            ev = Path(options["events_db"] or raw_root / "amo_events.db")
            en = Path(options["entities_db"] or raw_root / "amo_entities.db")
        else:
            ev = Path(options["events_db"] or default_root / "amo_events.db")
            en = Path(options["entities_db"] or default_root / "amo_entities.db")

        ev, en = ev.resolve(), en.resolve()
        if not ev.exists():
            raise FileNotFoundError(f"events db not found: {ev}")
        if not en.exists():
            raise FileNotFoundError(f"entities db not found: {en}")

        self.stdout.write(self.style.NOTICE(f"events:    {ev}"))
        self.stdout.write(self.style.NOTICE(f"entities:  {en}"))

        events_tables = ("events", "lead_transitions", "notes", "event_types")
        entities_tables = (
            "pipelines",
            "statuses",
            "leads",
            "tasks",
            "contacts",
            "companies",
            "links",
            "users",
            "sources",
            "customers",
            "customer_transactions",
            "conversations",
            "unsorted",
            "lists",
            "list_elements",
            "entity_subscribers",
            "roles",
        )

        with sqlite3.connect(str(ev), timeout=60) as conn:
            self.stdout.write("\n[amo_events.db]")
            for t in events_tables:
                n = _count(conn, t)
                self.stdout.write(f"  {t}: {n if n is not None else '(missing)'}")

        with sqlite3.connect(str(en), timeout=60) as conn:
            self.stdout.write("\n[amo_entities.db]")
            for t in entities_tables:
                n = _count(conn, t)
                self.stdout.write(f"  {t}: {n if n is not None else '(missing)'}")

        self.stdout.write(self.style.SUCCESS("\nDone."))
