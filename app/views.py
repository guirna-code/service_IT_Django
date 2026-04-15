from django.shortcuts import render
from django.db.models import Count, Avg
from django.db.models.functions import TruncDate

from .models import RapportIntervention, Machine, Utilisateur


def dashboard(request):
    # KPI principaux
    total_interventions = RapportIntervention.objects.count()
    duree_moyenne = RapportIntervention.objects.aggregate(Avg('duree'))['duree__avg']

    machines_en_panne = Machine.objects.filter(etat='EN_PANNE').count()

    # Interventions par technicien
    interventions_par_tech = (
        RapportIntervention.objects
        .values('utilisateur__username')
        .annotate(total=Count('id'))
    )

    # Interventions par jour (graph)
    interventions_par_jour = (
        RapportIntervention.objects
        .annotate(date=TruncDate('date_cloture'))
        .values('date')
        .annotate(total=Count('id'))
        .order_by('date')
    )

    context = {
        'total_interventions': total_interventions,
        'duree_moyenne': duree_moyenne,
        'machines_en_panne': machines_en_panne,
        'interventions_par_tech': interventions_par_tech,
        'interventions_par_jour': list(interventions_par_jour),
    }

    return render(request, 'dashboard.html', context)