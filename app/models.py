from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import qrcode
import os

POLE_CHOICES = [
    ('INF', 'Informatique'),
    ('RH', 'Ressources Humaines'),
    ('PROD', 'Production'),
    ('MKT', 'Marketing'),
]

class Utilisateur(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('technician', 'Technician'),
        ('client', 'Client'),
    )
    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class Machine(models.Model):
    class TypeMachine(models.TextChoices):
        PC = "PC", _("PC")
        SERVEUR = "SERVEUR", _("Serveur")
        IMPRIMANTE = "IMPRIMANTE", _("Imprimante")

    class EtatMachine(models.TextChoices):
        FONCTIONNEL = "FONCTIONNEL", _("Fonctionnel")
        EN_PANNE = "EN_PANNE", _("En panne")
        REPARATION = "REPARATION", _("Réparation")

    nom = models.CharField(max_length=100, verbose_name="Nom")
    numero_serie = models.CharField(max_length=100, unique=True, null=True, blank=True)
    type = models.CharField(max_length=20, choices=TypeMachine.choices, null=True, blank=True)

    pole = models.CharField(
        max_length=50,
        choices=POLE_CHOICES,
        default='INF',
        verbose_name="Pôle"
    )

    date_acquisition = models.DateField(null=True, blank=True)
    etat = models.CharField(max_length=20, choices=EtatMachine.choices, default=EtatMachine.FONCTIONNEL)
    enregistre_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.pole})"


class Composant(models.Model):
    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=50, null=True, blank=True)

    # ✅ CORRECTION ICI
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name="composants",
        default=1
    )

    def __str__(self):
        return f"{self.nom} - {self.machine.nom}"


class RapportIntervention(models.Model):
    date_cloture = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    duree = models.PositiveIntegerField(verbose_name="Durée (min)", null=True, blank=True)
    redacteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="rapports")
    machine_concernee = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name="interventions")
machine_concernee = models.ForeignKey(
    Machine,
    on_delete=models.CASCADE,
    related_name="interventions",
    null=True,
    blank=True
)