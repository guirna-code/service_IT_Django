from io import BytesIO
import qrcode
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.files import File
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


POLE_CHOICES = [
    ("INF", "Informatique"),
    ("RH", "Ressources Humaines"),
    ("PROD", "Production"),
    ("MKT", "Marketing"),
]


class UtilisateurManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class Utilisateur(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("technician", "Technician"),
        ("client", "Client"),
    )

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="client")

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
        REPARATION = "REPARATION", _("Reparation")

    nom = models.CharField(max_length=100, verbose_name="Nom")
    numero_serie = models.CharField(max_length=100, unique=True, null=True, blank=True)
    type = models.CharField(max_length=20, choices=TypeMachine.choices, null=True, blank=True)
    pole = models.CharField(max_length=50, choices=POLE_CHOICES, default="INF", verbose_name="Pole")
    date_acquisition = models.DateField(null=True, blank=True)
    etat = models.CharField(
        max_length=20,
        choices=EtatMachine.choices,
        default=EtatMachine.FONCTIONNEL,
    )
    qr_code = models.ImageField(upload_to="qrcodes/", null=True, blank=True)

    enregistre_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["nom"]
        indexes = [
            models.Index(fields=["etat"], name="app_machine_etat_5ed9c9_idx"),
            models.Index(fields=["type"], name="app_machine_type_f7331f_idx"),
            models.Index(fields=["pole"], name="app_machine_pole_8c2b40_idx"),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.qr_code:
            detail_url = reverse("app:machine_pdf", args=[self.id])
            qr = qrcode.make(f"{settings.SITE_URL}{detail_url}")
            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            buffer.seek(0)

            file_name = f"machine_{self.id}.png"
            self.qr_code.save(file_name, File(buffer), save=False)

            super().save(update_fields=["qr_code"])

    def __str__(self):
        return f"{self.nom} ({self.pole})"


class Composant(models.Model):
    class EtatComposant(models.TextChoices):
        OK = "OK", "OK"
        FAIBLE = "FAIBLE", "Faible"
        HS = "HS", "Hors service"

    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=50, null=True, blank=True)
    marque = models.CharField(max_length=100, null=True, blank=True)
    numero_serie = models.CharField(max_length=100, null=True, blank=True)
    date_installation = models.DateField(null=True, blank=True)
    etat = models.CharField(
        max_length=20,
        choices=EtatComposant.choices,
        default=EtatComposant.OK,
    )
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name="composants",
    )

    def __str__(self):
        return f"{self.nom} - {self.machine.nom}"


class RapportIntervention(models.Model):
    class TypeIntervention(models.TextChoices):
        MAINTENANCE = "maintenance", _("Maintenance")
        REPARATION = "reparation", _("Reparation")
        INSTALLATION = "installation", _("Installation")

    class StatutIntervention(models.TextChoices):
        EN_COURS = "en_cours", _("En cours")
        TERMINE = "terminee", _("Terminee")
        ANNULEE = "annulee", _("Annulee")
        ECHOUE = "echec", _("Echec")

    date = models.DateField(null=True, blank=True)
    date_cloture = models.DateTimeField(null=True, blank=True)
    type = models.CharField(max_length=50, choices=TypeIntervention.choices, null=True, blank=True)
    statut = models.CharField(
        max_length=50,
        choices=StatutIntervention.choices,
        default=StatutIntervention.EN_COURS,
    )
    description = models.TextField(null=True, blank=True)
    duree = models.PositiveIntegerField(verbose_name="Duree (min)", null=True, blank=True)

    redacteur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="rapports",
    )
    technicien = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interventions_assignees",
    )
    machine_concernee = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name="interventions",
    )

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["statut"], name="app_rapport_statut_ba4064_idx"),
            models.Index(fields=["date"], name="app_rapport_date_4ee5a3_idx"),
        ]

    def __str__(self):
        return f"Intervention #{self.id} - {self.get_type_display() if self.type else 'N/A'}"

    @property
    def status_label(self):
        return self.get_statut_display()

    @property
    def machine(self):
        return self.machine_concernee

    @property
    def technicien_email(self):
        if self.technicien:
            return self.technicien.get_full_name() or self.technicien.email

        if self.redacteur:
            return self.redacteur.get_full_name() or self.redacteur.email

        return "-"
