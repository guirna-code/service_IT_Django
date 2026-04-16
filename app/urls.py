from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Authentication
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Users
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.user_add, name='user_add'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    
    # Machines
    path('machines/', views.machine_list, name='machine_list'),
    path('machines/add/', views.machine_add, name='machine_add'),
    path('machines/<int:machine_id>/edit/', views.machine_edit, name='machine_edit'),
    path('machines/<int:machine_id>/delete/', views.machine_delete, name='machine_delete'),
    
    # Interventions
    path('interventions/', views.intervention_list, name='intervention_list'),
    path('interventions/add/', views.intervention_add, name='intervention_add'),
    path('interventions/<int:intervention_id>/edit/', views.intervention_edit, name='intervention_edit'),
    path('interventions/<int:intervention_id>/delete/', views.intervention_delete, name='intervention_delete'),
    
    # Components
    path('components/', views.component_list, name='component_list'),
]
