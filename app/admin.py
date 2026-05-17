from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Utilisateur, Machine, Composant, RapportIntervention


# ---------------- UTILISATEUR ----------------
@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    model = Utilisateur

    list_display = ("id", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Informations personnelles", {"fields": ("first_name", "last_name", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates importantes", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "role", "is_staff", "is_superuser", "is_active"),
        }),
    )


# ---------------- MACHINE ----------------
@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ("id", "nom", "numero_serie", "type", "pole", "etat", "enregistre_par")
    list_filter = ("type", "pole", "etat")
    search_fields = ("nom", "numero_serie")


# ---------------- COMPOSANT ----------------
@admin.register(Composant)
class ComposantAdmin(admin.ModelAdmin):
    list_display = ("id", "nom", "type", "etat", "machine")
    list_filter = ("type", "etat")
    search_fields = ("nom", "type", "machine__nom")


# ---------------- RAPPORT INTERVENTION ----------------
@admin.register(RapportIntervention)
class RapportInterventionAdmin(admin.ModelAdmin):
    list_display = ("id", "machine_concernee", "redacteur", "technicien", "type", "statut", "date", "duree")
    list_filter = ("type", "statut", "date")
    search_fields = (
        "machine_concernee__nom",
        "machine_concernee__numero_serie",
        "redacteur__email",
        "technicien__email",
        "description",
    )
