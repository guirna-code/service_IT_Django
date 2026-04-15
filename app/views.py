from django.http import HttpResponse


def home(request):
    return HttpResponse('Welcome to gestion_it home page.', content_type='text/html')
