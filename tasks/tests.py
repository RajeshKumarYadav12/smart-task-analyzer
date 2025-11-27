"""
Unit Tests for Smart Task Analyzer
"""
from django.test import TestCase, Client
from django.utils import timezone
from datetime import datetime, timedelta
from tasks.scoring import (
    calculate_priority_score,
    calculate_urgency_score,
    calculate_importance_score,
    calculate_effort_score,
    calculate_dependency_score,
    detect_circular_dependencies,
    has_circular_dependency,
    analyze_tasks,
    get_top_suggestions
)
import json


class ScoringAlgorithmTests(TestCase):
    """Test cases for the scoring algorithm"""
    
    def setUp(self):
        """Set up test data"""
        self.now = timezone.now()
        
        self.sample_task = {
            'id': 1,
            'title': 'Test Task',
            'due_date': self.now + timedelta(days=2),
            'estimated_hours': 5.0,
            'importance': 8,
            'dependencies': []
        }
    
    def test_urgency_score_past_due(self):
        """Test urgency scoring for overdue tasks"""
        past_date = self.now - timedelta(days=2)
        score, explanation = calculate_urgency_score(past_date, self.now)
        
        # Overdue tasks should get penalties
        self.assertLess(score, 50)
        self.assertIn('OVERDUE', explanation)
    
    def test_urgency_score_imminent(self):
        """Test urgency scoring for tasks due within 24 hours"""
        soon_date = self.now + timedelta(hours=12)
        score, explanation = calculate_urgency_score(soon_date, self.now)
        
        # Tasks due within 24 hours should get high scores
        self.assertGreaterEqual(score, 90)
        self.assertIn('CRITICAL', explanation)
    
    def test_urgency_score_distant(self):
        """Test urgency scoring for tasks far in the future"""
        far_date = self.now + timedelta(days=30)
        score, explanation = calculate_urgency_score(far_date, self.now)
        
        # Distant tasks should get low urgency scores
        self.assertLess(score, 30)
    
    def test_importance_score_mapping(self):
        """Test importance score conversion from 1-10 to 0-100"""
        # Test minimum importance
        score_min, _ = calculate_importance_score(1)
        self.assertEqual(score_min, 10.0)
        
        # Test maximum importance
        score_max, _ = calculate_importance_score(10)
        self.assertEqual(score_max, 100.0)
        
        # Test middle importance
        score_mid, _ = calculate_importance_score(5)
        self.assertEqual(score_mid, 50.0)
    
    def test_effort_score_quick_wins(self):
        """Test effort scoring rewards quick wins"""
        # Quick task (< 1 hour)
        score_quick, explanation_quick = calculate_effort_score(0.5)
        self.assertGreater(score_quick, 90)
        self.assertIn('QUICK WIN', explanation_quick)
        
        # Long task (> 8 hours)
        score_long, explanation_long = calculate_effort_score(15)
        self.assertLess(score_long, 20)
        self.assertIn('High effort', explanation_long)
    
    def test_dependency_score_no_dependencies(self):
        """Test dependency scoring for tasks with no dependents"""
        tasks = [
            {'id': 1, 'dependencies': []},
            {'id': 2, 'dependencies': []}
        ]
        
        score, explanation = calculate_dependency_score(1, tasks)
        self.assertEqual(score, 20.0)
        self.assertIn('No tasks blocked', explanation)
    
    def test_dependency_score_blocking_tasks(self):
        """Test dependency scoring for tasks that block others"""
        tasks = [
            {'id': 1, 'dependencies': []},
            {'id': 2, 'dependencies': [1]},
            {'id': 3, 'dependencies': [1]},
            {'id': 4, 'dependencies': [1]}
        ]
        
        score, explanation = calculate_dependency_score(1, tasks)
        # Task 1 blocks 3 tasks, should get high score
        self.assertGreaterEqual(score, 90)
        self.assertIn('CRITICAL BLOCKER', explanation)
    
    def test_complete_priority_calculation(self):
        """Test complete priority score calculation"""
        tasks = [self.sample_task]
        result = calculate_priority_score(self.sample_task, tasks, 'smart_balance')
        
        # Check all required fields are present
        self.assertIn('priority_score', result)
        self.assertIn('priority_level', result)
        self.assertIn('explanation', result)
        self.assertIn('urgency_score', result)
        self.assertIn('importance_score', result)
        self.assertIn('effort_score', result)
        self.assertIn('dependency_score', result)
        
        # Priority score should be between 0 and 100
        self.assertGreaterEqual(result['priority_score'], 0)
        self.assertLessEqual(result['priority_score'], 100)
        
        # Priority level should be valid
        self.assertIn(result['priority_level'], ['HIGH', 'MEDIUM', 'LOW'])
    
    def test_different_strategies(self):
        """Test that different strategies produce different scores"""
        tasks = [self.sample_task]
        
        score_balanced = calculate_priority_score(self.sample_task, tasks, 'smart_balance')
        score_fastest = calculate_priority_score(self.sample_task, tasks, 'fastest_wins')
        score_impact = calculate_priority_score(self.sample_task, tasks, 'high_impact')
        score_deadline = calculate_priority_score(self.sample_task, tasks, 'deadline_driven')
        
        # Scores should vary by strategy
        scores = [
            score_balanced['priority_score'],
            score_fastest['priority_score'],
            score_impact['priority_score'],
            score_deadline['priority_score']
        ]
        
        # Not all scores should be identical (though some might be close)
        self.assertTrue(len(set(scores)) > 1)


class CircularDependencyTests(TestCase):
    """Test cases for circular dependency detection"""
    
    def test_no_circular_dependencies(self):
        """Test detection with no circular dependencies"""
        tasks = [
            {'id': 1, 'dependencies': []},
            {'id': 2, 'dependencies': [1]},
            {'id': 3, 'dependencies': [2]}
        ]
        
        cycles = detect_circular_dependencies(tasks)
        self.assertEqual(len(cycles), 0)
    
    def test_simple_circular_dependency(self):
        """Test detection of simple circular dependency (A->B->A)"""
        tasks = [
            {'id': 1, 'dependencies': [2]},
            {'id': 2, 'dependencies': [1]}
        ]
        
        cycles = detect_circular_dependencies(tasks)
        self.assertGreater(len(cycles), 0)
        
        # Check if both tasks are in a cycle
        for cycle in cycles:
            if 1 in cycle:
                self.assertIn(2, cycle)
    
    def test_complex_circular_dependency(self):
        """Test detection of complex circular dependency (A->B->C->A)"""
        tasks = [
            {'id': 1, 'dependencies': [2]},
            {'id': 2, 'dependencies': [3]},
            {'id': 3, 'dependencies': [1]}
        ]
        
        cycles = detect_circular_dependencies(tasks)
        self.assertGreater(len(cycles), 0)
        
        # All three tasks should be in a cycle
        for cycle in cycles:
            if 1 in cycle:
                self.assertIn(2, cycle)
                self.assertIn(3, cycle)
    
    def test_has_circular_dependency_check(self):
        """Test individual task circular dependency check"""
        tasks = [
            {'id': 1, 'dependencies': [2]},
            {'id': 2, 'dependencies': [1]},
            {'id': 3, 'dependencies': []}
        ]
        
        # Tasks 1 and 2 should be in a circular dependency
        self.assertTrue(has_circular_dependency(1, tasks))
        self.assertTrue(has_circular_dependency(2, tasks))
        
        # Task 3 should not be in a circular dependency
        self.assertFalse(has_circular_dependency(3, tasks))
    
    def test_circular_dependency_penalty(self):
        """Test that circular dependencies receive score penalty"""
        tasks = [
            {'id': 1, 'dependencies': [2]},
            {'id': 2, 'dependencies': [1]}
        ]
        
        score, explanation = calculate_dependency_score(1, tasks)
        
        # Should receive zero score and warning message
        self.assertEqual(score, 0.0)
        self.assertIn('CIRCULAR DEPENDENCY', explanation)


class AnalyzeTasksTests(TestCase):
    """Test cases for task analysis and sorting"""
    
    def setUp(self):
        """Set up test data"""
        self.now = timezone.now()
        
        self.tasks = [
            {
                'id': 1,
                'title': 'Critical Bug Fix',
                'due_date': self.now + timedelta(hours=6),
                'estimated_hours': 2.0,
                'importance': 10,
                'dependencies': []
            },
            {
                'id': 2,
                'title': 'Documentation Update',
                'due_date': self.now + timedelta(days=7),
                'estimated_hours': 1.0,
                'importance': 3,
                'dependencies': []
            },
            {
                'id': 3,
                'title': 'Feature Implementation',
                'due_date': self.now + timedelta(days=3),
                'estimated_hours': 10.0,
                'importance': 8,
                'dependencies': [1]
            }
        ]
    
    def test_analyze_tasks_returns_all_tasks(self):
        """Test that analyze_tasks returns all input tasks"""
        result = analyze_tasks(self.tasks, 'smart_balance')
        self.assertEqual(len(result), len(self.tasks))
    
    def test_analyze_tasks_sorted_by_priority(self):
        """Test that tasks are sorted by priority score (descending)"""
        result = analyze_tasks(self.tasks, 'smart_balance')
        
        # Verify sorting
        for i in range(len(result) - 1):
            self.assertGreaterEqual(
                result[i]['priority_score'],
                result[i + 1]['priority_score']
            )
    
    def test_analyze_tasks_includes_scoring_details(self):
        """Test that analysis includes all scoring components"""
        result = analyze_tasks(self.tasks, 'smart_balance')
        
        for task in result:
            self.assertIn('priority_score', task)
            self.assertIn('priority_level', task)
            self.assertIn('urgency_score', task)
            self.assertIn('importance_score', task)
            self.assertIn('effort_score', task)
            self.assertIn('dependency_score', task)
            self.assertIn('explanation', task)
    
    def test_get_top_suggestions(self):
        """Test getting top N task suggestions"""
        suggestions = get_top_suggestions(self.tasks, limit=2, strategy='smart_balance')
        
        # Should return exactly 2 tasks
        self.assertEqual(len(suggestions), 2)
        
        # Should include recommendation text
        for suggestion in suggestions:
            self.assertIn('recommendation', suggestion)
    
    def test_fastest_wins_strategy(self):
        """Test that fastest_wins strategy prioritizes low-effort tasks"""
        # Add a very quick task
        quick_task = {
            'id': 4,
            'title': 'Quick Task',
            'due_date': self.now + timedelta(days=5),
            'estimated_hours': 0.5,
            'importance': 5,
            'dependencies': []
        }
        
        tasks_with_quick = self.tasks + [quick_task]
        result = analyze_tasks(tasks_with_quick, 'fastest_wins')
        
        # Quick task should rank relatively high
        quick_task_result = next(t for t in result if t['id'] == 4)
        self.assertGreater(quick_task_result['priority_score'], 50)


class APIEndpointTests(TestCase):
    """Test cases for API endpoints"""
    
    def setUp(self):
        """Set up test client and data"""
        self.client = Client()
        self.now = timezone.now()
        
        self.test_tasks = [
            {
                'id': 1,
                'title': 'Test Task 1',
                'due_date': (self.now + timedelta(days=2)).isoformat(),
                'estimated_hours': 5.0,
                'importance': 8,
                'dependencies': []
            },
            {
                'id': 2,
                'title': 'Test Task 2',
                'due_date': (self.now + timedelta(days=1)).isoformat(),
                'estimated_hours': 2.0,
                'importance': 9,
                'dependencies': []
            }
        ]
    
    def test_analyze_endpoint_success(self):
        """Test successful task analysis via API"""
        response = self.client.post(
            '/api/tasks/analyze/',
            data=json.dumps({
                'tasks': self.test_tasks,
                'strategy': 'smart_balance'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('tasks', data)
        self.assertIn('strategy', data)
        self.assertIn('total_tasks', data)
        self.assertEqual(data['total_tasks'], 2)
    
    def test_analyze_endpoint_empty_tasks(self):
        """Test analyze endpoint with empty task list"""
        response = self.client.post(
            '/api/tasks/analyze/',
            data=json.dumps({
                'tasks': [],
                'strategy': 'smart_balance'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    def test_analyze_endpoint_invalid_data(self):
        """Test analyze endpoint with invalid data"""
        response = self.client.post(
            '/api/tasks/analyze/',
            data=json.dumps({
                'tasks': [{'title': 'Incomplete Task'}]  # Missing required fields
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_suggest_endpoint_success(self):
        """Test successful task suggestions via API"""
        response = self.client.post(
            '/api/tasks/suggest/',
            data=json.dumps({
                'tasks': self.test_tasks,
                'strategy': 'smart_balance',
                'limit': 2
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('suggestions', data)
        self.assertIn('suggestions_count', data)
        self.assertLessEqual(data['suggestions_count'], 2)
    
    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
    
    def test_strategies_info_endpoint(self):
        """Test strategies info endpoint"""
        response = self.client.get('/api/strategies/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check all strategies are present
        self.assertIn('smart_balance', data)
        self.assertIn('fastest_wins', data)
        self.assertIn('high_impact', data)
        self.assertIn('deadline_driven', data)
    
    def test_circular_dependency_detection_in_api(self):
        """Test that API detects circular dependencies"""
        circular_tasks = [
            {
                'id': 1,
                'title': 'Task 1',
                'due_date': (self.now + timedelta(days=2)).isoformat(),
                'estimated_hours': 5.0,
                'importance': 8,
                'dependencies': [2]
            },
            {
                'id': 2,
                'title': 'Task 2',
                'due_date': (self.now + timedelta(days=2)).isoformat(),
                'estimated_hours': 3.0,
                'importance': 7,
                'dependencies': [1]
            }
        ]
        
        response = self.client.post(
            '/api/tasks/analyze/',
            data=json.dumps({
                'tasks': circular_tasks,
                'strategy': 'smart_balance'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should include circular dependency warning
        self.assertIn('circular_dependencies', data)
        self.assertGreater(len(data['circular_dependencies']), 0)


class EdgeCaseTests(TestCase):
    """Test cases for edge cases and error handling"""
    
    def setUp(self):
        """Set up test data"""
        self.now = timezone.now()
    
    def test_task_with_invalid_dependencies(self):
        """Test handling of tasks with non-existent dependency IDs"""
        tasks = [
            {
                'id': 1,
                'title': 'Task 1',
                'due_date': self.now + timedelta(days=2),
                'estimated_hours': 5.0,
                'importance': 8,
                'dependencies': [999]  # Non-existent task ID
            }
        ]
        
        # Should not crash, just ignore invalid dependencies
        result = analyze_tasks(tasks, 'smart_balance')
        self.assertEqual(len(result), 1)
    
    def test_extreme_estimated_hours(self):
        """Test handling of extreme estimated hours values"""
        # Very small value
        score_small, _ = calculate_effort_score(0.1)
        self.assertGreaterEqual(score_small, 0)
        self.assertLessEqual(score_small, 100)
        
        # Very large value
        score_large, _ = calculate_effort_score(1000)
        self.assertGreaterEqual(score_large, 0)
        self.assertLessEqual(score_large, 100)
    
    def test_all_tasks_same_priority(self):
        """Test handling when all tasks have identical attributes"""
        tasks = [
            {
                'id': i,
                'title': f'Task {i}',
                'due_date': self.now + timedelta(days=5),
                'estimated_hours': 5.0,
                'importance': 7,
                'dependencies': []
            }
            for i in range(1, 4)
        ]
        
        result = analyze_tasks(tasks, 'smart_balance')
        
        # All tasks should have same score
        scores = [t['priority_score'] for t in result]
        self.assertEqual(len(set(scores)), 1)
    
    def test_single_task_analysis(self):
        """Test analysis with only one task"""
        task = {
            'id': 1,
            'title': 'Single Task',
            'due_date': self.now + timedelta(days=2),
            'estimated_hours': 3.0,
            'importance': 6,
            'dependencies': []
        }
        
        result = analyze_tasks([task], 'smart_balance')
        self.assertEqual(len(result), 1)
        self.assertIn('priority_score', result[0])
