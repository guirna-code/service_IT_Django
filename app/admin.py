from django.contrib import admin

from .models import Composant, Machine, RapportIntervention, Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ("email", "role", "is_staff", "is_active")
    search_fields = ("email",)
    ordering = ("email",)


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ("nom", "numero_serie", "type", "etat", "date_acquisition", "enregistre_par")
    search_fields = ("nom", "numero_serie")
    list_filter = ("type", "etat")


@admin.register(Composant)
class ComposantAdmin(admin.ModelAdmin):
    list_display = ("nom", "type", "capacite", "machine")
    search_fields = ("nom", "type")


@admin.register(RapportIntervention)
class RapportInterventionAdmin(admin.ModelAdmin):
    list_display = ("machine_concernee", "redacteur", "date_cloture", "duree")
    search_fields = ("description",)
    list_filter = ("date_cloture",)