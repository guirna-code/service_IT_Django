from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .forms import ComposantForm, MachineForm, MachineStatusForm, RapportInterventionForm
from .models import POLE_CHOICES, Composant, Machine, RapportIntervention, Utilisateur
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import cm
from textwrap import wrap

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


def paginate(request, queryset, per_page=10):
    return Paginator(queryset, per_page).get_page(request.GET.get("page"))


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
@require_POST
def user_logout(request):
    auth_logout(request)
    return redirect("app:login")


@role_required("admin", "technician")
def dashboard(request):
    total_machines = Machine.objects.count()
    total_interventions = RapportIntervention.objects.count()
    total_technicians = Utilisateur.objects.filter(role="technician").count()
    machines_reparation = Machine.objects.filter(
    etat="REPARATION").count()

    machine_status_counts = {
        row["etat"]: row["total"]
        for row in Machine.objects.values("etat").annotate(total=Count("id"))
    }
    machines_functional = machine_status_counts.get(Machine.EtatMachine.FONCTIONNEL, 0)
    machines_repair = machine_status_counts.get(Machine.EtatMachine.REPARATION, 0)
    machines_failed = machine_status_counts.get(Machine.EtatMachine.EN_PANNE, 0)
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
            "machines_reparation": machines_reparation,
            "machines_functional": machines_functional,
            "machines_repair": machines_repair,
            "machines_failed": machines_failed,
            "machines_failed_percent": machines_failed_percent,
            "recent_interventions": recent_interventions,
        },
    )


@role_required("admin")
def manage_technicians(request):
    techs = Utilisateur.objects.filter(role="technician").only(
        "id",
        "email",
        "first_name",
        "last_name",
        "is_active",
    ).order_by("email")
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
    form = MachineForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        machine = form.save(commit=False)
        machine.enregistre_par = request.user
        machine.save()
        messages.success(request, "Machine ajoutee avec succes.")
        return redirect("app:machine_list_admin")

    return render(
        request,
        "app/admin/machine_add.html",
        machine_form_context(
            {
                "page_title": "Ajouter une machine",
                "form": form,
            }
        ),
    )


@role_required("admin")
def edit_machine(request, machine_id):
    machine = get_object_or_404(Machine, id=machine_id)
    form = MachineForm(request.POST or None, instance=machine)

    if request.method == "POST" and form.is_valid():
        machine = form.save()
        messages.success(request, "Machine modifiee avec succes.")
        return redirect("app:machine_detail", machine_id=machine.id)

    return render(
        request,
        "app/admin/machine_edit.html",
        machine_form_context(
            {
                "page_title": "Modifier une machine",
                "machine": machine,
                "form": form,
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
    machine_status_counts = {
        row["etat"]: row["total"]
        for row in Machine.objects.values("etat").annotate(total=Count("id"))
    }
    stats = {
        "total": sum(machine_status_counts.values()),
        "fonctionnel": machine_status_counts.get(Machine.EtatMachine.FONCTIONNEL, 0),
        "maintenance": machine_status_counts.get(Machine.EtatMachine.REPARATION, 0),
        "panne": machine_status_counts.get(Machine.EtatMachine.EN_PANNE, 0),
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
    machines = Machine.objects.only("nom", "numero_serie", "type", "pole", "etat").order_by("nom")
    for machine in machines.iterator(chunk_size=500):
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

    page_obj = paginate(request, machines, per_page=10)

    return render(
        request,
        "app/tech/machine_list.html",
        machine_form_context(
            {
                "page_title": "Machines",
                "machines": page_obj,
                "page_obj": page_obj,
            }
        ),
    )


@role_required("technician")
def update_machine_status(request, machine_id):
    machine = get_object_or_404(Machine, id=machine_id)
    form = MachineStatusForm(request.POST or None, instance=machine)

    if request.method == "POST" and form.is_valid():
        machine = form.save(commit=False)
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
                "form": form,
            }
        ),
    )


@role_required("admin", "technician")
def add_intervention(request):
    form = RapportInterventionForm(request.POST or None, user=request.user)

    if request.method == "POST" and form.is_valid():
        intervention = form.save(commit=False)
        intervention.redacteur = request.user
        if is_technician(request.user):
            intervention.technicien = request.user
        intervention.save()
        messages.success(request, "Rapport d'intervention cree avec succes.")
        return redirect("app:intervention_list")

    return render(
        request,
        "app/tech/intervention_add.html",
        {
            "page_title": "Ajouter une intervention",
            "form": form,
        },
    )


@role_required("admin", "technician")
def intervention_list(request):
    interventions = RapportIntervention.objects.select_related(
        "machine_concernee",
        "redacteur",
        "technicien",
    ).order_by("-id")
    page_obj = paginate(request, interventions, per_page=10)

    return render(
        request,
        "app/tech/intervention_list.html",
        {
            "page_title": "Liste des interventions",
            "interventions": page_obj,
            "page_obj": page_obj,
        },
    )


@role_required("admin", "technician")
def machine_detail(request, machine_id):
    machine = get_object_or_404(Machine.objects.select_related("enregistre_par"), id=machine_id)
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
    form = ComposantForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Composant ajoute avec succes.")
        return redirect("app:component_list")

    return render(
        request,
        "app/admin/component_form.html",
        {
            "page_title": "Ajouter un composant",
            "form": form,
        },
    )


@role_required("admin")
def edit_component(request, pk):
    component = get_object_or_404(Composant, pk=pk)
    form = ComposantForm(request.POST or None, instance=component)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Composant modifie avec succes.")
        return redirect("app:component_list")

    return render(
        request,
        "app/admin/component_form.html",
        {
            "page_title": "Modifier un composant",
            "component": component,
            "form": form,
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






def machine_pdf(request, machine_id):
    machine = get_object_or_404(Machine, id=machine_id)

    composants = Composant.objects.filter(machine=machine).order_by("nom")

    interventions = RapportIntervention.objects.filter(
        machine_concernee=machine
    ).select_related(
        "technicien",
        "redacteur"
    ).order_by("-date", "-id")

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="machine_{machine.id}.pdf"'
    )

    pdf = canvas.Canvas(response, pagesize=A4)

    width, height = A4
    y = height - 2 * cm

    # Background Header
    pdf.setFillColor(colors.HexColor("#0f172a"))
    pdf.rect(0, height - 4 * cm, width, 4 * cm, fill=1)

    # Title
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawString(2 * cm, height - 2.2 * cm, "ServiceIT Machine Report")

    pdf.setFont("Helvetica", 11)
    pdf.setFillColor(colors.HexColor("#cbd5e1"))
    pdf.drawString(
        2 * cm,
        height - 3 * cm,
        "Professional machine maintenance report"
    )

    y = height - 5 * cm

    # Section helper
    def section_title(title):
        nonlocal y

        pdf.setFillColor(colors.HexColor("#8b5cf6"))
        pdf.roundRect(
            1.7 * cm,
            y - 0.25 * cm,
            8 * cm,
            0.8 * cm,
            6,
            fill=1
        )

        pdf.setFillColor(colors.white)
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(2 * cm, y, title)

        y -= 1.2 * cm

    # MACHINE INFOS
    section_title("Informations machine")

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 11)

    infos = [
        ("Nom", machine.nom),
        ("Numero Serie", machine.numero_serie or "-"),
        ("Type", machine.get_type_display() if machine.type else "-"),
        ("Pole", machine.get_pole_display() if machine.pole else "-"),
        ("Etat", machine.get_etat_display() if machine.etat else "-"),
        ("Date acquisition", str(machine.date_acquisition or "-")),
    ]

    for label, value in infos:
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(2 * cm, y, f"{label} :")

        pdf.setFont("Helvetica", 11)
        pdf.drawString(6.2 * cm, y, str(value))

        y -= 0.7 * cm

    # QR CODE
    if machine.qr_code:
        qr_image = ImageReader(machine.qr_code.path)

        pdf.drawImage(
            qr_image,
            width - 7 * cm,
            height - 10 * cm,
            width=4.5 * cm,
            height=4.5 * cm
        )

    y -= 0.3 * cm

    # COMPONENTS
    section_title("Composants")

    if composants.exists():

        for composant in composants:

            line = (
                f"• {composant.nom}"
            )

            if composant.type:
                line += f" | Type: {composant.type}"

            if composant.etat:
                line += (
                    f" | Etat: "
                    f"{composant.get_etat_display()}"
                )

            pdf.setFont("Helvetica", 10.5)
            pdf.drawString(2 * cm, y, line[:110])

            y -= 0.6 * cm

            if y < 4 * cm:
                pdf.showPage()
                y = height - 2 * cm

    else:
        pdf.setFont("Helvetica", 10.5)
        pdf.drawString(
            2 * cm,
            y,
            "Aucun composant enregistre."
        )

        y -= 0.8 * cm

    y -= 0.4 * cm

    # INTERVENTIONS
    section_title("Interventions")

    if interventions.exists():

        for intervention in interventions:

            technicien = (
                intervention.technicien.email
                if intervention.technicien
                else intervention.redacteur.email
            )

            # Box
            pdf.setFillColor(colors.HexColor("#f8fafc"))
            pdf.roundRect(
                1.8 * cm,
                y - 4.5 * cm,
                width - 4 * cm,
                4.2 * cm,
                8,
                fill=1,
                stroke=0
            )

            pdf.setFillColor(colors.black)

            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawString(2.2 * cm, y - 0.4 * cm, "Intervention")

            lines = [
                f"Date : {intervention.date or '-'}",
                (
                    f"Type : "
                    f"{intervention.get_type_display()}"
                    if intervention.type else "-"
                ),
                f"Technicien : {technicien}",
                f"Statut : {intervention.get_statut_display()}",
                f"Duree : {intervention.duree or '-'} min",
            ]

            current_y = y - 1 * cm

            pdf.setFont("Helvetica", 10)

            for line in lines:
                pdf.drawString(2.4 * cm, current_y, line)
                current_y -= 0.45 * cm

            # DESCRIPTION
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(
                2.4 * cm,
                current_y,
                "Description :"
            )

            current_y -= 0.5 * cm

            pdf.setFont("Helvetica", 10)

            wrapped_desc = wrap(
                intervention.description or "-",
                width=85
            )

            for desc_line in wrapped_desc:
                pdf.drawString(
                    2.7 * cm,
                    current_y,
                    desc_line
                )

                current_y -= 0.42 * cm

            y = current_y - 0.8 * cm

            if y < 5 * cm:
                pdf.showPage()
                y = height - 2 * cm

    else:
        pdf.setFont("Helvetica", 10.5)
        pdf.drawString(
            2 * cm,
            y,
            "Aucune intervention enregistree."
        )

    # FOOTER
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.setFillColor(colors.grey)

    pdf.drawString(
        2 * cm,
        1.5 * cm,
        "Generated by ServiceIT • Professional IT Management System"
    )

    pdf.save()

    return response
