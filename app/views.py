from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import POLE_CHOICES, Composant, Machine, RapportIntervention, Utilisateur


def is_admin(user):
    return user.is_authenticated and getattr(user, "role", None) == "admin"


def is_technician(user):
    return user.is_authenticated and getattr(user, "role", None) == "technician"


def is_admin_or_technician(user):
    return user.is_authenticated and getattr(user, "role", None) in ["admin", "technician"]


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())

            if getattr(request.user, "role", None) not in roles:
                return render(
                    request,
                    "app/403.html",
                    {"page_title": "Acces refuse"},
                    status=403,
                )

            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def machine_form_context(extra=None):
    context = {
        "machine_type_choices": Machine.TypeMachine.choices,
        "machine_etat_choices": Machine.EtatMachine.choices,
        "pole_choices": POLE_CHOICES,
    }
    if extra:
        context.update(extra)
    return context


def user_login(request):
    if request.user.is_authenticated:
        if is_admin_or_technician(request.user):
            return redirect("app:dashboard")
        auth_logout(request)
        messages.error(request, "Votre role ne donne pas acces au tableau de bord.")
        return redirect("app:login")

    if request.method == "POST":
        email = request.POST.get("email") or request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, email=email, password=password)

        if user is not None:
            if getattr(user, "role", None) not in ["admin", "technician"]:
                messages.error(request, "Votre compte n'a pas acces a ServiceIT.")
                return redirect("app:login")

            auth_login(request, user)
            return redirect("app:dashboard")

        messages.error(request, "Email ou mot de passe incorrect.")

    return render(request, "app/login.html", {"page_title": "Connexion"})


@login_required
def user_logout(request):
    auth_logout(request)
    return redirect("app:login")


@role_required("admin", "technician")
def dashboard(request):
    total_machines = Machine.objects.count()
    total_interventions = RapportIntervention.objects.count()
    total_technicians = Utilisateur.objects.filter(role="technician").count()

    machines_functional = Machine.objects.filter(etat=Machine.EtatMachine.FONCTIONNEL).count()
    machines_repair = Machine.objects.filter(etat=Machine.EtatMachine.REPARATION).count()
    machines_failed = Machine.objects.filter(etat=Machine.EtatMachine.EN_PANNE).count()
    machines_failed_percent = int((machines_failed / total_machines) * 100) if total_machines else 0

    recent_interventions = RapportIntervention.objects.select_related(
        "machine_concernee",
        "redacteur",
        "technicien",
    ).order_by("-id")[:5]

    return render(
        request,
        "app/dashboard.html",
        {
            "page_title": "Tableau de bord",
            "total_machines": total_machines,
            "total_interventions": total_interventions,
            "total_technicians": total_technicians,
            "machines_functional": machines_functional,
            "machines_repair": machines_repair,
            "machines_failed": machines_failed,
            "machines_failed_percent": machines_failed_percent,
            "recent_interventions": recent_interventions,
        },
    )


@role_required("admin")
def manage_technicians(request):
    techs = Utilisateur.objects.filter(role="technician").order_by("email")
    return render(
        request,
        "app/admin/tech_list.html",
        {
            "page_title": "Gestion des techniciens",
            "techs": techs,
        },
    )


@role_required("admin")
def machine_list_admin(request):
    machines = Machine.objects.all().order_by("-id")

    q = request.GET.get("q")
    machine_type = request.GET.get("type")
    etat = request.GET.get("etat")

    if q:
        machines = machines.filter(Q(nom__icontains=q) | Q(numero_serie__icontains=q))

    if machine_type:
        machines = machines.filter(type=machine_type)

    if etat:
        machines = machines.filter(etat=etat)

    page_obj = Paginator(machines, 8).get_page(request.GET.get("page"))

    return render(
        request,
        "app/admin/machine_list.html",
        machine_form_context(
            {
                "page_title": "Gestion des machines",
                "machines": page_obj,
                "page_obj": page_obj,
            }
        ),
    )


@role_required("admin")
def add_machine(request):
    if request.method == "POST":
        nom = request.POST.get("nom")
        if not nom:
            messages.error(request, "Le nom de la machine est obligatoire.")
            return redirect("app:add_machine")

        Machine.objects.create(
            nom=nom,
            numero_serie=request.POST.get("numero_serie") or None,
            type=request.POST.get("type") or None,
            pole=request.POST.get("pole") or "INF",
            date_acquisition=request.POST.get("date_acquisition") or None,
            etat=request.POST.get("etat") or Machine.EtatMachine.FONCTIONNEL,
            enregistre_par=request.user,
        )
        messages.success(request, "Machine ajoutee avec succes.")
        return redirect("app:machine_list_admin")

    return render(
        request,
        "app/admin/machine_add.html",
        machine_form_context({"page_title": "Ajouter une machine"}),
    )


@role_required("admin")
def edit_machine(request, machine_id):
    machine = get_object_or_404(Machine, id=machine_id)

    if request.method == "POST":
        machine.nom = request.POST.get("nom") or machine.nom
        machine.numero_serie = request.POST.get("numero_serie") or None
        machine.type = request.POST.get("type") or None
        machine.pole = request.POST.get("pole") or "INF"
        machine.date_acquisition = request.POST.get("date_acquisition") or None
        machine.etat = request.POST.get("etat") or Machine.EtatMachine.FONCTIONNEL
        machine.save()

        messages.success(request, "Machine modifiee avec succes.")
        return redirect("app:machine_detail", machine_id=machine.id)

    return render(
        request,
        "app/admin/machine_edit.html",
        machine_form_context(
            {
                "page_title": "Modifier une machine",
                "machine": machine,
            }
        ),
    )


@role_required("admin")
def delete_machine(request, machine_id):
    machine = get_object_or_404(Machine, id=machine_id)

    if request.method == "POST":
        machine.delete()
        messages.success(request, "Machine supprimee avec succes.")
        return redirect("app:machine_list_admin")

    return render(
        request,
        "app/admin/machine_delete.html",
        {
            "page_title": "Supprimer une machine",
            "machine": machine,
        },
    )


@role_required("admin")
def inventory_report(request):
    machines = Machine.objects.all().order_by("nom")
    stats = {
        "total": machines.count(),
        "fonctionnel": machines.filter(etat=Machine.EtatMachine.FONCTIONNEL).count(),
        "maintenance": machines.filter(etat=Machine.EtatMachine.REPARATION).count(),
        "panne": machines.filter(etat=Machine.EtatMachine.EN_PANNE).count(),
    }

    return render(
        request,
        "app/admin/report.html",
        {
            "page_title": "Rapport d'inventaire",
            "stats": stats,
            "machines": machines,
        },
    )


@role_required("admin")
def export_inventory_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="rapport_inventaire.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("ServiceIT - Rapport d'inventaire", styles["Title"]),
        Spacer(1, 20),
    ]

    data = [["Nom", "No. serie", "Type", "Pole", "Etat"]]
    for machine in Machine.objects.all().order_by("nom"):
        data.append(
            [
                machine.nom,
                machine.numero_serie or "-",
                machine.get_type_display() if machine.type else "-",
                machine.get_pole_display() if machine.pole else "-",
                machine.get_etat_display() if machine.etat else "-",
            ]
        )

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8e7dff")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    elements.append(table)
    doc.build(elements)
    return response


@role_required("technician")
def machine_list_tech(request):
    machines = Machine.objects.all().order_by("nom")

    q = request.GET.get("q")
    machine_type = request.GET.get("type")
    etat = request.GET.get("etat")

    if q:
        machines = machines.filter(Q(nom__icontains=q) | Q(numero_serie__icontains=q))

    if machine_type:
        machines = machines.filter(type=machine_type)

    if etat:
        machines = machines.filter(etat=etat)

    return render(
        request,
        "app/tech/machine_list.html",
        machine_form_context(
            {
                "page_title": "Machines",
                "machines": machines,
            }
        ),
    )


@role_required("technician")
def update_machine_status(request, machine_id):
    machine = get_object_or_404(Machine, id=machine_id)

    if request.method == "POST":
        new_etat = request.POST.get("etat")
        if new_etat:
            machine.etat = new_etat
            machine.save(update_fields=["etat"])
            messages.success(request, f"Etat de la machine {machine.nom} mis a jour.")
        return redirect("app:machine_list_tech")

    return render(
        request,
        "app/tech/update_status.html",
        machine_form_context(
            {
                "page_title": "Modifier l'etat",
                "machine": machine,
            }
        ),
    )


@role_required("admin", "technician")
def add_intervention(request):
    if request.method == "POST":
        machine_id = request.POST.get("machine")
        if not machine_id:
            messages.error(request, "Veuillez selectionner une machine.")
            return redirect("app:add_intervention")

        machine = get_object_or_404(Machine, pk=machine_id)
        technicien_id = request.POST.get("technicien")
        technicien = None

        if technicien_id:
            technicien = Utilisateur.objects.filter(id=technicien_id, role="technician").first()
        elif is_technician(request.user):
            technicien = request.user

        RapportIntervention.objects.create(
            machine_concernee=machine,
            redacteur=request.user,
            technicien=technicien,
            description=request.POST.get("description") or "",
            type=request.POST.get("type") or None,
            date=request.POST.get("date") or None,
            statut=request.POST.get("statut") or RapportIntervention.StatutIntervention.EN_COURS,
            duree=request.POST.get("duree") or None,
        )

        messages.success(request, "Rapport d'intervention cree avec succes.")
        return redirect("app:intervention_list")

    return render(
        request,
        "app/tech/intervention_add.html",
        {
            "page_title": "Ajouter une intervention",
            "machines": Machine.objects.all().order_by("nom"),
            "techniciens": Utilisateur.objects.filter(role="technician").order_by("email"),
            "type_choices": RapportIntervention.TypeIntervention.choices,
            "statut_choices": RapportIntervention.StatutIntervention.choices,
        },
    )


@role_required("admin", "technician")
def intervention_list(request):
    interventions = RapportIntervention.objects.select_related(
        "machine_concernee",
        "redacteur",
        "technicien",
    ).order_by("-id")

    return render(
        request,
        "app/tech/intervention_list.html",
        {
            "page_title": "Liste des interventions",
            "interventions": interventions,
        },
    )


@role_required("admin", "technician")
def machine_detail(request, machine_id):
    machine = get_object_or_404(Machine, id=machine_id)
    interventions = RapportIntervention.objects.filter(machine_concernee=machine).select_related(
        "redacteur",
        "technicien",
    ).order_by("-id")
    composants = Composant.objects.filter(machine=machine).order_by("nom")

    return render(
        request,
        "app/machine_detail.html",
        {
            "page_title": f"Machine - {machine.nom}",
            "machine": machine,
            "interventions": interventions,
            "composants": composants,
        },
    )


@role_required("admin")
def component_list(request):
    components = Composant.objects.select_related("machine").order_by("machine__nom", "nom")
    return render(
        request,
        "app/admin/component_list.html",
        {
            "page_title": "Composants",
            "components": components,
        },
    )


@role_required("admin")
def add_component(request):
    if request.method == "POST":
        machine_id = request.POST.get("machine")
        if not machine_id:
            messages.error(request, "Veuillez selectionner une machine.")
            return redirect("app:add_component")

        Composant.objects.create(
            nom=request.POST.get("nom") or "",
            type=request.POST.get("type") or None,
            etat=request.POST.get("etat") or Composant.EtatComposant.OK,
            machine_id=machine_id,
        )

        messages.success(request, "Composant ajoute avec succes.")
        return redirect("app:component_list")

    return render(
        request,
        "app/admin/component_form.html",
        {
            "page_title": "Ajouter un composant",
            "machines": Machine.objects.all().order_by("nom"),
            "etat_choices": Composant.EtatComposant.choices,
        },
    )


@role_required("admin")
def edit_component(request, pk):
    component = get_object_or_404(Composant, pk=pk)

    if request.method == "POST":
        component.nom = request.POST.get("nom") or component.nom
        component.type = request.POST.get("type") or None
        component.etat = request.POST.get("etat") or Composant.EtatComposant.OK
        component.machine_id = request.POST.get("machine") or component.machine_id
        component.save()

        messages.success(request, "Composant modifie avec succes.")
        return redirect("app:component_list")

    return render(
        request,
        "app/admin/component_form.html",
        {
            "page_title": "Modifier un composant",
            "component": component,
            "machines": Machine.objects.all().order_by("nom"),
            "etat_choices": Composant.EtatComposant.choices,
        },
    )


@role_required("admin")
def delete_component(request, pk):
    component = get_object_or_404(Composant, pk=pk)

    if request.method == "POST":
        component.delete()
        messages.success(request, "Composant supprime avec succes.")
        return redirect("app:component_list")

    return render(
        request,
        "app/admin/component_delete.html",
        {
            "page_title": "Supprimer un composant",
            "component": component,
        },
    )
