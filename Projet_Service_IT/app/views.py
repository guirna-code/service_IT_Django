from django.http import HttpResponse

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Utilisateur, Machine, RapportIntervention, Composant, Affectation, File


def is_admin(user):
    return user.is_authenticated and getattr(user, "role", None) == "admin"


def is_technician(user):
    return user.is_authenticated and getattr(user, "role", None) == "technician"
def is_admin_or_technician(user):
    return user.is_authenticated and user.role in ["admin", "technician"]

def user_login(request):
    if request.user.is_authenticated:
        return redirect("app:dashboard")

    if request.method == "POST":
        identifier = request.POST.get("username") or request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, email=identifier, password=password)


        if user is not None:
            auth_login(request, user)
            return redirect("app:dashboard")

        messages.error(request, "Email ou mot de passe incorrect.")

    return render(request, "app/login.html")


@login_required
def user_logout(request):
    auth_logout(request)
    return redirect("app:login")


@login_required
def dashboard(request):
    total_machines = Machine.objects.count()
    total_interventions = RapportIntervention.objects.count()
    total_technicians = Utilisateur.objects.filter(role="technician").count()

    machines_functional = Machine.objects.filter(etat="FONCTIONNEL").count()
    machines_repair = Machine.objects.filter(etat="REPARATION").count()
    machines_failed = Machine.objects.filter(etat="EN_PANNE").count()

    machines_failed_percent = 0
    if total_machines > 0:
        machines_failed_percent = int((machines_failed / total_machines) * 100)

    recent_interventions = RapportIntervention.objects.select_related(
        "machine_concernee",
        "redacteur"
    ).order_by("-id")[:5]

    machine_chart_data = [
        machines_functional,
        machines_repair,
        machines_failed,
    ]

    context = {
        "machine_chart_data": machine_chart_data,
        "page_title": "Tableau de bord",
        "total_machines": total_machines,
        "total_interventions": total_interventions,
        "total_technicians": total_technicians,
        "machines_functional": machines_functional,
        "machines_repair": machines_repair,
        "machines_failed": machines_failed,
        "machines_failed_percent": machines_failed_percent,
        "recent_interventions": recent_interventions,
    }

    return render(request, "app/dashboard.html", context)

@login_required
@user_passes_test(is_admin)
def machine_list_admin(request):
    machines = Machine.objects.all().order_by("-id")

    q = request.GET.get("q")
    machine_type = request.GET.get("type")
    etat = request.GET.get("etat")

    if q:
        machines = machines.filter(
            Q(nom__icontains=q) | Q(numero_serie__icontains=q)
        )

    if machine_type:
        machines = machines.filter(type=machine_type)

    if etat:
        machines = machines.filter(etat=etat)

    paginator = Paginator(machines, 8)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "app/admin/machine_list.html", {
        "page_title": "Gestion des machines",
        "machines": page_obj,
        "page_obj": page_obj,
    })


@login_required
@user_passes_test(is_admin)
def manage_technicians(request):
    techs = Utilisateur.objects.filter(role="technician")

    return render(request, "app/admin/tech_list.html", {
        "page_title": "Gestion des techniciens",
        "techs": techs,
    })



@login_required
@user_passes_test(is_admin)
def add_machine(request):
    if request.method == "POST":
        Machine.objects.create(
            nom=request.POST.get("nom"),
            numero_serie=request.POST.get("numero_serie"),
            type=request.POST.get("type"),
            pole=request.POST.get("pole"),
            date_acquisition=request.POST.get("date_acquisition") or None,
            etat=request.POST.get("etat") or "FONCTIONNEL",
            enregistre_par=request.user,
        )

        messages.success(request, "Machine ajoutée avec succès.")
        return redirect("app:machine_list_admin")

    return render(request, "app/admin/machine_add.html", {
        "page_title": "Ajouter une machine",
    })


@login_required
@user_passes_test(is_admin)
def inventory_report(request):
    machines = Machine.objects.all()

    stats = {
        "total": machines.count(),
        "fonctionnel": machines.filter(etat="FONCTIONNEL").count(),
        "maintenance": machines.filter(etat="REPARATION").count(),
        "panne": machines.filter(etat="EN_PANNE").count(),
    }

    return render(request, "app/admin/report.html", {
        "page_title": "Rapport d'inventaire",
        "stats": stats,
        "machines": machines,
    })


@login_required
@user_passes_test(is_technician)
def machine_list_tech(request):
    machines = Machine.objects.all().order_by("-id")

    q = request.GET.get("q")
    machine_type = request.GET.get("type")
    etat = request.GET.get("etat")

    if q:
        machines = machines.filter(
            Q(nom__icontains=q) | Q(numero_serie__icontains=q)
        )

    if machine_type:
        machines = machines.filter(type=machine_type)

    if etat:
        machines = machines.filter(etat=etat)

    return render(request, "app/tech/machine_list.html", {
        "page_title": "Liste des machines",
        "machines": machines,
    })


@login_required
@user_passes_test(is_technician)
def update_machine_status(request, machine_id):
    machine = get_object_or_404(Machine, id=machine_id)

    if request.method == "POST":
        new_etat = request.POST.get("etat")

        if new_etat:
            machine.etat = new_etat
            machine.save()
            messages.success(request, f"État de la machine {machine.nom} mis à jour.")

        return redirect("app:machine_list_tech")

    return render(request, "app/tech/update_status.html", {
        "page_title": "Modifier état machine",
        "machine": machine,
    })

@login_required
@user_passes_test(is_admin)
def edit_machine(request, machine_id):
    machine = get_object_or_404(Machine, id=machine_id)

    if request.method == "POST":
        machine.nom = request.POST.get("nom")
        machine.numero_serie = request.POST.get("numero_serie")
        machine.type = request.POST.get("type")
        machine.pole = request.POST.get("pole")
        machine.date_acquisition = request.POST.get("date_acquisition") or None
        machine.etat = request.POST.get("etat") or "FONCTIONNEL"
        machine.save()

        messages.success(request, "Machine modifiée avec succès.")
        return redirect("app:machine_detail", machine_id=machine.id)

    return render(request, "app/admin/machine_edit.html", {
        "page_title": "Modifier une machine",
        "machine": machine,
    })


@login_required
@user_passes_test(is_admin_or_technician)
def add_intervention(request):
    if request.method == "POST":
        machine_pk = request.POST.get("machine")
        machine = get_object_or_404(Machine, pk=machine_pk)

        RapportIntervention.objects.create(
            machine_concernee=machine,
            redacteur=request.user,
            description=request.POST.get("description"),
        )

        messages.success(request, "Rapport d'intervention créé avec succès.")
        return redirect("app:dashboard")

    machines = Machine.objects.all()

    return render(request, "app/tech/intervention_add.html", {
    "page_title": "Rédiger une intervention",
    "machines": machines,
})



@login_required
@user_passes_test(is_admin)
def add_inventory_report(request):
    return inventory_report(request)


@login_required
@user_passes_test(is_admin_or_technician)
def intervention_list(request):
    interventions = RapportIntervention.objects.select_related(
        "machine_concernee",
        "redacteur"
    ).order_by("-id")

    return render(request, "app/tech/intervention_list.html", {
    "page_title": "Liste des interventions",
    "interventions": interventions,
})


@login_required
@user_passes_test(is_admin)
def machine_detail(request, machine_id):
    machine = get_object_or_404(Machine, id=machine_id)

    interventions = RapportIntervention.objects.filter(
        machine_concernee=machine
    ).select_related("redacteur").order_by("-id")

    composants = Composant.objects.filter(machine=machine).order_by("nom")

    context = {
        "page_title": f"Machine • {machine.nom}",
        "machine": machine,
        "interventions": interventions,
        "composants": composants,
    }

    return render(request, "app/machine_detail.html", context)


@login_required
@user_passes_test(is_admin)
def delete_machine(request, machine_id):
    machine = get_object_or_404(Machine, id=machine_id)

    if request.method == "POST":
        machine.delete()
        messages.success(request, "Machine supprimée avec succès.")
        return redirect("app:machine_list_admin")

    return render(request, "app/admin/machine_delete.html", {
        "page_title": "Supprimer machine",
        "machine": machine,
    })

@login_required
@user_passes_test(is_admin)
def export_inventory_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="rapport_inventaire.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("ServiceIT - Rapport d'inventaire", styles["Title"]))
    elements.append(Spacer(1, 20))

    machines = Machine.objects.all().order_by("nom")

    data = [
        ["Nom", "N° Série", "Type", "Pôle", "État"]
    ]

    for machine in machines:
        data.append([
            machine.nom,
            machine.numero_serie or "-",
            machine.type or "-",
            machine.pole or "-",
            machine.get_etat_display(),
        ])

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8e7dff")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(table)
    doc.build(elements)

    return response


# Affectations Views
@login_required
@user_passes_test(is_admin)
def affectation_list(request):
    affectations = Affectation.objects.select_related("machine", "utilisateur").order_by("-date_affectation")

    q = request.GET.get("q")
    statut = request.GET.get("statut")
    pole = request.GET.get("pole")

    if q:
        affectations = affectations.filter(
            Q(machine__nom__icontains=q) |
            Q(utilisateur__email__icontains=q) |
            Q(machine__numero_serie__icontains=q)
        )

    if statut:
        affectations = affectations.filter(statut=statut)

    if pole:
        affectations = affectations.filter(pole=pole)

    paginator = Paginator(affectations, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "app/admin/affectation_list.html", {
        "page_title": "Gestion des affectations",
        "affectations": page_obj,
        "page_obj": page_obj,
    })


@login_required
@user_passes_test(is_admin)
def add_affectation(request):
    if request.method == "POST":
        machine_id = request.POST.get("machine")
        utilisateur_id = request.POST.get("utilisateur")
        pole = request.POST.get("pole")
        date_affectation = request.POST.get("date_affectation")
        remarque = request.POST.get("remarque")

        machine = get_object_or_404(Machine, id=machine_id)

        affectation = Affectation.objects.create(
            machine=machine,
            utilisateur_id=utilisateur_id if utilisateur_id else None,
            pole=pole,
            date_affectation=date_affectation,
            remarque=remarque,
        )

        messages.success(request, f"Affectation créée pour {machine.nom}.")
        return redirect("app:affectation_list")

    machines = Machine.objects.filter(affectations__statut="ACTIVE").exclude(
        affectations__statut="ACTIVE"
    ).union(Machine.objects.exclude(affectations__statut="ACTIVE"))

    utilisateurs = Utilisateur.objects.all()

    return render(request, "app/admin/affectation_form.html", {
        "page_title": "Nouvelle affectation",
        "machines": machines,
        "utilisateurs": utilisateurs,
        "pole_choices": POLE_CHOICES,
    })


@login_required
@user_passes_test(is_admin)
def edit_affectation(request, pk):
    affectation = get_object_or_404(Affectation, pk=pk)

    if request.method == "POST":
        utilisateur_id = request.POST.get("utilisateur")
        pole = request.POST.get("pole")
        date_affectation = request.POST.get("date_affectation")
        date_retour = request.POST.get("date_retour") or None
        remarque = request.POST.get("remarque")
        statut = request.POST.get("statut")

        affectation.utilisateur_id = utilisateur_id if utilisateur_id else None
        affectation.pole = pole
        affectation.date_affectation = date_affectation
        affectation.date_retour = date_retour
        affectation.remarque = remarque
        affectation.statut = statut
        affectation.save()

        messages.success(request, "Affectation modifiée avec succès.")
        return redirect("app:affectation_list")

    utilisateurs = Utilisateur.objects.all()

    return render(request, "app/admin/affectation_form.html", {
        "page_title": "Modifier affectation",
        "affectation": affectation,
        "utilisateurs": utilisateurs,
        "pole_choices": POLE_CHOICES,
    })


@login_required
@user_passes_test(is_admin)
def delete_affectation(request, pk):
    affectation = get_object_or_404(Affectation, pk=pk)

    if request.method == "POST":
        affectation.delete()
        messages.success(request, "Affectation supprimée avec succès.")
        return redirect("app:affectation_list")

    return render(request, "app/admin/affectation_delete.html", {
        "page_title": "Supprimer affectation",
        "affectation": affectation,
    })


# Composants Views
@login_required
@user_passes_test(is_admin)
def component_list(request):
    composants = Composant.objects.select_related("machine").order_by("machine__nom", "nom")

    q = request.GET.get("q")
    machine_id = request.GET.get("machine")
    etat = request.GET.get("etat")

    if q:
        composants = composants.filter(
            Q(nom__icontains=q) |
            Q(type__icontains=q) |
            Q(marque__icontains=q) |
            Q(numero_serie__icontains=q)
        )

    if machine_id:
        composants = composants.filter(machine_id=machine_id)

    if etat:
        composants = composants.filter(etat=etat)

    paginator = Paginator(composants, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    machines = Machine.objects.all().order_by("nom")

    return render(request, "app/admin/component_list.html", {
        "page_title": "Gestion des composants",
        "composants": page_obj,
        "page_obj": page_obj,
        "machines": machines,
    })


@login_required
@user_passes_test(is_admin)
def add_component(request):
    if request.method == "POST":
        Composant.objects.create(
            nom=request.POST.get("nom"),
            type=request.POST.get("type"),
            numero_serie=request.POST.get("numero_serie"),
            marque=request.POST.get("marque"),
            date_installation=request.POST.get("date_installation") or None,
            etat=request.POST.get("etat") or "OK",
            machine_id=request.POST.get("machine"),
        )

        messages.success(request, "Composant ajouté avec succès.")
        return redirect("app:component_list")

    machines = Machine.objects.all().order_by("nom")

    return render(request, "app/admin/component_form.html", {
        "page_title": "Nouveau composant",
        "machines": machines,
    })


@login_required
@user_passes_test(is_admin)
def edit_component(request, pk):
    composant = get_object_or_404(Composant, pk=pk)

    if request.method == "POST":
        composant.nom = request.POST.get("nom")
        composant.type = request.POST.get("type")
        composant.numero_serie = request.POST.get("numero_serie")
        composant.marque = request.POST.get("marque")
        composant.date_installation = request.POST.get("date_installation") or None
        composant.etat = request.POST.get("etat") or "OK"
        composant.machine_id = request.POST.get("machine")
        composant.save()

        messages.success(request, "Composant modifié avec succès.")
        return redirect("app:component_list")

    machines = Machine.objects.all().order_by("nom")

    return render(request, "app/admin/component_form.html", {
        "page_title": "Modifier composant",
        "composant": composant,
        "machines": machines,
    })


@login_required
@user_passes_test(is_admin)
def delete_component(request, pk):
    composant = get_object_or_404(Composant, pk=pk)

    if request.method == "POST":
        composant.delete()
        messages.success(request, "Composant supprimé avec succès.")
        return redirect("app:component_list")

    return render(request, "app/admin/component_delete.html", {
        "page_title": "Supprimer composant",
        "composant": composant,
    })