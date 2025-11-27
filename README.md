SMART TASK ANALYZER

An intelligent task prioritization system built with Django and JavaScript that analyzes tasks based on urgency, importance, effort, and dependencies.


SETUP INSTRUCTIONS

Prerequisites:

Python 3.8 or higher
pip package manager

Backend Setup:

1. Navigate to backend directory: cd backend
2. Create virtual environment: python -m venv venv
3. Activate virtual environment: venv\Scripts\activate (Windows) or source venv/bin/activate (Mac/Linux)
4. Install dependencies: pip install -r requirements.txt
5. Run migrations: python manage.py migrate



Frontend Setup:
The frontend is static HTML/CSS/JavaScript with no build step required.

HOW TO RUN BACKEND AND FRONTEND

Running Backend:

1. Open terminal in backend directory
2. Start Django server: python manage.py runserver
3. Backend API available at: http://127.0.0.1:8000/api/

Running Frontend:
Method 1 - Python HTTP Server (Recommended):

1. Open terminal in frontend directory
2. Run: python -m http.server 8080
3. Open browser to: http://localhost:8080



Method 2 - Direct File Access:
Open frontend/index.html directly in browser (may have CORS issues)

Testing the Application:

1. Ensure backend is running on port 8000
2. Open frontend in browser
3. Load demo data: Open console (F12), type loadDemoData(), press Enter
4. Click "Analyze Tasks" button



ALGORITHM EXPLANATION

The Smart Task Analyzer implements a sophisticated multi-factor scoring algorithm that evaluates tasks across four key dimensions, each scored from 0-100 points. The final priority score determines task ranking and helps users focus on the most critical work.

Component 1 - Urgency Score: This component evaluates time sensitivity based on due dates. Tasks due within 24 hours receive 90-100 points marked as CRITICAL. Tasks due within 3 days get 70-90 points (HIGH URGENCY), within 1 week get 50-70 points (MEDIUM), within 2 weeks get 30-50 points (LOW), and beyond 2 weeks receive 0-30 points. Overdue tasks receive penalties that increase with time elapsed, preventing them from being forgotten while acknowledging their delayed status.

Component 2 - Importance Score: Users rate tasks from 1-10 for subjective importance, which directly maps to 0-100 points (rating times 10). This ensures user judgment is properly weighted. Ratings 9-10 are CRITICAL, 7-8 are HIGH, 5-6 are MEDIUM, 3-4 are LOW, and 1-2 are MINIMAL priority.

Component 3 - Effort Score: This component rewards "quick wins" using an inverse relationship with estimated hours. Tasks under 1 hour receive 90-100 points with a QUICK WIN bonus. Tasks requiring 1-4 hours get 45-90 points, 4-8 hours get 17-45 points, and tasks over 8 hours receive 0-17 points. This design encourages completing small tasks to build momentum and reduce backlog.

Component 4 - Dependency Score: This evaluates how many other tasks are blocked by the current task. Tasks with no dependents receive a baseline 20 points. Blocking 1 task gives 50 points, blocking 2 tasks gives 70 points, and blocking 3 or more tasks receives 90-100 points marked as CRITICAL BLOCKER. The system uses depth-first search (DFS) graph algorithms to detect circular dependencies, which receive 0 points as a penalty.



Strategy Weighting: Four strategies adjust component weights for different contexts. Smart Balance uses 30 percent urgency, 30 percent importance, 20 percent effort, 20 percent dependency for general use. Fastest Wins emphasizes 50 percent effort for momentum building. High Impact prioritizes 45 percent importance and 30 percent dependency for maximum impact. Deadline Driven allocates 60 percent to urgency for crisis situations.



Final Calculation: Priority Score equals (urgency_weight times urgency_score) plus (importance_weight times importance_score) plus (effort_weight times effort_score) plus (dependency_weight times dependency_score). Scores 75 and above are HIGH priority (red), 50-74 are MEDIUM (yellow), and below 50 are LOW (green). This transparent scoring system provides detailed explanations for each task ranking.




DESIGN DECISIONS

Architecture: The system uses clean architecture with separation of concerns. Scoring logic is isolated in scoring.py for testability, API logic in views.py, and validation in serializers.py. The stateless API design means tasks do not require database persistence, enabling on-demand analysis and easy scaling.

Algorithm Design: Normalized 0-100 scoring across all components provides consistency and intuitive weight interpretation. Multiple strategies demonstrate flexibility for different contexts. The strategy pattern allows easy addition of new prioritization modes without code duplication.

Frontend Design: Vanilla JavaScript eliminates framework overhead for fast, lightweight operation. Dual input modes (form and JSON bulk import) accommodate both casual users and power users. Real-time validation reduces server load and improves user experience.

Dependency Management: Graph algorithms (DFS) efficiently detect circular dependencies with O(V+E) complexity. The system handles complex dependency trees and provides clear warnings for cycle detection.



EDGE CASES HANDLED

1. Circular Dependencies: Detected using DFS graph traversal, penalized with 0 dependency score, user warned with specific task IDs
2. Overdue Tasks: Special penalty handling prevents ignoring past-due tasks, penalty increases with elapsed time
3. Invalid Dependencies: Non-existent task IDs gracefully ignored without system crashes
4. Extreme Values: Very small or large estimated hours clamped to valid 0-100 score ranges
5. Empty Task Lists: API returns appropriate 400 errors, frontend validates before submission
6. Identical Priorities: Stable sorting maintains original order for tied scores
7. Timezone Handling: All calculations use Django timezone utilities for cross-timezone compatibility
8. Missing Fields: Dependencies default to empty list, IDs auto-assigned when missing




TIME BREAKDOWN

Algorithm Design and Implementation: 3 hours (30 percent)
Backend API Development: 2 hours (20 percent)
Frontend Interface: 2.5 hours (25 percent)
Testing and Debugging: 1.5 hours (15 percent)
Documentation: 1 hour (10 percent)
Total Development Time: 10 hours



FUTURE IMPROVEMENTS

Algorithm: Machine learning for user preference adaptation, historical data for completion time prediction, team collaboration factors, resource constraint modeling
Features: User authentication and persistence, task history tracking, team collaboration, calendar integration, mobile app, notifications, Gantt chart visualization
Technical: GraphQL API option, WebSocket real-time updates, caching layer, CSV/Excel export, PDF reports, rate limiting
Testing: Integration tests, load testing, frontend unit tests, end-to-end testing, performance benchmarks
DevOps: Docker containerization, CI/CD pipeline, production deployment guide, monitoring and alerting



BONUS FEATURES ATTEMPTED

IMPLEMENTED BONUS 1 - Circular Dependency Detection and Visualization (COMPLETE):
Implementation: Full graph-based cycle detection using depth-first search algorithm in scoring.py (lines 100-190). The detect_circular_dependencies() function builds a dependency graph and applies DFS with recursion stack to identify cycles. Tasks involved in circular dependencies receive 0 dependency score as penalty. Frontend displays visual warning boxes showing specific task IDs affected by circular dependencies.
How It Works: When analyzing tasks, the system constructs a directed graph of dependencies and traverses it using DFS. If a node is encountered that is already in the recursion stack, a cycle is detected. All tasks in the cycle are flagged and displayed to the user with a warning message.
Testing: Add Task 1 depending on Task 2, and Task 2 depending on Task 1. The system will detect the cycle and display: "Warning: Circular dependencies detected in tasks: [1, 2]"



IMPLEMENTED BONUS 2 - Unit Tests for Scoring Algorithm (COMPLETE):
Implementation: Comprehensive test suite in tests.py with 30+ test cases covering all aspects of the scoring system.
Coverage Details:

- ScoringAlgorithmTests (15+ tests): Urgency calculations for past due/imminent/distant tasks, importance score mapping validation, effort score rewards for quick wins, dependency scoring with blockers, complete priority calculation, strategy variations
- CircularDependencyTests (5 tests): Simple circular dependency detection (A to B to A), complex multi-node cycles (A to B to C to A), individual task circular checks, penalty application verification
- APIEndpointTests (8 tests): Successful analysis requests, error handling, empty task validation, invalid data checks, suggest endpoint, health check, strategies endpoint, circular dependency API detection
- EdgeCaseTests (5 tests): Invalid dependencies handling, extreme estimated hours, identical task priorities, single task analysis
  How to Run: Navigate to backend directory and execute: python manage.py test
  Expected Output: "Ran 30+ tests in X.XXXs - OK"



Additional Features Beyond Bonuses:

Four distinct sorting strategies with configurable weights
Top 3 task suggestions endpoint with explanations
JSON bulk import/export for power users
Color-coded priority visualization (RED for high, YELLOW for medium, GREEN for low)
Responsive mobile-friendly design
Real-time form validation
Demo data loader for quick testing
Detailed component-level score breakdowns
Self-documenting API with strategy information endpoint



Run Tests Command: cd backend then python manage.py test

API Endpoints: /api/tasks/analyze/, /api/tasks/suggest/, /api/health/, /api/strategies/

Frontend Demo: Open console, type loadDemoData(), click Analyze Tasks


