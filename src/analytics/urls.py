from django.urls import path

from .views import ProcessGraphView
from .views_extra import PipelineFunnelView, TransitionsByUserView

urlpatterns = [
    path("process-graph/", ProcessGraphView.as_view(), name="process-graph"),
    path("pipeline-funnel/", PipelineFunnelView.as_view(), name="pipeline-funnel"),
    path("transitions-by-user/", TransitionsByUserView.as_view(), name="transitions-by-user"),
]

