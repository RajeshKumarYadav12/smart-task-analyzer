"""
Smart Task Priority Scoring Algorithm

This module implements a sophisticated task prioritization system that balances
multiple factors to determine which tasks should be tackled first.

ALGORITHM OVERVIEW:
===================
The scoring algorithm considers four main components:

1. URGENCY SCORE (0-100 points)
   - Based on time until due date
   - Past due tasks get penalties
   - Imminent deadlines get urgency boosts
   
2. IMPORTANCE SCORE (0-100 points)
   - Direct mapping from user's importance rating (1-10)
   - Scaled to 0-100 range
   
3. EFFORT SCORE (0-100 points)
   - Rewards "quick wins" (low effort tasks)
   - Uses inverse relationship with estimated hours
   - Encourages completing small tasks to build momentum
   
4. DEPENDENCY SCORE (0-100 points)
   - Rewards tasks that unblock other tasks
   - Counts how many tasks depend on this one
   - Detects and penalizes circular dependencies

FINAL SCORE CALCULATION:
========================
Priority Score = (urgency_weight × urgency_score) + 
                 (importance_weight × importance_score) +
                 (effort_weight × effort_score) +
                 (dependency_weight × dependency_score)

Different strategies adjust these weights to emphasize different priorities.
"""

from datetime import datetime, timedelta
from django.utils import timezone
from typing import List, Dict, Tuple, Set


# ============================================================================
# CONFIGURABLE WEIGHTS FOR DIFFERENT STRATEGIES
# ============================================================================

STRATEGY_WEIGHTS = {
    'smart_balance': {
        'urgency': 0.30,
        'importance': 0.30,
        'effort': 0.20,
        'dependency': 0.20,
    },
    'fastest_wins': {
        'urgency': 0.15,
        'importance': 0.20,
        'effort': 0.50,  # Heavy emphasis on low-effort tasks
        'dependency': 0.15,
    },
    'high_impact': {
        'urgency': 0.15,
        'importance': 0.45,  # Heavy emphasis on importance
        'effort': 0.10,
        'dependency': 0.30,  # Also consider blocking tasks
    },
    'deadline_driven': {
        'urgency': 0.60,  # Heavy emphasis on deadlines
        'importance': 0.20,
        'effort': 0.10,
        'dependency': 0.10,
    },
}


# ============================================================================
# CIRCULAR DEPENDENCY DETECTION
# ============================================================================

def detect_circular_dependencies(tasks: List[Dict]) -> List[Set[int]]:
    """
    Detect circular dependencies using depth-first search.
    
    A circular dependency occurs when Task A depends on Task B, 
    and Task B (directly or indirectly) depends on Task A.
    
    Args:
        tasks: List of task dictionaries
        
    Returns:
        List of sets, where each set contains task IDs involved in a cycle
    """
    # Build adjacency list: task_id -> list of tasks it depends on
    graph = {}
    task_ids = set()
    
    for task in tasks:
        task_id = task.get('id')
        if task_id is None:
            continue
        task_ids.add(task_id)
        dependencies = task.get('dependencies', [])
        graph[task_id] = dependencies
    
    cycles = []
    visited = set()
    rec_stack = set()
    
    def dfs(node: int, path: List[int]) -> bool:
        """DFS helper to detect cycles"""
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in task_ids:
                continue  # Skip invalid dependencies
                
            if neighbor not in visited:
                if dfs(neighbor, path.copy()):
                    return True
            elif neighbor in rec_stack:
                # Found a cycle
                cycle_start = path.index(neighbor)
                cycle = set(path[cycle_start:])
                if cycle not in cycles:
                    cycles.append(cycle)
                return True
        
        rec_stack.remove(node)
        return False
    
    # Check each node
    for task_id in task_ids:
        if task_id not in visited:
            dfs(task_id, [])
    
    return cycles


def has_circular_dependency(task_id: int, tasks: List[Dict]) -> bool:
    """
    Check if a specific task is involved in a circular dependency.
    
    Args:
        task_id: ID of the task to check
        tasks: List of all tasks
        
    Returns:
        True if task is part of a circular dependency
    """
    cycles = detect_circular_dependencies(tasks)
    for cycle in cycles:
        if task_id in cycle:
            return True
    return False


# ============================================================================
# INDIVIDUAL SCORING COMPONENTS
# ============================================================================

def calculate_urgency_score(due_date: datetime, current_time: datetime = None) -> Tuple[float, str]:
    """
    Calculate urgency score based on time until due date.
    
    Scoring logic:
    - Past due: Base score minus penalty (can go negative)
    - Due within 24 hours: 90-100 points
    - Due within 3 days: 70-90 points
    - Due within 1 week: 50-70 points
    - Due within 2 weeks: 30-50 points
    - Due after 2 weeks: 0-30 points
    
    Args:
        due_date: Task due date
        current_time: Current time (defaults to now)
        
    Returns:
        Tuple of (score, explanation)
    """
    if current_time is None:
        current_time = timezone.now()
    
    # Calculate time difference
    time_diff = due_date - current_time
    hours_until_due = time_diff.total_seconds() / 3600
    days_until_due = hours_until_due / 24
    
    # Past due - apply penalty
    if hours_until_due < 0:
        days_overdue = abs(days_until_due)
        # Penalty increases with time overdue
        penalty = min(50, days_overdue * 10)
        score = max(0, 40 - penalty)
        explanation = f"OVERDUE by {abs(days_until_due):.1f} days (penalty applied)"
    
    # Critical: Due within 24 hours
    elif hours_until_due <= 24:
        score = 90 + (10 * (1 - hours_until_due / 24))
        explanation = f"CRITICAL: Due in {hours_until_due:.1f} hours"
    
    # High urgency: Due within 3 days
    elif days_until_due <= 3:
        score = 70 + (20 * (1 - (days_until_due - 1) / 2))
        explanation = f"HIGH URGENCY: Due in {days_until_due:.1f} days"
    
    # Medium urgency: Due within 1 week
    elif days_until_due <= 7:
        score = 50 + (20 * (1 - (days_until_due - 3) / 4))
        explanation = f"MEDIUM URGENCY: Due in {days_until_due:.1f} days"
    
    # Low urgency: Due within 2 weeks
    elif days_until_due <= 14:
        score = 30 + (20 * (1 - (days_until_due - 7) / 7))
        explanation = f"LOW URGENCY: Due in {days_until_due:.1f} days"
    
    # Minimal urgency: Due after 2 weeks
    else:
        score = max(0, 30 * (1 - (days_until_due - 14) / 30))
        explanation = f"Minimal urgency: Due in {days_until_due:.1f} days"
    
    return round(score, 2), explanation


def calculate_importance_score(importance: int) -> Tuple[float, str]:
    """
    Convert importance rating (1-10) to score (0-100).
    
    Simple linear mapping with descriptive labels.
    
    Args:
        importance: User's importance rating (1-10)
        
    Returns:
        Tuple of (score, explanation)
    """
    score = (importance / 10) * 100
    
    if importance >= 9:
        label = "CRITICAL"
    elif importance >= 7:
        label = "HIGH"
    elif importance >= 5:
        label = "MEDIUM"
    elif importance >= 3:
        label = "LOW"
    else:
        label = "MINIMAL"
    
    explanation = f"{label} importance (rated {importance}/10)"
    return round(score, 2), explanation


def calculate_effort_score(estimated_hours: float) -> Tuple[float, str]:
    """
    Calculate effort score - rewards quick wins (low effort tasks).
    
    Scoring logic:
    - Uses inverse relationship with estimated hours
    - Tasks under 1 hour get bonus points
    - Exponential decay for longer tasks
    
    Args:
        estimated_hours: Estimated hours to complete
        
    Returns:
        Tuple of (score, explanation)
    """
    # Quick wins (< 1 hour) get high scores
    if estimated_hours <= 1:
        score = 100 - (estimated_hours * 10)
        explanation = f"QUICK WIN: Only {estimated_hours:.1f}h effort"
    
    # Short tasks (1-4 hours) get good scores
    elif estimated_hours <= 4:
        score = 90 - ((estimated_hours - 1) * 15)
        explanation = f"Low effort: {estimated_hours:.1f}h estimated"
    
    # Medium tasks (4-8 hours) get moderate scores
    elif estimated_hours <= 8:
        score = 45 - ((estimated_hours - 4) * 7)
        explanation = f"Medium effort: {estimated_hours:.1f}h estimated"
    
    # Long tasks (8+ hours) get lower scores
    else:
        score = max(0, 17 - ((estimated_hours - 8) * 2))
        explanation = f"High effort: {estimated_hours:.1f}h estimated"
    
    return round(score, 2), explanation


def calculate_dependency_score(task_id: int, tasks: List[Dict]) -> Tuple[float, str]:
    """
    Calculate dependency score based on how many tasks depend on this one.
    
    Tasks that block other tasks should be prioritized higher.
    Penalize tasks involved in circular dependencies.
    
    Args:
        task_id: ID of the task being scored
        tasks: List of all tasks
        
    Returns:
        Tuple of (score, explanation)
    """
    # Check for circular dependency
    if has_circular_dependency(task_id, tasks):
        return 0.0, "CIRCULAR DEPENDENCY DETECTED - requires resolution"
    
    # Count how many tasks depend on this one
    dependent_count = 0
    for task in tasks:
        dependencies = task.get('dependencies', [])
        if task_id in dependencies:
            dependent_count += 1
    
    # Score based on number of dependent tasks
    if dependent_count == 0:
        score = 20
        explanation = "No tasks blocked"
    elif dependent_count == 1:
        score = 50
        explanation = f"Blocks {dependent_count} task"
    elif dependent_count == 2:
        score = 70
        explanation = f"Blocks {dependent_count} tasks"
    elif dependent_count >= 3:
        score = 90 + min(10, (dependent_count - 3) * 2)
        explanation = f"CRITICAL BLOCKER: Blocks {dependent_count} tasks"
    
    return round(score, 2), explanation


# ============================================================================
# MAIN SCORING FUNCTION
# ============================================================================

def calculate_priority_score(task: Dict, tasks: List[Dict], strategy: str = 'smart_balance') -> Dict:
    """
    Calculate the final priority score for a task.
    
    This is the main function that combines all scoring components
    according to the selected strategy.
    
    Args:
        task: Task dictionary with all required fields
        tasks: List of all tasks (needed for dependency analysis)
        strategy: Scoring strategy to use
        
    Returns:
        Dictionary with detailed scoring breakdown
    """
    # Get strategy weights
    weights = STRATEGY_WEIGHTS.get(strategy, STRATEGY_WEIGHTS['smart_balance'])
    
    # Calculate individual component scores
    urgency_score, urgency_exp = calculate_urgency_score(task['due_date'])
    importance_score, importance_exp = calculate_importance_score(task['importance'])
    effort_score, effort_exp = calculate_effort_score(task['estimated_hours'])
    
    task_id = task.get('id')
    if task_id is not None:
        dependency_score, dependency_exp = calculate_dependency_score(task_id, tasks)
    else:
        dependency_score = 20
        dependency_exp = "No ID provided for dependency analysis"
    
    # Calculate weighted final score
    final_score = (
        weights['urgency'] * urgency_score +
        weights['importance'] * importance_score +
        weights['effort'] * effort_score +
        weights['dependency'] * dependency_score
    )
    
    # Determine priority level
    if final_score >= 75:
        priority_level = "HIGH"
    elif final_score >= 50:
        priority_level = "MEDIUM"
    else:
        priority_level = "LOW"
    
    # Build comprehensive explanation
    explanation_parts = [
        f"Urgency: {urgency_exp}",
        f"Importance: {importance_exp}",
        f"Effort: {effort_exp}",
        f"Dependencies: {dependency_exp}"
    ]
    
    explanation = " | ".join(explanation_parts)
    
    return {
        'priority_score': round(final_score, 2),
        'priority_level': priority_level,
        'explanation': explanation,
        'urgency_score': urgency_score,
        'importance_score': importance_score,
        'effort_score': effort_score,
        'dependency_score': dependency_score,
    }


def analyze_tasks(tasks: List[Dict], strategy: str = 'smart_balance') -> List[Dict]:
    """
    Analyze and sort a list of tasks by priority.
    
    Args:
        tasks: List of task dictionaries
        strategy: Scoring strategy to use
        
    Returns:
        List of tasks sorted by priority (highest first) with scores
    """
    # Validate strategy
    if strategy not in STRATEGY_WEIGHTS:
        strategy = 'smart_balance'
    
    # Calculate scores for all tasks
    analyzed_tasks = []
    for task in tasks:
        scoring_result = calculate_priority_score(task, tasks, strategy)
        
        # Combine task data with scoring results
        analyzed_task = {
            **task,
            **scoring_result
        }
        analyzed_tasks.append(analyzed_task)
    
    # Sort by priority score (descending)
    analyzed_tasks.sort(key=lambda x: x['priority_score'], reverse=True)
    
    return analyzed_tasks


def get_top_suggestions(tasks: List[Dict], limit: int = 3, strategy: str = 'smart_balance') -> List[Dict]:
    """
    Get the top N tasks to work on based on priority analysis.
    
    Args:
        tasks: List of task dictionaries
        limit: Number of suggestions to return
        strategy: Scoring strategy to use
        
    Returns:
        List of top priority tasks with detailed recommendations
    """
    analyzed = analyze_tasks(tasks, strategy)
    top_tasks = analyzed[:limit]
    
    # Add recommendation reasons
    for i, task in enumerate(top_tasks):
        rank = i + 1
        task['recommendation'] = f"Ranked #{rank}: {task['explanation']}"
    
    return top_tasks
