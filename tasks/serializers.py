"""
Django REST Framework serializers for Task model
"""
from rest_framework import serializers
from .models import Task
from datetime import datetime
from django.utils import timezone


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model with validation.
    """
    class Meta:
        model = Task
        fields = ['id', 'title', 'due_date', 'estimated_hours', 'importance', 'dependencies', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_estimated_hours(self, value):
        """Ensure estimated hours is positive"""
        if value <= 0:
            raise serializers.ValidationError("Estimated hours must be greater than 0")
        return value
    
    def validate_importance(self, value):
        """Ensure importance is between 1 and 10"""
        if value < 1 or value > 10:
            raise serializers.ValidationError("Importance must be between 1 and 10")
        return value
    
    def validate_dependencies(self, value):
        """Ensure dependencies is a list"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Dependencies must be a list")
        return value


class TaskInputSerializer(serializers.Serializer):
    """
    Serializer for task input in analyze endpoint.
    Doesn't require database ID as tasks may not be persisted.
    """
    id = serializers.IntegerField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255)
    due_date = serializers.DateTimeField()
    estimated_hours = serializers.FloatField(min_value=0.1)
    importance = serializers.IntegerField(min_value=1, max_value=10)
    dependencies = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list
    )
    
    def validate_due_date(self, value):
        """Ensure due_date is a valid datetime"""
        if not isinstance(value, datetime):
            raise serializers.ValidationError("Invalid date format")
        return value


class TaskAnalysisResultSerializer(serializers.Serializer):
    """
    Serializer for task analysis results with calculated priority score.
    """
    id = serializers.IntegerField(allow_null=True)
    title = serializers.CharField()
    due_date = serializers.DateTimeField()
    estimated_hours = serializers.FloatField()
    importance = serializers.IntegerField()
    dependencies = serializers.ListField(child=serializers.IntegerField())
    priority_score = serializers.FloatField()
    priority_level = serializers.CharField()
    explanation = serializers.CharField()
    urgency_score = serializers.FloatField()
    importance_score = serializers.FloatField()
    effort_score = serializers.FloatField()
    dependency_score = serializers.FloatField()


class AnalyzeRequestSerializer(serializers.Serializer):
    """
    Request serializer for the analyze endpoint.
    """
    tasks = TaskInputSerializer(many=True)
    strategy = serializers.ChoiceField(
        choices=['smart_balance', 'fastest_wins', 'high_impact', 'deadline_driven'],
        default='smart_balance',
        required=False
    )
