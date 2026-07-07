from django.contrib import admin

from .models import ChangeRequest, Project, ProjectCategory


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'project_type', 'price', 'hours', 'data_creare')


@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'project')


@admin.register(ChangeRequest)
class ChangeRequestAdmin(admin.ModelAdmin):
    list_display = ('project_cat', 'status', 'extra_cost', 'extra_hours', 'creation_date')
    list_filter = ('status',)
