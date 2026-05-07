from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.urls import reverse
from .models import Utilisateur, Machine, RapportIntervention, Composant


# ==========================================
# TESTS DE RÔLES (SÉCURITÉ)
# ==========================================
def is_admin(user):
    return user.is_authenticated and getattr(user, 'role', None) == 'admin'


def is_technician(user):
    return user.is_authenticated and getattr(user, 'role', None) == 'technician'


# ==========================================
# AUTHENTIFICATION
# ==========================================
def user_login(request):
    """Formulaire de connexion.

    Attend des champs `username` (ou `email`) et `password`.
    Redirige vers `app:dashboard` après authentification.
    """
    if request.user.is_authenticated:
        return redirect('app:dashboard')

    if request.method == 'POST':
        identifier = request.POST.get('username') or request.POST.get('email')
        password = request.POST.get('password')

        # Essaie d'abord l'authentification standard (username)
        user = authenticate(request, username=identifier, password=password)
        if user is None:
            # Certains projets utilisent l'email comme identifiant
            user = authenticate(request, email=identifier, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect('app:dashboard')

        messages.error(request, "Email ou mot de passe incorrect.")

    return render(request, 'app/login.html')


@login_required
def user_logout(request):
    auth_logout(request)
    return redirect('app:login')


# ==========================================
# INTERFACE COMMUNE
# ==========================================
@login_required
def dashboard(request):
    role = getattr(request.user, 'role', None)
    if role == 'admin':
        context = {
            'total_techs': Utilisateur.objects.filter(role='technician').count(),
            'total_machines': Machine.objects.count(),
            'en_panne': Machine.objects.filter(etat='EN_PANNE').count(),
        }
        return render(request, 'app/admin/dashboard.html', context)

    if role == 'technician':
        context = {
            'mes_interventions': RapportIntervention.objects.filter(redacteur=request.user).count(),
            'machines_dispo': Machine.objects.all().count(),
        }
        return render(request, 'app/tech/dashboard.html', context)

    messages.error(request, "Accès non autorisé.")
    return redirect('app:login')


# ==========================================
# INTERFACE ADMIN (Gestion & Stratégie)
# ==========================================

@login_required
@user_passes_test(is_admin)
def manage_technicians(request):
    techs = Utilisateur.objects.filter(role='technician')
    return render(request, 'app/admin/tech_list.html', {'techs': techs})


@login_required
@user_passes_test(is_admin)
def machine_list_admin(request):
    machines = Machine.objects.all()
    return render(request, 'app/admin/machine_list.html', {'machines': machines})


@login_required
@user_passes_test(is_admin)
def add_machine(request):
    if request.method == 'POST':
        Machine.objects.create(
            nom=request.POST.get('nom'),
            numero_serie=request.POST.get('numero_serie'),
            etat=request.POST.get('etat') or 'FONCTIONNEL',
            enregistre_par=request.user
        )
        messages.success(request, "Machine ajoutée avec succès")
        return redirect('app:machine_list_admin')

    return render(request, 'app/admin/machine_form.html')


@login_required
@user_passes_test(is_admin)
def inventory_report(request):
    machines = Machine.objects.all()
    stats = {
        'total': machines.count(),
        'fonctionnel': machines.filter(etat='FONCTIONNEL').count(),
        'panne': machines.filter(etat='EN_PANNE').count(),
    }
    return render(request, 'app/admin/report.html', {'stats': stats, 'machines': machines})


# ==========================================
# INTERFACE TECHNICIEN (Terrain & Maintenance)
# ==========================================

@login_required
@user_passes_test(is_technician)
def machine_list_tech(request):
    machines = Machine.objects.all()
    return render(request, 'app/tech/machine_list.html', {'machines': machines})


@login_required
@user_passes_test(is_technician)
def update_machine_status(request, machine_id):
    machine = get_object_or_404(Machine, id=machine_id)
    if request.method == 'POST':
        new_etat = request.POST.get('etat')
        if new_etat:
            machine.etat = new_etat
            machine.save()
            messages.info(request, f"État de la machine {machine.nom} mis à jour.")
        return redirect('app:machine_list_tech')

    return render(request, 'app/tech/update_status.html', {'machine': machine})


@login_required
@user_passes_test(is_technician)
def add_intervention(request):
    if request.method == 'POST':
        machine_pk = request.POST.get('machine')
        machine = get_object_or_404(Machine, pk=machine_pk)
        RapportIntervention.objects.create(
            machine_concernee=machine,
            redacteur=request.user,
            description=request.POST.get('description'),
            # Assurez-vous de gérer le format de la date côté template/JS
        )
        messages.success(request, "Intervention créée.")
        return redirect('app:dashboard')

    machines = Machine.objects.all()
    return render(request, 'app/tech/intervention_form.html', {'machines': machines})