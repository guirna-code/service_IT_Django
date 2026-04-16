from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .models import Utilisateur, Machine, Composant, RapportIntervention


# =========================
# Home
# =========================
def home(request):
    return render(request, 'app/home.html')


def dashboard(request):
    machines = Machine.objects.all()
    interventions = RapportIntervention.objects.all()
    technicians = Utilisateur.objects.filter(role='technician')

    machines_failed = machines.filter(etat='EN_PANNE').count()
    total_machines = machines.count()

    machines_failed_percent = int((machines_failed / total_machines) * 100) if total_machines > 0 else 0

    context = {
        'total_machines': total_machines,
        'total_interventions': interventions.count(),
        'total_technicians': technicians.count(),
        'machines_failed': machines_failed,
        'machines_failed_percent': machines_failed_percent,
        'machines_functional': machines.filter(etat='FONCTIONNEL').count(),
        'machines_repair': machines.filter(etat='REPARATION').count(),
        'recent_interventions': interventions.order_by('-date_cloture')[:5],
    }

    return render(request, 'app/dashboard.html', context)


# =========================
# Authentication
# =========================
def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user:
            auth_login(request, user)
            return redirect('app:dashboard')

    return render(request, 'app/login.html')


def user_logout(request):
    auth_logout(request)
    return redirect('app:login')


# =========================
# Users
# =========================
def user_list(request):
    users = Utilisateur.objects.all()
    return render(request, 'app/user_list.html', {'users': users})


def user_add(request):
    if request.method == 'POST':
        Utilisateur.objects.create_user(
            email=request.POST.get('email'),
            password="123456",  # مؤقت
            role=request.POST.get('role'),
        )
        return redirect('app:user_list')

    return render(request, 'app/user_add.html')


def user_edit(request, user_id):
    user = get_object_or_404(Utilisateur, id=user_id)

    if request.method == 'POST':
        user.email = request.POST.get('email')
        user.role = request.POST.get('role')
        user.save()
        return redirect('app:user_list')

    return render(request, 'app/user_edit.html', {'target_user': user})


def user_delete(request, user_id):
    user = get_object_or_404(Utilisateur, id=user_id)

    if request.method == 'POST':
        user.delete()
        return redirect('app:user_list')

    return render(request, 'app/user_delete.html', {'target_user': user})


# =========================
# Machines
# =========================
def machine_list(request):
    machines = Machine.objects.select_related('enregistre_par')
    return render(request, 'app/machine_list.html', {'machines': machines})


def machine_add(request):
    if request.method == 'POST':
        Machine.objects.create(
            nom=request.POST.get('nom'),
            numero_serie=request.POST.get('numero_serie'),
            type=request.POST.get('type'),
            date_acquisition=request.POST.get('date_acquisition'),
            etat=request.POST.get('etat'),
            enregistre_par=request.user
        )
        return redirect('app:machine_list')

    return render(request, 'app/machine_add.html')


def machine_edit(request, machine_id):
    machine = get_object_or_404(Machine, id=machine_id)

    if request.method == 'POST':
        machine.nom = request.POST.get('nom')
        machine.type = request.POST.get('type')
        machine.etat = request.POST.get('etat')
        machine.save()
        return redirect('app:machine_list')

    return render(request, 'app/machine_edit.html', {'machine': machine})


def machine_delete(request, machine_id):
    machine = get_object_or_404(Machine, id=machine_id)

    if request.method == 'POST':
        machine.delete()
        return redirect('app:machine_list')

    return render(request, 'app/machine_delete.html', {'machine': machine})


# =========================
# Interventions
# =========================
def intervention_list(request):
    interventions = RapportIntervention.objects.select_related('machine_concernee', 'redacteur')
    return render(request, 'app/intervention_list.html', {'interventions': interventions})


def intervention_add(request):
    machines = Machine.objects.all()
    users = Utilisateur.objects.filter(role='technician')

    if request.method == 'POST':
        RapportIntervention.objects.create(
            machine_concernee_id=request.POST.get('machine'),
            redacteur_id=request.POST.get('technicien'),
            date_cloture=request.POST.get('date'),
            description=request.POST.get('description'),
            pieces_changees=request.POST.get('pieces'),
            duree=request.POST.get('duree'),
        )
        return redirect('app:intervention_list')

    return render(request, 'app/intervention_add.html', {
        'machines': machines,
        'techniciens': users
    })


def intervention_edit(request, intervention_id):
    intervention = get_object_or_404(RapportIntervention, id=intervention_id)

    if request.method == 'POST':
        intervention.description = request.POST.get('description')
        intervention.duree = request.POST.get('duree')
        intervention.save()
        return redirect('app:intervention_list')

    return render(request, 'app/intervention_edit.html', {'intervention': intervention})


def intervention_delete(request, intervention_id):
    intervention = get_object_or_404(RapportIntervention, id=intervention_id)

    if request.method == 'POST':
        intervention.delete()
        return redirect('app:intervention_list')

    return render(request, 'app/intervention_delete.html', {'intervention': intervention})


# =========================
# Components
# =========================
def component_list(request):
    components = Composant.objects.select_related('machine')
    return render(request, 'app/component_list.html', {'components': components})