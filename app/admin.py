from django.db import models
from django.utils import timezone
import qrcode
import os
from django.conf import settings


# -----------------------------
# Utilisateur
# -----------------------------
class Utilisateur(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('TECHNICIEN', 'Technicien'),
    ]

    username = models.CharField(max_length=150)
    departement = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # 🔹 Méthodes métier
    def est_admin(self):
        return self.role == 'ADMIN'

    def est_technicien(self):
        return self.role == 'TECHNICIEN'

    def nombre_interventions(self):
        return self.rapports.count()

    def derniere_intervention(self):
        return self.rapports.order_by('-date_cloture').first()

    def __str__(self):
        return f"{self.username} ({self.role})"


# -----------------------------
# Machine
# -----------------------------
class Machine(models.Model):
    TYPE_CHOICES = [
        ('PC', 'PC'),
        ('SERVEUR', 'Serveur'),
        ('IMPRIMANTE', 'Imprimante'),
    ]

    ETAT_CHOICES = [
        ('FONCTIONNEL', 'Fonctionnel'),
        ('EN_PANNE', 'En panne'),
        ('REPARATION', 'Réparation'),
    ]

    nom = models.CharField(max_length=100)
    numero_serie = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    date_acquisition = models.DateField()
    etat = models.CharField(max_length=20, choices=ETAT_CHOICES)
    qr_code_path = models.CharField(max_length=255, blank=True, null=True)

    # 🔹 Génération QR Code
    def generer_qr(self):
        data = f"{self.nom} | {self.numero_serie}"

        qr = qrcode.make(data)

        folder = os.path.join(settings.MEDIA_ROOT, "qr_codes")
        os.makedirs(folder, exist_ok=True)

        filename = f"machine_{self.id}.png"
        filepath = os.path.join(folder, filename)

        qr.save(filepath)

        self.qr_code_path = f"qr_codes/{filename}"
        self.save()

    # 🔹 Modifier état
    def modifier_etat(self, nouvel_etat):
        if nouvel_etat not in dict(self.ETAT_CHOICES):
            raise ValueError("Etat invalide")
        self.etat = nouvel_etat
        self.save()

    # 🔹 Vérifications utiles
    def est_en_panne(self):
        return self.etat == 'EN_PANNE'

    def est_fonctionnelle(self):
        return self.etat == 'FONCTIONNEL'

    # 🔹 Statistiques
    def nombre_interventions(self):
        return self.rapports.count()

    def derniere_intervention(self):
        return self.rapports.order_by('-date_cloture').first()

    def duree_totale_interventions(self):
        return sum(r.duree for r in self.rapports.all())

    def __str__(self):
        return f"{self.nom} ({self.numero_serie})"


# -----------------------------
# Composant
# -----------------------------
class Composant(models.Model):
    nom = models.CharField(max_length=100)
    capacite = models.CharField(max_length=100)
    type = models.CharField(max_length=50)

    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name="composants"
    )

    # 🔹 Méthodes métier
    def est_critique(self):
        return self.type in ['CPU', 'Disque']

    def description_complete(self):
        return f"{self.nom} - {self.type} ({self.capacite})"

    def appartient_a_machine(self):
        return self.machine.nom

    def __str__(self):
        return self.description_complete()


# -----------------------------
# Rapport d'intervention
# -----------------------------
class RapportIntervention(models.Model):
    date_cloture = models.DateTimeField(default=timezone.now)
    description = models.TextField()
    pieces_changees = models.CharField(max_length=255)
    duree = models.IntegerField(help_text="Durée en minutes")

    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="rapports"
    )

    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name="rapports"
    )

    # 🔹 Méthodes métier
    def est_longue(self):
        return self.duree > 120

    def est_courte(self):
        return self.duree < 30

    def resume(self):
        return f"{self.utilisateur.username} a réparé {self.machine.nom}"

    def changer_machine(self, nouvelle_machine):
        self.machine = nouvelle_machine
        self.save()

    def ajouter_piece(self, piece):
        if self.pieces_changees:
            self.pieces_changees += f", {piece}"
        else:
            self.pieces_changees = piece
        self.save()

    def duree_en_heures(self):
        return round(self.duree / 60, 2)

    def __str__(self):
        return f"Rapport #{self.id} - {self.machine.nom}"