import uuid

from django.db import models


class Project(models.Model):
    class ProjectType(models.TextChoices):
        THREE_D_ART = '3d_art', '3D Art'
        GRAPHIC_DESIGN = 'graphic_design', 'Graphic Design'

    DEFAULT_CATEGORIES = {
        ProjectType.THREE_D_ART: ['Mesh', 'Textures', 'Rigging'],
        ProjectType.GRAPHIC_DESIGN: ['Typography', 'Layout', 'Branding', 'Logo-type'],
    }

    name = models.CharField(max_length=200)
    project_type = models.CharField(max_length=20, choices=ProjectType.choices)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    token_artist = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    token_client = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    data_creare = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ProjectCategory(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='categories')
    category_name = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.project.name} - {self.category_name}'


class ChangeRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'reject', 'Reject'
        ARCHIVED = 'archived', 'Archived'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='change_requests')
    project_cat = models.ForeignKey(ProjectCategory, on_delete=models.CASCADE, related_name='change_requests')
    description = models.TextField()
    extra_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    extra_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.project_cat} - {self.description[:30]}'
