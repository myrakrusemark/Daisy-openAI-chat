from django.shortcuts import render
from django.http import HttpResponse
import modules.ContextHandlers as ch

ch = ch.instance

# Create your views here.

def index(request):
    print(ch)
    # Page from the theme 
    return render(request, 'pages/index.html')
