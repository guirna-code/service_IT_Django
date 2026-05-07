from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    # Authentication
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Common
    path('', views.dashboard, name='dashboard'),

    # Admin
    path('admin/technicians/', views.manage_technicians, name='manage_technicians'),
    path('admin/machines/', views.machine_list_admin, name='machine_list_admin'),
    path('admin/machines/add/', views.add_machine, name='add_machine'),
    path('admin/report/', views.inventory_report, name='inventory_report'),

    # Technician
    path('tech/machines/', views.machine_list_tech, name='machine_list_tech'),
    path('tech/machines/<int:machine_id>/update/', views.update_machine_status, name='update_machine_status'),
    path('tech/interventions/add/', views.add_intervention, name='add_intervention'),
]
from django.urls import path
from . import views

app_name = 'app' # Assure-toi que cela correspond à tes redirects (ex: redirect('app:dashboard'))

urlpatterns = [
    # Authentification
    path('', views.user_login, name='login'), # La racine devient la page de login
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Interface ADMIN
    path('admin/technicians/', views.manage_technicians, name='manage_technicians'),
    path('admin/machines/add/', views.add_machine, name='add_machine'),
    path('admin/report/', views.inventory_report, name='inventory_report'),

    # Interface TECHNICIEN
    path('tech/machines/', views.machine_list_tech, name='machine_list_tech'),
    path('tech/machines/status/<int:machine_id>/', views.update_machine_status, name='update_machine_status'),
    path('tech/intervention/new/', views.add_intervention, name='add_intervention'),
]