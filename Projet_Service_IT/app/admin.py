from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Utilisateur, Machine, Composant, RapportIntervention , RapportD_inventaire


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    model = Utilisateur
    list_display = ("id", "email", "role", "is_staff", "is_superuser", "is_active")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("email",)
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "role", "is_staff", "is_superuser", "is_active"),
        }),
    )


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ("id", "nom", "numero_serie", "type", "pole", "etat", "enregistre_par")
    list_filter = ("type", "pole", "etat")
    search_fields = ("nom", "numero_serie")


@admin.register(Composant)
class ComposantAdmin(admin.ModelAdmin):
    list_display = ("id", "nom", "type", "machine")
    search_fields = ("nom", "type", "machine__nom")


@admin.register(RapportIntervention)
class RapportInterventionAdmin(admin.ModelAdmin):
    list_display = ("id", "machine_concernee", "redacteur", "date_cloture", "duree")
    list_filter = ("date_cloture",)
    search_fields = ("machine_concernee__nom", "redacteur__email", "description")

@admin.register(RapportD_inventaire)
class RapportD_inventaireAdmin(admin.ModelAdmin):
    list_display = ("id", "machine_concernee", "redacteur", "date_cloture", "duree")
    list_filter = ("date_cloture",)
    search_fields = ("machine_concernee__nom", "redacteur__email", "description")