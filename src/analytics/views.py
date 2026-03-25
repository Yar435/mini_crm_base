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
from analytics.cache_keys import make_process_graph_cache_key
from analytics.metrics import process_graph_build_seconds
from analytics.services.graph_builder import GraphMode, build_process_graph_from_params
from analytics.time_utils import parse_query_timestamp


class ProcessGraphView(APIView):
    permission_classes = [IsAuthenticated]

    CACHE_TIMEOUT_SECONDS = contract.CACHE_TIMEOUT_SECONDS

    @staticmethod
    def _parse_optional_float(
        value: str | None, *, field: str
    ) -> tuple[Optional[float], Optional[str]]:
        if value is None or value == "":
            return None, None
        err_msg = (
            contract.ERR_MIN_PRICE_INVALID if field == "min" else contract.ERR_MAX_PRICE_INVALID
        )
        try:
            v = float(value)
        except Exception:
            return None, err_msg
        if v < 0:
            return None, err_msg
        return v, None

    @extend_schema(
        tags=["Analytics"],
        summary="Граф процессов (микроаналитика)",
        description=(
            "Возвращает узлы (статусы воронки) и рёбра (переходы) с весами и метриками. "
            "Требуется JWT (Bearer). "
            "**as_of** — момент среза: целое число unix-времени (секунды) или ISO-8601 в UTC. "
            "**mode=replay_speed** — все переходы с начала истории до as_of. "
            "**mode=rolling_window** — только переходы в окне [as_of − window_minutes×60, as_of]; "
            "параметр **window_minutes** обязателен. "
            "**top_k** — число рёбер (1…500), по умолчанию 20. "
            "**min_price** / **max_price** — опционально: учитывать только лиды из таблицы `amo_leads` "
            "в этой воронке с заполненной ценой в диапазоне; лиды без записи в `amo_leads` при активном "
            "фильтре не попадают в выборку."
        ),
        parameters=[
            OpenApiParameter(
                name="pipeline_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Идентификатор воронки (amo pipeline id)",
            ),
            OpenApiParameter(
                name="as_of",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Unix timestamp (секунды) или ISO datetime (например 2025-01-01T00:00:00Z)",
            ),
            OpenApiParameter(
                name="mode",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="replay_speed (по умолчанию) | rolling_window",
            ),
            OpenApiParameter(
                name="window_minutes",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Только для rolling_window: ширина окна в минутах (>0)",
            ),
            OpenApiParameter(
                name="top_k",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description=f"Сколько рёбер вернуть (1…{contract.TOP_K_MAX}), по умолчанию {contract.TOP_K_DEFAULT}",
            ),
            OpenApiParameter(
                name="from_status_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Ограничить рёбра переходами только с этого статуса",
            ),
            OpenApiParameter(
                name="min_price",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Минимальная цена лида (фильтр по amo_leads), опционально",
            ),
            OpenApiParameter(
                name="max_price",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Максимальная цена лида (фильтр по amo_leads), опционально",
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiResponse(
                response=inline_serializer(
                    name="ProcessGraphValidationError",
                    fields={"detail": serializers.CharField()},
                ),
                description="Некорректные параметры запроса",
            ),
            401: OpenApiResponse(
                response=inline_serializer(
                    name="ProcessGraphUnauthorized",
                    fields={"detail": serializers.CharField()},
                ),
                description="Не авторизован (нет или невалидный JWT)",
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        pipeline_id = request.query_params.get("pipeline_id")
        as_of = request.query_params.get("as_of")
        mode = request.query_params.get("mode", "replay_speed")
        window_minutes = request.query_params.get("window_minutes")
        top_k = request.query_params.get("top_k", str(contract.TOP_K_DEFAULT))
        from_status_id = request.query_params.get("from_status_id")
        min_price_raw = request.query_params.get("min_price")
        max_price_raw = request.query_params.get("max_price")

        if not pipeline_id:
            return Response({"detail": _(contract.ERR_PIPELINE_ID_REQUIRED)}, status=400)
        if not as_of:
            return Response({"detail": _(contract.ERR_AS_OF_REQUIRED)}, status=400)

        try:
            pipeline_id_int = int(pipeline_id)
        except Exception:
            return Response({"detail": _(contract.ERR_PIPELINE_ID_INVALID)}, status=400)

        if mode not in contract.GRAPH_MODES:
            return Response({"detail": _(contract.ERR_MODE_INVALID)}, status=400)

        window_minutes_int: Optional[int] = None
        if window_minutes is not None and window_minutes != "":
            try:
                window_minutes_int = int(window_minutes)
            except Exception:
                return Response({"detail": _(contract.ERR_WINDOW_MINUTES_INVALID)}, status=400)

        try:
            top_k_int = int(top_k)
        except Exception:
            return Response({"detail": _(contract.ERR_TOP_K_INVALID)}, status=400)
        if top_k_int <= 0 or top_k_int > contract.TOP_K_MAX:
            return Response({"detail": _(contract.ERR_TOP_K_BOUNDS)}, status=400)

        from_status_id_int: Optional[int] = None
        if from_status_id not in (None, ""):
            try:
                from_status_id_int = int(from_status_id)
            except Exception:
                return Response({"detail": _(contract.ERR_FROM_STATUS_ID_INVALID)}, status=400)

        min_price, err = self._parse_optional_float(min_price_raw, field="min")
        if err:
            return Response({"detail": _(err)}, status=400)
        max_price, err = self._parse_optional_float(max_price_raw, field="max")
        if err:
            return Response({"detail": _(err)}, status=400)
        if min_price is not None and max_price is not None and min_price > max_price:
            return Response({"detail": _(contract.ERR_PRICE_RANGE_INVALID)}, status=400)

        if mode == "rolling_window" and window_minutes_int is None:
            return Response({"detail": _(contract.ERR_WINDOW_MINUTES_REQUIRED)}, status=400)

        try:
            as_of_ts = parse_query_timestamp(as_of)
        except Exception:
            return Response({"detail": _(contract.ERR_AS_OF_INVALID)}, status=400)

        cache_key = make_process_graph_cache_key(
            pipeline_id=pipeline_id_int,
            mode=mode,  # type: ignore[arg-type]
            as_of_ts=as_of_ts,
            window_minutes=window_minutes_int,
            top_k=top_k_int,
            from_status_id=from_status_id_int,
            min_price=min_price,
            max_price=max_price,
        )
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        t0 = time.perf_counter()
        result = build_process_graph_from_params(
            pipeline_id=pipeline_id_int,
            as_of=as_of,
            mode=mode,  # type: ignore[arg-type]
            window_minutes=window_minutes_int,
            top_k=top_k_int,
            from_status_id=from_status_id_int,
            min_price=min_price,
            max_price=max_price,
        )
        process_graph_build_seconds.observe(time.perf_counter() - t0)

        cache.set(cache_key, result, timeout=self.CACHE_TIMEOUT_SECONDS)
        return Response(result)
