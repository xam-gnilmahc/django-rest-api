from django.urls import include, path

urlpatterns = [
    path("", include("tutorials.urls")),
    path("schema_viewer/", include("schema_viewer.urls")),
]
