from django.shortcuts import render


def home(request):
    return render(request, 'index.html')

def bhauditor(request):
    return render(request, 'bhauditor.html')

def bhoras(request):
    return render(request, 'bhoras.html')