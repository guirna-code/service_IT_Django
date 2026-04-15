from django.db import models
from django.contrib.auth.models import AbstractUser
import qrcode
import os
from django.conf import settings
class Utilisateur(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('technician', 'Technician'),
        ('client', 'Client'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

class Machine(models.Model):
    nom = models.CharField(max_length=100)
    numero_serie = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=20, choices=[
        ('PC', 'PC'),
        ('SERVEUR', 'Serveur'),
        ('IMPRIMANTE', 'Imprimante')
    ])
    date_acquisition = models.DateField()
    etat = models.CharField(max_length=20, choices=[
        ('FONCTIONNEL', 'F'),
        ('EN_PANNE', 'E'),
        ('REPARATION', 'R')
    ])
    qr_code_path = models.CharField(max_length=255)

    enregistre_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='machines_gerees'
    )

class Composant(models.Model):
    nom = models.CharField(max_length=100)
    capacite = models.CharField(max_length=50)
    type = models.CharField(max_length=50)

    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name='composants'
    )

class RapportIntervention(models.Model):
    date_cloture = models.DateTimeField()
    description = models.TextField()
    pieces_changees = models.CharField(max_length=255)
    duree = models.IntegerField()

    redacteur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='rapports_rediges'
    )

    machine_concernee = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name='interventions'
    )