import io
import math
from datetime import timedelta

import cloudinary.exceptions
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, UserCreationForm
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from PIL import Image
from xhtml2pdf import pisa

from .models import ChangeRequest, DraftImage, Project, ProjectCategory

ACCEPTED_STATUSES = [ChangeRequest.Status.APPROVED, ChangeRequest.Status.ARCHIVED]
HOURS_PER_WORKDAY = 8

FIELD_CLASS = 'field w-full rounded-lg px-3 py-2 text-gray-100'

MAX_UPLOAD_SIZE = 5 * 1024 * 1024
TARGET_IMAGE_SIZE = 1 * 1024 * 1024
MAX_IMAGE_DIMENSION = 2560

DEMO_PROJECT_NAME = 'Demo Project'


def compress_image_upload(image):
    """Downscale/re-encode an uploaded image until it's under TARGET_IMAGE_SIZE.

    Uploads over MAX_UPLOAD_SIZE are rejected outright (via ImageUploadTooLarge)
    rather than compressed, since squeezing a 25MB file down to 1MB would wreck
    quality badly enough that the result looks like a bug, not a feature.
    """
    if image.size > MAX_UPLOAD_SIZE:
        raise ImageUploadTooLarge

    if image.size <= TARGET_IMAGE_SIZE:
        return image

    img = Image.open(image)
    img_format = 'PNG' if img.format == 'PNG' and img.mode in ('RGBA', 'P') else 'JPEG'
    if img_format == 'JPEG' and img.mode != 'RGB':
        img = img.convert('RGB')

    if max(img.size) > MAX_IMAGE_DIMENSION:
        img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.LANCZOS)

    buffer = io.BytesIO()
    if img_format == 'JPEG':
        quality = 90
        while quality >= 30:
            buffer.seek(0)
            buffer.truncate()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            if buffer.tell() <= TARGET_IMAGE_SIZE:
                break
            quality -= 10
    else:
        img.save(buffer, format='PNG', optimize=True)

    buffer.seek(0)
    name = image.name.rsplit('.', 1)[0] + ('.jpg' if img_format == 'JPEG' else '.png')
    content_type = 'image/jpeg' if img_format == 'JPEG' else 'image/png'
    return InMemoryUploadedFile(buffer, 'ImageField', name, content_type, buffer.getbuffer().nbytes, None)


class ImageUploadTooLarge(Exception):
    pass


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': FIELD_CLASS})


class StyledUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': FIELD_CLASS})


class StyledPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': FIELD_CLASS})


class StyledSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': FIELD_CLASS})


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


def get_or_create_demo_project():
    project, created = Project.objects.get_or_create(
        name=DEMO_PROJECT_NAME,
        defaults={
            'project_type': Project.ProjectType.GRAPHIC_DESIGN,
            'description': "This is a live demo — click around, request a change, approve one. Nothing here is real client work.",
        },
    )
    if created:
        categories = {
            category_name: ProjectCategory.objects.create(project=project, category_name=category_name)
            for category_name in Project.DEFAULT_CATEGORIES[project.project_type]
        }

        ChangeRequest.objects.create(
            project=project, project_cat=categories['Typography'],
            description='Switch body font to something more modern', status=ChangeRequest.Status.APPROVED,
            extra_cost=45, extra_hours=1.5, artist_note='Swapped to Inter', accepted_at=timezone.now(),
        )
        ChangeRequest.objects.create(
            project=project, project_cat=categories['Layout'],
            description='Add a sticky header on scroll', status=ChangeRequest.Status.PENDING,
            extra_cost=80, extra_hours=2,
        )
        ChangeRequest.objects.create(
            project=project, project_cat=categories['Branding'],
            description='Try a warmer accent color', status=ChangeRequest.Status.APPROVED,
            extra_cost=30, extra_hours=1, accepted_at=timezone.now(),
        )
        ChangeRequest.objects.create(
            project=project, project_cat=categories['Logo-type'],
            description='Explore a monogram version of the logo', status=ChangeRequest.Status.PENDING,
            extra_cost=25, extra_hours=1,
        )
        recalculate_project_totals(project)

    return project


def landing(request):
    demo_project = get_or_create_demo_project()
    return render(request, 'projects/landing.html', {'demo_token': demo_project.token_client})


def register(request):
    if request.user.is_authenticated:
        return redirect('projects:dashboard')

    if request.method == 'POST':
        form = StyledUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('projects:dashboard')
    else:
        form = StyledUserCreationForm()

    return render(request, 'projects/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('projects:dashboard')

    if request.method == 'POST':
        form = StyledAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('projects:dashboard')
    else:
        form = StyledAuthenticationForm()

    return render(request, 'projects/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('projects:landing')


@login_required
def dashboard(request):
    return render(request, 'projects/dashboard.html', {'projects': request.user.projects.all().order_by('-data_creare')})


@login_required
@require_POST
def delete_project(request, token_artist):
    project = get_object_or_404(Project, token_artist=token_artist, owner=request.user)
    for draft in project.draft_images.all():
        draft.image.delete(save=False)
    project.delete()

    return redirect('projects:dashboard')


@login_required
def project_create(request):
    if request.method == 'POST':
        custom_type = request.POST.get('custom_project_type', '').strip()
        if custom_type:
            project_type = custom_type[:50]
            default_categories = []
        else:
            project_type = request.POST.get('project_type')
            default_categories = Project.DEFAULT_CATEGORIES.get(project_type, [])

        project = Project.objects.create(
            owner=request.user,
            name=request.POST.get('name'),
            project_type=project_type,
            description=request.POST.get('description', ''),
        )
        for category_name in default_categories:
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


@require_POST
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


@require_POST
def add_category(request, token_artist):
    project = get_object_or_404(Project, token_artist=token_artist)

    category_name = request.POST.get('category_name', '').strip()
    url = reverse('projects:artist_workspace', kwargs={'token_artist': token_artist})
    if category_name:
        category = ProjectCategory.objects.create(project=project, category_name=category_name)
        return redirect(f'{url}?open={category.id}')

    return redirect(url)


@require_POST
def rename_category(request, token_artist, category_id):
    category = get_object_or_404(ProjectCategory, id=category_id, project__token_artist=token_artist)

    new_name = request.POST.get('category_name', '').strip()
    if new_name:
        category.category_name = new_name
        category.save(update_fields=['category_name'])

    url = reverse('projects:artist_workspace', kwargs={'token_artist': token_artist})
    return redirect(f'{url}?open={category.id}')


@require_POST
def delete_category(request, token_artist, category_id):
    category = get_object_or_404(ProjectCategory, id=category_id, project__token_artist=token_artist)
    category.deleted_at = timezone.now()
    category.save(update_fields=['deleted_at'])
    recalculate_project_totals(category.project)

    return redirect(reverse('projects:artist_workspace', kwargs={'token_artist': token_artist}))


@require_POST
def restore_category(request, token_artist, category_id):
    category = get_object_or_404(ProjectCategory, id=category_id, project__token_artist=token_artist)
    category.deleted_at = None
    category.save(update_fields=['deleted_at'])
    recalculate_project_totals(category.project)

    url = reverse('projects:artist_workspace', kwargs={'token_artist': token_artist})
    return redirect(f'{url}?open={category.id}')


@require_POST
def upload_draft_image(request, token_artist):
    project = get_object_or_404(Project, token_artist=token_artist)

    url = reverse('projects:artist_workspace', kwargs={'token_artist': token_artist})
    image = request.FILES.get('image')
    if image:
        try:
            image = compress_image_upload(image)
            DraftImage.objects.create(project=project, image=image)
        except (ImageUploadTooLarge, cloudinary.exceptions.Error):
            return redirect(f'{url}?image_error=1')

    return redirect(url)


@require_POST
def delete_draft_image(request, token_artist, image_id):
    draft = get_object_or_404(DraftImage, id=image_id, project__token_artist=token_artist)
    draft.image.delete(save=False)
    draft.delete()

    return redirect(reverse('projects:artist_workspace', kwargs={'token_artist': token_artist}))


@require_POST
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
    is_demo = project.name == DEMO_PROJECT_NAME
    return render(request, 'projects/client_view.html', {'project': project, 'categories': categories, 'is_demo': is_demo})


@require_POST
def client_add_change_request(request, token_client, category_id):
    category = get_object_or_404(ProjectCategory, id=category_id, project__token_client=token_client)

    url = reverse('projects:client_view', kwargs={'token_client': token_client})
    if category.project.name == DEMO_PROJECT_NAME:
        return redirect(f'{url}?open={category.id}')

    ChangeRequest.objects.create(
        project=category.project,
        project_cat=category,
        description=request.POST.get('description', ''),
    )

    return redirect(f'{url}?open={category.id}')


@require_POST
def client_approve_change_request(request, token_client, change_request_id):
    change_request = get_object_or_404(
        ChangeRequest,
        id=change_request_id,
        project__token_client=token_client,
        status=ChangeRequest.Status.PENDING,
        extra_cost__gt=0,
    )
    if change_request.project.name != DEMO_PROJECT_NAME:
        change_request.status = ChangeRequest.Status.APPROVED
        change_request.accepted_at = timezone.now()
        change_request.save(update_fields=['status', 'accepted_at'])
        recalculate_project_totals(change_request.project)

    return redirect(reverse('projects:client_view', kwargs={'token_client': token_client}))


@require_POST
def client_cancel_change_request(request, token_client, change_request_id):
    change_request = get_object_or_404(
        ChangeRequest,
        id=change_request_id,
        project__token_client=token_client,
        status=ChangeRequest.Status.PENDING,
    )
    if change_request.project.name == DEMO_PROJECT_NAME:
        return redirect(reverse('projects:client_view', kwargs={'token_client': token_client}))
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
