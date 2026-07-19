import math
from datetime import timedelta

from django.db import migrations

ACCEPTED_STATUSES = ['approved', 'archived']
HOURS_PER_WORKDAY = 8


def backfill(apps, schema_editor):
    ChangeRequest = apps.get_model('projects', 'ChangeRequest')
    Project = apps.get_model('projects', 'Project')

    for change_request in ChangeRequest.objects.filter(status__in=ACCEPTED_STATUSES, accepted_at__isnull=True):
        change_request.accepted_at = change_request.creation_date
        change_request.save(update_fields=['accepted_at'])

    for project in Project.objects.all():
        accepted = ChangeRequest.objects.filter(project=project, status__in=ACCEPTED_STATUSES)
        first = accepted.filter(accepted_at__isnull=False).order_by('accepted_at').first()
        if first:
            workdays = max(1, math.ceil(float(project.hours) / HOURS_PER_WORKDAY))
            project.estimated_date = first.accepted_at.date() + timedelta(days=workdays - 1)
        else:
            project.estimated_date = None
        project.save(update_fields=['estimated_date'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0007_changerequest_accepted_at'),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
