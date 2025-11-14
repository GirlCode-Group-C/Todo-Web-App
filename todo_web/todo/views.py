from django.shortcuts import render

def landing_page(request):
    return render(request, 'todo/landing.html')
# Create your views here.
