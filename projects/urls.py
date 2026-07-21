from django.urls import path

from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('new/', views.project_create, name='project_create'),
    path('artist/<uuid:token_artist>/', views.artist_workspace, name='artist_workspace'),
    path('artist/<uuid:token_artist>/category/add/', views.add_category, name='add_category'),
    path('artist/<uuid:token_artist>/category/<int:category_id>/change-request/', views.add_change_request, name='add_change_request'),
    path('artist/<uuid:token_artist>/category/<int:category_id>/rename/', views.rename_category, name='rename_category'),
    path('artist/<uuid:token_artist>/category/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    path('artist/<uuid:token_artist>/category/<int:category_id>/restore/', views.restore_category, name='restore_category'),
    path('artist/<uuid:token_artist>/change-request/<int:change_request_id>/status/', views.update_change_request_status, name='update_change_request_status'),
    path('artist/<uuid:token_artist>/draft-image/', views.upload_draft_image, name='upload_draft_image'),
    path('artist/<uuid:token_artist>/draft-image/<int:image_id>/delete/', views.delete_draft_image, name='delete_draft_image'),
    path('client/<uuid:token_client>/', views.client_view, name='client_view'),
    path('client/<uuid:token_client>/category/<int:category_id>/change-request/', views.client_add_change_request, name='client_add_change_request'),
    path('client/<uuid:token_client>/change-request/<int:change_request_id>/approve/', views.client_approve_change_request, name='client_approve_change_request'),
    path('client/<uuid:token_client>/change-request/<int:change_request_id>/cancel/', views.client_cancel_change_request, name='client_cancel_change_request'),
    path('scope/<uuid:token>/export/', views.export_pdf, name='export_pdf'),
]
