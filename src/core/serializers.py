from rest_framework import serializers


class DetailResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class HealthChecksSerializer(serializers.Serializer):
    db = serializers.CharField()
    redis = serializers.CharField()
    # Делаем поле числовым (секунды), допускаем null, если тика не было
    celery_beat_age_sec = serializers.FloatField(required=False, allow_null=True)


class HealthResponseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["ok", "fail"])
    checks = HealthChecksSerializer()
