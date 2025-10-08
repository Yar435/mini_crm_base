from rest_framework import serializers, viewsets

from .models import Deal, Manager


class ManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manager
        fields = "__all__"


class DealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deal
        fields = "__all__"


class ManagerViewSet(viewsets.ModelViewSet):
    queryset = Manager.objects.all()
    serializer_class = ManagerSerializer


class DealViewSet(viewsets.ModelViewSet):
    queryset = Deal.objects.select_related("client", "manager").all()
    serializer_class = DealSerializer
