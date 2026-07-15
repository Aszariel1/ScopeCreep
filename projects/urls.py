from django.urls import path

from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_create, name='project_create'),
    path('artist/<uuid:token_artist>/', views.artist_workspace, name='artist_workspace'),
    path('artist/<uuid:token_artist>/category/<int:category_id>/change-request/', views.add_change_request, name='add_change_request'),
    path('artist/<uuid:token_artist>/change-request/<int:change_request_id>/status/', views.update_change_request_status, name='update_change_request_status'),
    path('artist/<uuid:token_artist>/draft-image/', views.upload_draft_image, name='upload_draft_image'),
    path('client/<uuid:token_client>/', views.client_view, name='client_view'),
]
