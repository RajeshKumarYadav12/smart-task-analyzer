"""
Admin configuration for tasks app
"""
from django.contrib import admin
from .models import Task


class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'due_date', 'estimated_hours', 'importance', 'created_at']
    list_filter = ['importance', 'created_at']
    search_fields = ['title']
    ordering = ['-created_at']


admin.site.register(Task, TaskAdmin)
