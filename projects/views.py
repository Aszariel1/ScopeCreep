import math
from datetime import timedelta

from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from xhtml2pdf import pisa

from .models import ChangeRequest, DraftImage, Project, ProjectCategory

ACCEPTED_STATUSES = [ChangeRequest.Status.APPROVED, ChangeRequest.Status.ARCHIVED]
HOURS_PER_WORKDAY = 8


def recalculate_project_totals(project):
    accepted = project.change_requests.filter(status__in=ACCEPTED_STATUSES, project_cat__deleted_at__isnull=True)
    totals = accepted.aggregate(price=Sum('extra_cost'), hours=Sum('extra_hours'))
    project.price = totals['price'] or 0
    project.hours = totals['hours'] or 0

    first = accepted.filter(accepted_at__isnull=False).order_by('accepted_at').first()
    if first:
        workdays = max(1, math.ceil(float(project.hours) / HOURS_PER_WORKDAY))
        project.estimated_date = first.accepted_at.date() + timedelta(days=workdays - 1)
    else:
        project.estimated_date = None

    project.save(update_fields=['price', 'hours', 'estimated_date'])


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
        Project.objects.prefetch_related('categories__change_requests', 'draft_images'),
        token_artist=token_artist,
    )
    all_categories = project.categories.all()
    context = {
        'project': project,
        'categories': [c for c in all_categories if not c.deleted_at],
        'deleted_categories': [c for c in all_categories if c.deleted_at],
    }
    return render(request, 'projects/workspace.html', context)


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


def add_category(request, token_artist):
    project = get_object_or_404(Project, token_artist=token_artist)

    category_name = request.POST.get('category_name', '').strip()
    url = reverse('projects:artist_workspace', kwargs={'token_artist': token_artist})
    if category_name:
        category = ProjectCategory.objects.create(project=project, category_name=category_name)
        return redirect(f'{url}?open={category.id}')

    return redirect(url)


def rename_category(request, token_artist, category_id):
    category = get_object_or_404(ProjectCategory, id=category_id, project__token_artist=token_artist)

    new_name = request.POST.get('category_name', '').strip()
    if new_name:
        category.category_name = new_name
        category.save(update_fields=['category_name'])

    url = reverse('projects:artist_workspace', kwargs={'token_artist': token_artist})
    return redirect(f'{url}?open={category.id}')


def delete_category(request, token_artist, category_id):
    category = get_object_or_404(ProjectCategory, id=category_id, project__token_artist=token_artist)
    category.deleted_at = timezone.now()
    category.save(update_fields=['deleted_at'])
    recalculate_project_totals(category.project)

    return redirect(reverse('projects:artist_workspace', kwargs={'token_artist': token_artist}))


def restore_category(request, token_artist, category_id):
    category = get_object_or_404(ProjectCategory, id=category_id, project__token_artist=token_artist)
    category.deleted_at = None
    category.save(update_fields=['deleted_at'])
    recalculate_project_totals(category.project)

    url = reverse('projects:artist_workspace', kwargs={'token_artist': token_artist})
    return redirect(f'{url}?open={category.id}')


def upload_draft_image(request, token_artist):
    project = get_object_or_404(Project, token_artist=token_artist)

    image = request.FILES.get('image')
    if image:
        DraftImage.objects.create(project=project, image=image)

    return redirect(reverse('projects:artist_workspace', kwargs={'token_artist': token_artist}))


def delete_draft_image(request, token_artist, image_id):
    draft = get_object_or_404(DraftImage, id=image_id, project__token_artist=token_artist)
    draft.image.delete(save=False)
    draft.delete()

    return redirect(reverse('projects:artist_workspace', kwargs={'token_artist': token_artist}))


def update_change_request_status(request, token_artist, change_request_id):
    change_request = get_object_or_404(
        ChangeRequest, id=change_request_id, project__token_artist=token_artist,
    )

    new_status = request.POST.get('status')
    if new_status in ChangeRequest.Status.values:
        change_request.status = new_status
        change_request.extra_cost = request.POST.get('extra_cost') or 0
        change_request.extra_hours = request.POST.get('extra_hours') or 0
        change_request.artist_note = request.POST.get('note', '').strip()
        if new_status in ACCEPTED_STATUSES and not change_request.accepted_at:
            change_request.accepted_at = timezone.now()
        change_request.save(update_fields=['status', 'extra_cost', 'extra_hours', 'artist_note', 'accepted_at'])
        recalculate_project_totals(change_request.project)

    url = reverse('projects:artist_workspace', kwargs={'token_artist': token_artist})
    return redirect(f'{url}?open={change_request.project_cat_id}')


def client_view(request, token_client):
    project = get_object_or_404(
        Project.objects.prefetch_related('categories__change_requests', 'draft_images'),
        token_client=token_client,
    )
    categories = [c for c in project.categories.all() if not c.deleted_at]
    return render(request, 'projects/client_view.html', {'project': project, 'categories': categories})


def client_add_change_request(request, token_client, category_id):
    category = get_object_or_404(ProjectCategory, id=category_id, project__token_client=token_client)

    ChangeRequest.objects.create(
        project=category.project,
        project_cat=category,
        description=request.POST.get('description', ''),
    )

    url = reverse('projects:client_view', kwargs={'token_client': token_client})
    return redirect(f'{url}?open={category.id}')


def client_approve_change_request(request, token_client, change_request_id):
    change_request = get_object_or_404(
        ChangeRequest,
        id=change_request_id,
        project__token_client=token_client,
        status=ChangeRequest.Status.PENDING,
        extra_cost__gt=0,
    )
    change_request.status = ChangeRequest.Status.APPROVED
    change_request.accepted_at = timezone.now()
    change_request.save(update_fields=['status', 'accepted_at'])
    recalculate_project_totals(change_request.project)

    return redirect(reverse('projects:client_view', kwargs={'token_client': token_client}))


def client_cancel_change_request(request, token_client, change_request_id):
    change_request = get_object_or_404(
        ChangeRequest,
        id=change_request_id,
        project__token_client=token_client,
        status=ChangeRequest.Status.PENDING,
    )
    change_request.delete()

    return redirect(reverse('projects:client_view', kwargs={'token_client': token_client}))


def export_pdf(request, token):
    project = get_object_or_404(
        Project.objects.prefetch_related('categories__change_requests'),
        Q(token_artist=token) | Q(token_client=token),
    )

    categories = [c for c in project.categories.all() if not c.deleted_at]
    html = render_to_string('projects/pdf_export.html', {'project': project, 'categories': categories})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{project.name}-scope.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response
