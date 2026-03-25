from __future__ import annotations

import argparse
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Optional

from django.core.management.base import BaseCommand
from django.db import transaction

from analytics.blondon_paths import blondon_memory_dir
from analytics.models import AmoLeadTransition, AmoPipeline, AmoStatus


def _sqlite_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cur = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table_name,),
    )
    return cur.fetchone() is not None


def _iter_sqlite_rows(conn: sqlite3.Connection, query: str, params: tuple, batch_size: int):
    cur = conn.execute(query, params)
    while True:
        rows = cur.fetchmany(batch_size)
        if not rows:
            break
        yield rows


class Command(BaseCommand):
    help = (
        "Sync amoCRM lead transitions from downloaded sqlite snapshots "
        "into Postgres (analytics app). Idempotent by event_id. "
        "Use --raw-mem to read from Blondon_memory/RAW_MEM (full-size dumps). "
        "SQLite layout: amo_events.db has events, lead_transitions, notes, event_types; "
        "amo_entities.db has pipelines, statuses, leads, tasks, links, contacts, companies, …"
    )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--raw-mem",
            action="store_true",
            help="Use Blondon_memory/RAW_MEM/amo_events.db and amo_entities.db (full dumps).",
        )
        parser.add_argument(
            "--events-db",
            default=None,
            help="Path to amo_events.db (sqlite). Default: Blondon_memory/amo_events.db",
        )
        parser.add_argument(
            "--entities-db",
            default=None,
            help="Path to amo_entities.db (sqlite). Default: Blondon_memory/amo_entities.db",
        )
        parser.add_argument(
            "--transition-table",
            default="lead_transitions",
            help="Sqlite transition table name (default: lead_transitions)",
        )
        parser.add_argument(
            "--rebuild-transition-table",
            action="store_true",
            help="Rebuild lead_transitions in sqlite by re-running transition.py if needed.",
        )
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=5000,
            help="Bulk insert chunk size",
        )

    def handle(self, *args, **options):
        raw_mem = options["raw_mem"]
        default_root = blondon_memory_dir()
        raw_root = default_root / "RAW_MEM"
        if raw_mem:
            events_default = raw_root / "amo_events.db"
            entities_default = raw_root / "amo_entities.db"
        else:
            events_default = default_root / "amo_events.db"
            entities_default = default_root / "amo_entities.db"

        events_db_path = Path(options["events_db"] or events_default).resolve()
        entities_db_path = Path(options["entities_db"] or entities_default).resolve()
        transition_table = options["transition_table"]
        rebuild_needed = options["rebuild_transition_table"]
        chunk_size = int(options["chunk_size"])

        if not events_db_path.exists():
            raise FileNotFoundError(f"events db not found: {events_db_path}")
        if not entities_db_path.exists():
            raise FileNotFoundError(f"entities db not found: {entities_db_path}")

        self.stdout.write(self.style.NOTICE(f"[1/3] Load pipelines/statuses from {entities_db_path}"))
        self._sync_pipelines_and_statuses(entities_db_path)

        self.stdout.write(self.style.NOTICE(f"[2/3] Ensure transitions in {events_db_path}"))
        self._ensure_lead_transitions(events_db_path, transition_table, rebuild_needed=rebuild_needed)

        self.stdout.write(self.style.NOTICE("[3/3] Import lead_transitions into Postgres"))
        self._sync_lead_transitions(events_db_path, transition_table, chunk_size=chunk_size)

        self.stdout.write(self.style.SUCCESS("Sync completed."))

    def _sync_pipelines_and_statuses(self, entities_db_path: Path) -> None:
        with sqlite3.connect(str(entities_db_path), timeout=30) as conn:
            pipeline_rows = conn.execute(
                "SELECT id, name, sort, is_main FROM pipelines ORDER BY id"
            ).fetchall()
            status_rows = conn.execute(
                "SELECT id, pipeline_id, name, sort, is_final FROM statuses ORDER BY id"
            ).fetchall()

        pipelines_by_id = {}
        for pid, name, sort, is_main in pipeline_rows:
            pipelines_by_id[pid] = AmoPipeline.objects.update_or_create(
                id=int(pid),
                defaults={
                    "name": name,
                    "sort": sort if sort is not None else None,
                    "is_main": bool(is_main),
                },
            )[0]

        for sid, pid, name, sort, is_final in status_rows:
            pipeline_obj = pipelines_by_id.get(int(pid))
            if pipeline_obj is None:
                # Inconsistent snapshot: skip invalid status.
                continue

            AmoStatus.objects.update_or_create(
                id=int(sid),
                defaults={
                    "pipeline": pipeline_obj,
                    "name": name,
                    "sort": sort if sort is not None else None,
                    "is_final": bool(is_final),
                },
            )

    def _ensure_lead_transitions(self, events_db_path: Path, transition_table: str, rebuild_needed: bool) -> None:
        with sqlite3.connect(str(events_db_path), timeout=30) as conn:
            exists = _sqlite_table_exists(conn, transition_table)
        if exists and not rebuild_needed:
            return

        script_path = blondon_memory_dir() / "transition.py"
        if not script_path.exists():
            raise FileNotFoundError(f"transition.py not found: {script_path.resolve()}")

        # Rebuild transitions in sqlite by running the existing extractor script.
        self.stdout.write(self.style.NOTICE(f"[transition] Rebuilding `{transition_table}` in sqlite via {script_path}"))
        subprocess.run(
            [sys.executable, str(script_path), "--db", str(events_db_path)],
            check=True,
            cwd=str(Path.cwd()),
        )

    def _sync_lead_transitions(
        self, events_db_path: Path, transition_table: str, *, chunk_size: int
    ) -> None:
        with sqlite3.connect(str(events_db_path), timeout=30) as conn:
            total = conn.execute(f"SELECT COUNT(*) FROM {transition_table}").fetchone()[0]
            self.stdout.write(self.style.NOTICE(f"Found {total} rows in sqlite `{transition_table}`"))

            status_by_id = {
                s.id: s for s in AmoStatus.objects.all().iterator()
            }

            imported = 0
            batch_idx = 0

            # Generator of batches
            for rows in _iter_sqlite_rows(
                conn,
                f"""
                SELECT event_id, lead_id, at, by_user, from_status_id, to_status_id
                FROM {transition_table}
                ORDER BY at ASC
                """,
                params=(),
                batch_size=chunk_size,
            ):
                batch_idx += 1
                objs = []
                for (
                    event_id,
                    lead_id,
                    at,
                    by_user,
                    from_status_id,
                    to_status_id,
                ) in rows:
                    from_status = (
                        status_by_id.get(int(from_status_id))
                        if from_status_id is not None
                        else None
                    )
                    to_status = (
                        status_by_id.get(int(to_status_id))
                        if to_status_id is not None
                        else None
                    )

                    objs.append(
                        AmoLeadTransition(
                            event_id=str(event_id),
                            lead_id=int(lead_id),
                            at=int(at),
                            by_user=int(by_user) if by_user is not None else None,
                            from_status=from_status,
                            to_status=to_status,
                        )
                    )

                # Bulk insert with ignore_conflicts for idempotency.
                with transaction.atomic():
                    AmoLeadTransition.objects.bulk_create(
                        objs, ignore_conflicts=True, batch_size=chunk_size
                    )
                imported += len(objs)
                if batch_idx % 10 == 0:
                    self.stdout.write(f"Imported batch {batch_idx}; total imported rows (attempted): {imported}")

