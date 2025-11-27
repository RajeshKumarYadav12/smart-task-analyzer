"""
Task model for Smart Task Analyzer
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Task(models.Model):
    """
    Task model representing a single task with priority attributes.
    
    Fields:
    - title: Task name/description
    - due_date: When the task is due
    - estimated_hours: Estimated effort in hours
    - importance: Subjective importance rating (1-10)
    - dependencies: JSON field storing list of task IDs that must complete first
    """
    title = models.CharField(max_length=255)
    due_date = models.DateTimeField()
    estimated_hours = models.FloatField(
        validators=[MinValueValidator(0.1)],
        help_text="Estimated hours to complete the task"
    )
    importance = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Importance rating from 1 (low) to 10 (high)"
    )
    dependencies = models.JSONField(
        default=list,
        blank=True,
        help_text="List of task IDs that must be completed before this task"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
