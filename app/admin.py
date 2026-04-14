from django.contrib import admin
from .models import Utilisateur, Machine, Composant, RapportIntervention

admin.site.register(Utilisateur)
admin.site.register(Machine)
admin.site.register(Composant)
admin.site.register(RapportIntervention)