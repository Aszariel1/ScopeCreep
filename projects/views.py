from django.shortcuts import get_object_or_404, redirect, render

from .models import Project, ProjectCategory


def project_create(request):
    if request.method == 'POST':
        project = Project.objects.create(
            name=request.POST.get('name'),
            project_type=request.POST.get('project_type'),
            description=request.POST.get('description', ''),
        )
        for category_name in Project.DEFAULT_CATEGORIES[project.project_type]:
            ProjectCategory.objects.create(project=project, category_name=category_name)

        return redirect('projects:artist_workspace', token_artist=project.token_artist)

    return render(request, 'projects/home.html')


def artist_workspace(request, token_artist):
    project = get_object_or_404(Project, token_artist=token_artist)
    return render(request, 'projects/workspace.html', {'project': project})


def client_view(request, token_client):
    project = get_object_or_404(Project, token_client=token_client)
    return render(request, 'projects/client_view.html', {'project': project})
