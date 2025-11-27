"""
URL configuration for task_analyzer project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.generic import TemplateView


def api_root(request):
    """Root API endpoint with documentation"""
    return JsonResponse({
        'message': 'Welcome to Smart Task Analyzer API',
        'version': '1.0.0',
        'endpoints': {
            'analyze_tasks': '/api/tasks/analyze/',
            'suggest_tasks': '/api/tasks/suggest/',
            'health_check': '/api/health/',
            'strategies': '/api/strategies/',
        },
        'frontend': {
            'note': 'Open frontend/index.html in your browser or serve it on a different port',
            'example': 'python -m http.server 8080 (in frontend directory)'
        },
        'documentation': 'See README.md for complete API documentation'
    })


urlpatterns = [
    path('', api_root, name='api_root'),
    path('admin/', admin.site.urls),
    path('api/', include('tasks.urls')),
]
