from django.shortcuts import get_object_or_404, render

from .models import Project


def project_create(request):
    return render(request, 'projects/home.html')


def artist_workspace(request, token_artist):
    project = get_object_or_404(Project, token_artist=token_artist)
    return render(request, 'projects/workspace.html', {'project': project})


def client_view(request, token_client):
    project = get_object_or_404(Project, token_client=token_client)
    return render(request, 'projects/client_view.html', {'project': project})
