from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from django.core.management.base import BaseCommand
from django.db import transaction

from analytics.blondon_paths import blondon_memory_dir
from analytics.models import AmoLead, AmoLink, AmoPipeline, AmoStatus, AmoTask


def _iter_sqlite_rows(
    conn: sqlite3.Connection, query: str, params: tuple, batch_size: int
) -> Iterable[list[tuple]]:
    cur = conn.execute(query, params)
    while True:
        rows = cur.fetchmany(batch_size)
        if not rows:
            break
        yield rows


def _parse_json_cell(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        val = json.loads(raw)
        return val if isinstance(val, dict) else {}
    except Exception:
        return {}


class Command(BaseCommand):
    help = (
        "Sync amoCRM entities from amo_entities.db (leads, tasks, links) into Postgres. "
        "Requires pipelines/statuses already synced (e.g. sync_amo_transitions). "
        "Idempotent: leads/tasks by primary key, links by unique constraint."
    )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--raw-mem",
            action="store_true",
            help="Use Blondon_memory/RAW_MEM/amo_entities.db",
        )
        parser.add_argument(
            "--entities-db",
            default=None,
            help="Path to amo_entities.db",
        )
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=3000,
            help="Batch size for bulk operations",
        )
        parser.add_argument(
            "--skip-links",
            action="store_true",
            help="Do not import links (large table)",
        )

    def handle(self, *args, **options):
        root = blondon_memory_dir()
        if options["raw_mem"]:
            path = Path(options["entities_db"] or root / "RAW_MEM" / "amo_entities.db")
        else:
            path = Path(options["entities_db"] or root / "amo_entities.db")
        path = path.resolve()
        if not path.exists():
            raise FileNotFoundError(f"entities db not found: {path}")

        chunk = int(options["chunk_size"])
        self.stdout.write(self.style.NOTICE(f"Using {path}"))

        pipelines = {p.id for p in AmoPipeline.objects.all()}
        statuses = {s.id for s in AmoStatus.objects.all()}

        with sqlite3.connect(str(path), timeout=60) as conn:
            self._sync_leads(conn, pipelines, statuses, chunk)
            self._sync_tasks(conn, chunk)
            if not options["skip_links"]:
                self._sync_links(conn, chunk)

        self.stdout.write(self.style.SUCCESS("Sync amo_entities completed."))

    def _sync_leads(
        self,
        conn: sqlite3.Connection,
        pipelines: set[int],
        statuses: set[int],
        chunk: int,
    ) -> None:
        self.stdout.write(self.style.NOTICE("[leads] importing…"))
        total = 0
        for rows in _iter_sqlite_rows(
            conn,
            """
            SELECT id, name, price, pipeline_id, status_id, created_at, updated_at,
                   responsible_user_id, is_deleted, raw_json
            FROM leads
            ORDER BY id
            """,
            (),
            chunk,
        ):
            objs: list[AmoLead] = []
            for (
                lid,
                name,
                price,
                pipeline_id,
                status_id,
                created_at,
                updated_at,
                responsible_user_id,
                is_deleted,
                raw_json,
            ) in rows:
                pid = int(pipeline_id) if pipeline_id is not None else None
                if pid is None or pid not in pipelines:
                    continue
                sid = int(status_id) if status_id is not None else None
                status_obj = None
                if sid is not None and sid in statuses:
                    status_obj_id = sid
                else:
                    status_obj_id = None

                objs.append(
                    AmoLead(
                        id=int(lid),
                        pipeline_id=pid,
                        status_id=status_obj_id,
                        name=name or "",
                        price=price,
                        created_at=created_at,
                        updated_at=updated_at,
                        responsible_user_id=responsible_user_id,
                        is_deleted=bool(is_deleted),
                        raw_json=_parse_json_cell(raw_json),
                    )
                )
            if not objs:
                continue
            with transaction.atomic():
                AmoLead.objects.bulk_create(
                    objs,
                    batch_size=chunk,
                    update_conflicts=True,
                    unique_fields=["id"],
                    update_fields=[
                        "pipeline_id",
                        "status_id",
                        "name",
                        "price",
                        "created_at",
                        "updated_at",
                        "responsible_user_id",
                        "is_deleted",
                        "raw_json",
                    ],
                )
            total += len(objs)
            self.stdout.write(f"  leads batch: +{len(objs)} (total attempted {total})")

    def _sync_tasks(self, conn: sqlite3.Connection, chunk: int) -> None:
        self.stdout.write(self.style.NOTICE("[tasks] importing…"))
        total = 0
        for rows in _iter_sqlite_rows(
            conn,
            """
            SELECT id, entity_type, entity_id, text, is_completed, complete_till,
                   created_at, updated_at, responsible_user_id, created_by, result, raw_json
            FROM tasks
            ORDER BY id
            """,
            (),
            chunk,
        ):
            objs: list[AmoTask] = []
            for row in rows:
                (
                    tid,
                    entity_type,
                    entity_id,
                    text,
                    is_completed,
                    complete_till,
                    created_at,
                    updated_at,
                    responsible_user_id,
                    created_by,
                    result,
                    raw_json,
                ) = row
                objs.append(
                    AmoTask(
                        id=int(tid),
                        entity_type=entity_type or "",
                        entity_id=entity_id,
                        text=text or "",
                        is_completed=bool(is_completed) if is_completed is not None else None,
                        complete_till=complete_till,
                        created_at=created_at,
                        updated_at=updated_at,
                        responsible_user_id=responsible_user_id,
                        created_by=created_by,
                        result=result or "",
                        raw_json=_parse_json_cell(raw_json),
                    )
                )
            with transaction.atomic():
                AmoTask.objects.bulk_create(
                    objs,
                    batch_size=chunk,
                    update_conflicts=True,
                    unique_fields=["id"],
                    update_fields=[
                        "entity_type",
                        "entity_id",
                        "text",
                        "is_completed",
                        "complete_till",
                        "created_at",
                        "updated_at",
                        "responsible_user_id",
                        "created_by",
                        "result",
                        "raw_json",
                    ],
                )
            total += len(objs)
            self.stdout.write(f"  tasks batch: +{len(objs)} (total attempted {total})")

    def _sync_links(self, conn: sqlite3.Connection, chunk: int) -> None:
        self.stdout.write(self.style.NOTICE("[links] importing…"))
        total = 0
        for rows in _iter_sqlite_rows(
            conn,
            """
            SELECT from_type, from_id, to_type, to_id, link_type, raw_json
            FROM links
            """,
            (),
            chunk,
        ):
            objs: list[AmoLink] = []
            for from_type, from_id, to_type, to_id, link_type, raw_json in rows:
                objs.append(
                    AmoLink(
                        from_type=from_type or "",
                        from_id=int(from_id),
                        to_type=to_type or "",
                        to_id=int(to_id),
                        link_type=link_type or "",
                        raw_json=_parse_json_cell(raw_json),
                    )
                )
            if not objs:
                continue
            with transaction.atomic():
                AmoLink.objects.bulk_create(
                    objs,
                    batch_size=chunk,
                    update_conflicts=True,
                    unique_fields=[
                        "from_type",
                        "from_id",
                        "to_type",
                        "to_id",
                        "link_type",
                    ],
                    update_fields=["raw_json"],
                )
            total += len(objs)
            self.stdout.write(f"  links batch: +{len(objs)} (total attempted {total})")
