from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import ChangeRequest, Project, ProjectCategory


def project_create(request):
    if request.method == 'POST':
        project = Project.objects.create(
            name=request.POST.get('name'),
            project_type=request.POST.get('project_type'),
            description=request.POST.get('description', ''),
        )
        for category_name in Project.DEFAULT_CATEGORIES[project.project_type]:
            ProjectCategory.objects.create(project=project, category_name=category_name)

        return redirect(reverse('projects:artist_workspace', kwargs={'token_artist': project.token_artist}) + '?new=1')

    return render(request, 'projects/home.html')


def artist_workspace(request, token_artist):
    project = get_object_or_404(
        Project.objects.prefetch_related('categories__change_requests'),
        token_artist=token_artist,
    )
    return render(request, 'projects/workspace.html', {'project': project})


def add_change_request(request, token_artist, category_id):
    category = get_object_or_404(ProjectCategory, id=category_id, project__token_artist=token_artist)

    ChangeRequest.objects.create(
        project=category.project,
        project_cat=category,
        description=request.POST.get('description', ''),
        extra_cost=request.POST.get('extra_cost') or 0,
        extra_hours=request.POST.get('extra_hours') or 0,
    )

    url = reverse('projects:artist_workspace', kwargs={'token_artist': token_artist})
    return redirect(f'{url}?open={category.id}')


def client_view(request, token_client):
    project = get_object_or_404(Project, token_client=token_client)
    return render(request, 'projects/client_view.html', {'project': project})
