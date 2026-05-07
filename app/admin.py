
from django.contrib import admin
from .models import Utilisateur, Machine, Composant, RapportIntervention



# ---------------- UTILISATEUR ----------------
@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'role')
    list_filter = ('role',)   # ❌ enlève departement si erreur
    search_fields = ('username',)


# ---------------- MACHINE ----------------
@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'numero_serie', 'type', 'etat')
    list_filter = ('type', 'etat')
    search_fields = ('nom', 'numero_serie')
    
# ---------------- COMPOSANT ----------------
@admin.register(Composant)
class ComposantAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'type', 'machine')
    search_fields = ('nom',)


# ---------------- RAPPORT ----------------
@admin.register(RapportIntervention)
class RapportInterventionAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_machine', 'get_utilisateur', 'date_cloture', 'duree')

    def get_machine(self, obj):
        return obj.machine.nom
    get_machine.admin_order_field = 'machine'
    get_machine.short_description = 'Machine'

    def get_utilisateur(self, obj):
        return obj.utilisateur.username
    get_utilisateur.admin_order_field = 'utilisateur'
    get_utilisateur.short_description = 'Technicien'

