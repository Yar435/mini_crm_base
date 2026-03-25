from django.db import models


class AmoPipeline(models.Model):
    """
    Пайплайн amoCRM.
    """

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    sort = models.IntegerField(null=True, blank=True)
    is_main = models.BooleanField(default=False)

    class Meta:
        db_table = "amo_pipelines"


class AmoStatus(models.Model):
    """
    Статус внутри пайплайна.
    """

    id = models.IntegerField(primary_key=True)
    pipeline = models.ForeignKey(
        AmoPipeline,
        to_field="id",
        on_delete=models.CASCADE,
        related_name="statuses",
    )
    name = models.CharField(max_length=255)
    sort = models.IntegerField(null=True, blank=True)
    is_final = models.BooleanField(default=False)

    class Meta:
        db_table = "amo_statuses"
        indexes = [
            models.Index(fields=["pipeline"]),
            models.Index(fields=["is_final"]),
        ]


class AmoLeadTransition(models.Model):
    """
    Переход лида между статусами (из amo events).
    """

    event_id = models.CharField(max_length=128, primary_key=True)
    lead_id = models.IntegerField(db_index=True)
    at = models.IntegerField(db_index=True)  # unix timestamp (seconds)
    by_user = models.IntegerField(null=True, blank=True)
    from_status = models.ForeignKey(
        AmoStatus,
        to_field="id",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transitions_from",
    )
    to_status = models.ForeignKey(
        AmoStatus,
        to_field="id",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transitions_to",
    )

    class Meta:
        db_table = "amo_lead_transitions"
        indexes = [
            models.Index(fields=["lead_id", "at"]),
            models.Index(fields=["at"]),
            models.Index(fields=["from_status", "at"]),
            models.Index(fields=["to_status", "at"]),
        ]


class AmoLead(models.Model):
    """
    Снимок лида из amo_entities (для фильтров аналитики и джойнов с переходами).
    """

    id = models.IntegerField(primary_key=True)
    pipeline = models.ForeignKey(
        AmoPipeline,
        to_field="id",
        on_delete=models.CASCADE,
        related_name="leads",
    )
    status = models.ForeignKey(
        AmoStatus,
        to_field="id",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
    )
    name = models.CharField(max_length=512, blank=True)
    price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    created_at = models.IntegerField(null=True, blank=True)
    updated_at = models.IntegerField(null=True, blank=True)
    responsible_user_id = models.IntegerField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    raw_json = models.JSONField(default=dict)

    class Meta:
        db_table = "amo_leads"
        indexes = [
            models.Index(fields=["pipeline", "price"]),
            models.Index(fields=["pipeline", "status"]),
        ]


class AmoTask(models.Model):
    """Задача из amo_entities."""

    id = models.IntegerField(primary_key=True)
    entity_type = models.CharField(max_length=32, blank=True)
    entity_id = models.IntegerField(null=True, blank=True)
    text = models.TextField(blank=True)
    is_completed = models.BooleanField(null=True, blank=True)
    complete_till = models.IntegerField(null=True, blank=True)
    created_at = models.IntegerField(null=True, blank=True)
    updated_at = models.IntegerField(null=True, blank=True)
    responsible_user_id = models.IntegerField(null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    result = models.TextField(blank=True)
    raw_json = models.JSONField(default=dict)

    class Meta:
        db_table = "amo_tasks"
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["responsible_user_id"]),
        ]


class AmoLink(models.Model):
    """Связь сущностей (leads/contacts/companies/...) из amo_entities."""

    id = models.BigAutoField(primary_key=True)
    from_type = models.CharField(max_length=32)
    from_id = models.IntegerField()
    to_type = models.CharField(max_length=32)
    to_id = models.IntegerField()
    link_type = models.CharField(max_length=64, blank=True)
    raw_json = models.JSONField(default=dict)

    class Meta:
        db_table = "amo_links"
        constraints = [
            models.UniqueConstraint(
                fields=["from_type", "from_id", "to_type", "to_id", "link_type"],
                name="amo_links_unique_edge",
            )
        ]
        indexes = [
            models.Index(fields=["from_type", "from_id"]),
            models.Index(fields=["to_type", "to_id"]),
        ]


class AmoSyncState(models.Model):
    """Watermarks для инкрементальной синхронизации с amoCRM API."""

    key = models.CharField(max_length=64, primary_key=True)
    watermark_updated_at = models.BigIntegerField(default=0)
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    class Meta:
        db_table = "amo_sync_state"

