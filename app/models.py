from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UtilisateurManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")

        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", Utilisateur.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Le superuser doit avoir is_staff=True")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Le superuser doit avoir is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class Utilisateur(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", _("Admin")
        TECHNICIAN = "technician", _("Technician")
        CLIENT = "client", _("Client")

    username = None
    email = models.EmailField(unique=True, verbose_name="Email")
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT,
        verbose_name="Rôle",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UtilisateurManager()

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["email"]

    def __str__(self):
        full_name = self.get_full_name().strip()
        return full_name if full_name else self.email


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
        verbose_name="Numéro de série",
    )
    type = models.CharField(
        max_length=20,
        choices=TypeMachine.choices,
        verbose_name="Type",
    )
    date_acquisition = models.DateField(verbose_name="Date d'acquisition")
    etat = models.CharField(
        max_length=20,
        choices=EtatMachine.choices,
        default=EtatMachine.FONCTIONNEL,
        verbose_name="État",
    )
    qr_code_path = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Chemin du QR code",
    )
    enregistre_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="machines_gerees",
        verbose_name="Enregistré par",
    )

    class Meta:
        verbose_name = "Machine"
        verbose_name_plural = "Machines"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} - {self.numero_serie}"


class Composant(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Nom")
    capacite = models.CharField(max_length=50, verbose_name="Capacité")
    type = models.CharField(max_length=50, verbose_name="Type")
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name="composants",
        verbose_name="Machine",
    )

    class Meta:
        verbose_name = "Composant"
        verbose_name_plural = "Composants"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.machine.nom})"


class RapportIntervention(models.Model):
    date_cloture = models.DateTimeField(verbose_name="Date de clôture")
    description = models.TextField(verbose_name="Description")
    pieces_changees = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Pièces changées",
    )
    duree = models.PositiveIntegerField(verbose_name="Durée (minutes)")
    redacteur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="rapports_rediges",
        verbose_name="Rédacteur",
    )
    machine_concernee = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name="interventions",
        verbose_name="Machine concernée",
    )

    class Meta:
        verbose_name = "Rapport d'intervention"
        verbose_name_plural = "Rapports d'intervention"
        ordering = ["-date_cloture"]

    def __str__(self):
        return f"Intervention sur {self.machine_concernee.nom} - {self.date_cloture:%d/%m/%Y %H:%M}"