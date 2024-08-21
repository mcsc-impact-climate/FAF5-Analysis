from django.urls import path
from . import views

urlpatterns = [
    path("transportation/", views.index, name="transportation-app"),
    path("get_geojsons/", views.get_geojsons, name="get-geojsons"),
    path("get_uploaded_geojsons/", views.get_uploaded_geojsons, name="get-uploaded-geojsons"),
    path("get_geojson/", views.get_geojson, name="get-geojson"),
    path("get_geojson/<geojson_name>/", views.get_geojson, name="get-geojson"),
]
