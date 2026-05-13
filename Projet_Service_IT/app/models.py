from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
import qrcode
from io import BytesIO

from django.core.files import File

POLE_CHOICES = [
    ("INF", "Informatique"),
    ("RH", "Ressources Humaines"),
    ("PROD", "Production"),
    ("MKT", "Marketing"),
    ("FIN", "Finance"),
    ("AUTRE", "Autre")
]


class UtilisateurManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class Utilisateur(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("technician", "Technician"),
        
    )

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="technician",
        null=True,
        blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UtilisateurManager()

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
    numero_serie = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )
    type = models.CharField(
        max_length=20,
        choices=TypeMachine.choices,
        null=True,
        blank=True
    )
    pole = models.CharField(
        max_length=50,
        choices=POLE_CHOICES,
        default="INF",
        verbose_name="Pôle"
    )
    date_acquisition = models.DateField(null=True, blank=True)
    etat = models.CharField(
        max_length=20,
        choices=EtatMachine.choices,
        default=EtatMachine.FONCTIONNEL
    )
    enregistre_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    qr_code = models.ImageField(
    upload_to="qr_codes/",
    null=True,
    blank=True
)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.pole})"


class Composant(models.Model):
    class EtatComposant(models.TextChoices):
        OK = "OK", _("OK")
        FAIBLE = "FAIBLE", _("Faible")
        HS = "HS", _("Hors service")

    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=50, null=True, blank=True)
    numero_serie = models.CharField(max_length=100, null=True, blank=True)
    marque = models.CharField(max_length=100, null=True, blank=True)
    date_installation = models.DateField(null=True, blank=True)
    etat = models.CharField(
        max_length=20,
        choices=EtatComposant.choices,
        default=EtatComposant.OK
    )

    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name="composants"
    )

    def __str__(self):
        return f"{self.nom} - {self.machine.nom}"


class Affectation(models.Model):
    class StatutAffectation(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        RETURNED = "RETURNED", _("Retourné")

    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name="affectations"
    )
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="affectations"
    )
    pole = models.CharField(
        max_length=50,
        choices=POLE_CHOICES,
        default="INF",
        verbose_name="Pôle"
    )
    date_affectation = models.DateField()
    date_retour = models.DateField(null=True, blank=True)
    remarque = models.TextField(null=True, blank=True)
    statut = models.CharField(
        max_length=20,
        choices=StatutAffectation.choices,
        default=StatutAffectation.ACTIVE
    )

    class Meta:
        ordering = ["-date_affectation"]

    def __str__(self):
        user_name = self.utilisateur.email if self.utilisateur else "Non assigné"
        return f"{self.machine.nom} - {user_name} ({self.get_statut_display()})"

class RapportIntervention(models.Model):
    date_cloture = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    duree = models.PositiveIntegerField(
        verbose_name="Durée (min)",
        null=True,
        blank=True
    )
    redacteur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="rapports"
    )
    machine_concernee = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name="rapport_interventions",
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ["-date_cloture"]

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        if not self.qr_code:

            qr = qrcode.make(
            f"http://127.0.0.1:8000/machines/{self.id}/"
        )

            buffer = BytesIO()

            qr.save(buffer, format="PNG")

            file_name = f"machine_{self.id}.png"

            self.qr_code.save(
                file_name,
                File(buffer),
                save=False
        )

            super().save(update_fields=["qr_code"])

    def __str__(self):
        return f"Intervention - {self.machine_concernee}"
class RapportD_inventaire(models.Model):
    date_cloture = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    duree = models.PositiveIntegerField(
        verbose_name="Durée (min)",
        null=True,
        blank=True
    )
    redacteur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="rapports_inventaire"
    )
    machine_concernee = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name="inventaires",
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["-date_cloture"]

    def __str__(self):
        return f"Inventaire - {self.machine_concernee}"