from __future__ import annotations

import argparse

from django.conf import settings
from django.core.management.base import BaseCommand

from analytics.services.incremental_leads_sync import reset_leads_watermark, run_incremental_leads_sync


class Command(BaseCommand):
    help = (
        "Incremental sync of leads from amoCRM API v4 into AmoLead. "
        "Requires AMOCRM_SUBDOMAIN and AMOCRM_ACCESS_TOKEN (or pass --subdomain / --token). "
        "Pipelines/statuses must exist (sync_amo_transitions first)."
    )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--subdomain", default=None, help="Account subdomain (default: AMOCRM_SUBDOMAIN)")
        parser.add_argument("--token", default=None, help="Long-lived token (default: AMOCRM_ACCESS_TOKEN)")
        parser.add_argument(
            "--reset-watermark",
            action="store_true",
            help="Reset stored watermark to 0 before run (next run recomputes from DB or last week)",
        )

    def handle(self, *args, **options):
        if options["reset_watermark"]:
            reset_leads_watermark(0)
            self.stdout.write(self.style.NOTICE("Watermark reset."))

        subdomain = (options["subdomain"] or getattr(settings, "AMOCRM_SUBDOMAIN", "") or "").strip()
        token = (options["token"] or getattr(settings, "AMOCRM_ACCESS_TOKEN", "") or "").strip()
        if not subdomain or not token:
            raise SystemExit(
                "Set AMOCRM_SUBDOMAIN and AMOCRM_ACCESS_TOKEN in environment or pass --subdomain / --token"
            )

        out = run_incremental_leads_sync(subdomain=subdomain, token=token)
        if not out.get("ok"):
            self.stdout.write(self.style.ERROR(out.get("error", "unknown")))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS(str(out)))
