"""
API Views for Smart Task Analyzer
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    AnalyzeRequestSerializer,
    TaskAnalysisResultSerializer,
    TaskInputSerializer
)
from .scoring import analyze_tasks, get_top_suggestions, detect_circular_dependencies
from datetime import datetime
from django.utils import timezone


@api_view(['POST'])
def analyze_tasks_view(request):
    """
    POST /api/tasks/analyze/
    
    Analyze a list of tasks and return them sorted by priority.
    
    Request Body:
    {
        "tasks": [
            {
                "id": 1,
                "title": "Task name",
                "due_date": "2024-12-31T23:59:59Z",
                "estimated_hours": 5.0,
                "importance": 8,
                "dependencies": [2, 3]
            },
            ...
        ],
        "strategy": "smart_balance"  // Optional: smart_balance, fastest_wins, high_impact, deadline_driven
    }
    
    Response:
    {
        "strategy": "smart_balance",
        "total_tasks": 5,
        "circular_dependencies": [],
        "tasks": [
            {
                // Original task fields plus:
                "priority_score": 85.5,
                "priority_level": "HIGH",
                "explanation": "...",
                "urgency_score": 90.0,
                "importance_score": 80.0,
                "effort_score": 75.0,
                "dependency_score": 50.0
            },
            ...
        ]
    }
    """
    # Validate request data
    serializer = AnalyzeRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'error': 'Invalid request data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    tasks = validated_data['tasks']
    strategy = validated_data.get('strategy', 'smart_balance')
    
    # Check for empty task list
    if not tasks:
        return Response({
            'error': 'No tasks provided',
            'details': 'The tasks list cannot be empty'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Detect circular dependencies
    circular_deps = detect_circular_dependencies(tasks)
    circular_dep_info = []
    if circular_deps:
        circular_dep_info = [list(cycle) for cycle in circular_deps]
    
    try:
        # Analyze tasks using the scoring algorithm
        analyzed_tasks = analyze_tasks(tasks, strategy)
        
        # Serialize results
        result_serializer = TaskAnalysisResultSerializer(analyzed_tasks, many=True)
        
        response_data = {
            'strategy': strategy,
            'total_tasks': len(analyzed_tasks),
            'circular_dependencies': circular_dep_info,
            'tasks': result_serializer.data
        }
        
        if circular_dep_info:
            response_data['warning'] = 'Circular dependencies detected. Affected tasks have reduced priority scores.'
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'error': 'Analysis failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def suggest_tasks_view(request):
    """
    POST /api/tasks/suggest/
    
    Get top 3 recommended tasks to work on.
    
    Request Body:
    {
        "tasks": [...],  // Same format as analyze endpoint
        "strategy": "smart_balance",  // Optional
        "limit": 3  // Optional, default is 3
    }
    
    Response:
    {
        "strategy": "smart_balance",
        "suggestions_count": 3,
        "suggestions": [
            {
                // Task with all scoring details plus:
                "recommendation": "Ranked #1: ..."
            },
            ...
        ]
    }
    """
    # Validate request data
    serializer = AnalyzeRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'error': 'Invalid request data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    tasks = validated_data['tasks']
    strategy = validated_data.get('strategy', 'smart_balance')
    limit = request.data.get('limit', 3)
    
    # Validate limit
    try:
        limit = int(limit)
        if limit < 1:
            limit = 3
    except (ValueError, TypeError):
        limit = 3
    
    # Check for empty task list
    if not tasks:
        return Response({
            'error': 'No tasks provided',
            'details': 'The tasks list cannot be empty'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get top suggestions
        suggestions = get_top_suggestions(tasks, limit, strategy)
        
        # Serialize results
        result_serializer = TaskAnalysisResultSerializer(suggestions, many=True)
        
        response_data = {
            'strategy': strategy,
            'suggestions_count': len(suggestions),
            'suggestions': result_serializer.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'error': 'Suggestion generation failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def health_check(request):
    """
    GET /api/health/
    
    Simple health check endpoint.
    """
    return Response({
        'status': 'healthy',
        'message': 'Smart Task Analyzer API is running',
        'timestamp': timezone.now().isoformat()
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def strategies_info(request):
    """
    GET /api/strategies/
    
    Get information about available scoring strategies.
    """
    strategies = {
        'smart_balance': {
            'name': 'Smart Balance',
            'description': 'Balanced approach considering all factors equally',
            'weights': {
                'urgency': 0.30,
                'importance': 0.30,
                'effort': 0.20,
                'dependency': 0.20
            },
            'best_for': 'General task management with no specific constraints'
        },
        'fastest_wins': {
            'name': 'Fastest Wins',
            'description': 'Prioritizes quick, low-effort tasks for momentum',
            'weights': {
                'urgency': 0.15,
                'importance': 0.20,
                'effort': 0.50,
                'dependency': 0.15
            },
            'best_for': 'Building momentum and clearing backlog quickly'
        },
        'high_impact': {
            'name': 'High Impact',
            'description': 'Focuses on important tasks that unlock other work',
            'weights': {
                'urgency': 0.15,
                'importance': 0.45,
                'effort': 0.10,
                'dependency': 0.30
            },
            'best_for': 'Maximum impact and removing blockers'
        },
        'deadline_driven': {
            'name': 'Deadline Driven',
            'description': 'Heavily prioritizes imminent deadlines',
            'weights': {
                'urgency': 0.60,
                'importance': 0.20,
                'effort': 0.10,
                'dependency': 0.10
            },
            'best_for': 'Crisis mode or when deadlines are critical'
        }
    }
    
    return Response(strategies, status=status.HTTP_200_OK)
