from django.urls import path

from . import views


app_name = "app"

urlpatterns = [
    # Auth
    path("login/", views.user_login, name="login"),
    path("accounts/login/", views.user_login, name="accounts_login"),
    path("logout/", views.user_logout, name="logout"),

    # Dashboard
    path("", views.dashboard, name="dashboard"),

    # Admin
    path("dashboard/admin/technicians/", views.manage_technicians, name="manage_technicians"),
    path("dashboard/admin/machines/", views.machine_list_admin, name="machine_list_admin"),
    path("dashboard/admin/machines/add/", views.add_machine, name="add_machine"),
    path("dashboard/admin/machines/<int:machine_id>/edit/", views.edit_machine, name="edit_machine"),
    path("dashboard/admin/machines/<int:machine_id>/delete/", views.delete_machine, name="delete_machine"),
    path("dashboard/admin/report/", views.inventory_report, name="inventory_report"),
    path("dashboard/admin/export-pdf/", views.export_inventory_pdf, name="export_inventory_pdf"),
    path("dashboard/admin/components/", views.component_list, name="component_list"),
    path("dashboard/admin/components/add/", views.add_component, name="add_component"),
    path("dashboard/admin/components/<int:pk>/edit/", views.edit_component, name="edit_component"),
    path("dashboard/admin/components/<int:pk>/delete/", views.delete_component, name="delete_component"),

    # Machines shared by admin and technician
    path("machines/<int:machine_id>/", views.machine_detail, name="machine_detail"),

    # Technician
    path("dashboard/tech/machines/", views.machine_list_tech, name="machine_list_tech"),
    path("dashboard/tech/machines/<int:machine_id>/update/", views.update_machine_status, name="update_machine_status",),
    path("dashboard/tech/interventions/", views.intervention_list, name="intervention_list"),
    path("dashboard/tech/interventions/add/", views.add_intervention, name="add_intervention"),
    path("machines/<int:machine_id>/pdf/", views.machine_pdf, name="machine_pdf"),
]
