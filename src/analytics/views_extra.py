"""Дополнительные read-only endpoint'ы аналитики (воронка, переходы по пользователям)."""

from __future__ import annotations

import time
from typing import Optional

from django.core.cache import cache
from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

import analytics.api_contract as contract
from analytics.cache_keys import make_pipeline_funnel_cache_key, make_transitions_by_user_cache_key
from analytics.metrics import process_graph_build_seconds
from analytics.services.pipeline_insights import build_pipeline_funnel, build_transitions_by_user
from analytics.time_utils import parse_query_timestamp


class PipelineFunnelView(APIView):
    permission_classes = [IsAuthenticated]
    CACHE_TIMEOUT_SECONDS = min(300, contract.CACHE_TIMEOUT_SECONDS)

    @extend_schema(
        tags=["Analytics"],
        summary="Сводка лидов по статусам воронки",
        description=(
            "Подсчёт `AmoLead` по `status_id` для указанной воронки. "
            "Снимок соответствует текущим данным в БД после импорта (не исторический срез на `as_of`)."
        ),
        parameters=[
            OpenApiParameter(
                name="pipeline_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
            ),
            OpenApiParameter(
                name="include_deleted",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Учитывать удалённые лиды (is_deleted), по умолчанию false",
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiResponse(
                response=inline_serializer(
                    name="FunnelValidationError",
                    fields={"detail": serializers.CharField()},
                ),
                description="Некорректные параметры",
            ),
            401: OpenApiResponse(
                response=inline_serializer(
                    name="FunnelUnauthorized",
                    fields={"detail": serializers.CharField()},
                ),
                description="Не авторизован",
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        pipeline_id = request.query_params.get("pipeline_id")
        inc = request.query_params.get("include_deleted", "false").lower() in (
            "1",
            "true",
            "yes",
        )
        if not pipeline_id:
            return Response({"detail": _("pipeline_id is required")}, status=400)
        try:
            pid = int(pipeline_id)
        except Exception:
            return Response({"detail": _("pipeline_id must be int")}, status=400)

        cache_key = make_pipeline_funnel_cache_key(pipeline_id=pid, include_deleted=inc)
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        t0 = time.perf_counter()
        data = build_pipeline_funnel(pipeline_id=pid, include_deleted=inc)
        process_graph_build_seconds.observe(time.perf_counter() - t0)
        cache.set(cache_key, data, timeout=self.CACHE_TIMEOUT_SECONDS)
        return Response(data)


BY_USER_TOP_K_DEFAULT = 50
BY_USER_TOP_K_MAX = 500


class TransitionsByUserView(APIView):
    permission_classes = [IsAuthenticated]
    CACHE_TIMEOUT_SECONDS = min(300, contract.CACHE_TIMEOUT_SECONDS)

    @extend_schema(
        tags=["Analytics"],
        summary="Переходы по пользователям (агрегат)",
        description=(
            "Считает число переходов `AmoLeadTransition` в интервале времени "
            "[from_ts, to_ts] (unix секунды или ISO), только по статусам выбранной воронки."
        ),
        parameters=[
            OpenApiParameter(
                name="pipeline_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
            ),
            OpenApiParameter(
                name="from_ts",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Начало интервала (unix секунды или ISO datetime UTC)",
            ),
            OpenApiParameter(
                name="to_ts",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Конец интервала (unix секунды или ISO datetime UTC)",
            ),
            OpenApiParameter(
                name="top_k",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description=f"Сколько пользователей в топе (1…{BY_USER_TOP_K_MAX}), по умолчанию {BY_USER_TOP_K_DEFAULT}",
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiResponse(
                response=inline_serializer(
                    name="ByUserValidationError",
                    fields={"detail": serializers.CharField()},
                ),
                description="Некорректные параметры",
            ),
            401: OpenApiResponse(
                response=inline_serializer(
                    name="ByUserUnauthorized",
                    fields={"detail": serializers.CharField()},
                ),
                description="Не авторизован",
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        pipeline_id = request.query_params.get("pipeline_id")
        from_ts_raw = request.query_params.get("from_ts")
        to_ts_raw = request.query_params.get("to_ts")
        top_k_raw = request.query_params.get("top_k", str(BY_USER_TOP_K_DEFAULT))

        if not pipeline_id:
            return Response({"detail": _("pipeline_id is required")}, status=400)
        if not from_ts_raw or not to_ts_raw:
            return Response({"detail": _("from_ts and to_ts are required")}, status=400)

        try:
            pid = int(pipeline_id)
        except Exception:
            return Response({"detail": _("pipeline_id must be int")}, status=400)

        try:
            from_ts = parse_query_timestamp(from_ts_raw)
            to_ts = parse_query_timestamp(to_ts_raw)
        except Exception:
            return Response(
                {"detail": _("from_ts and to_ts must be unix timestamp or ISO datetime")},
                status=400,
            )

        try:
            top_k = int(top_k_raw)
        except Exception:
            return Response({"detail": _("top_k must be int")}, status=400)
        if top_k <= 0 or top_k > BY_USER_TOP_K_MAX:
            return Response({"detail": _("top_k out of bounds")}, status=400)

        cache_key = make_transitions_by_user_cache_key(
            pipeline_id=pid, from_ts=from_ts, to_ts=to_ts, top_k=top_k
        )
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        t0 = time.perf_counter()
        try:
            data = build_transitions_by_user(
                pipeline_id=pid, from_ts=from_ts, to_ts=to_ts, top_k=top_k
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
        process_graph_build_seconds.observe(time.perf_counter() - t0)
        cache.set(cache_key, data, timeout=self.CACHE_TIMEOUT_SECONDS)
        return Response(data)
