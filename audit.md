# EdukaTrack Comprehensive Audit & Codebase Breakdown

## 1. High-Level Architecture
EdukaTrack employs a **Monolithic Client-Server Architecture** utilizing Server-Side Rendering (SSR) alongside RESTful API endpoints.
* **Design Patterns:** 
  * **MVC (Model-View-Controller):** The application strictly separates database schema (`models.py`), presentation logic (`templates/` and `static/`), and routing/business logic (`app.py`).
  * **Factory Pattern:** The application initializes via a `create_app` factory in `app.py`, allowing for easier testing and environment-specific configurations.
  * **Singleton Pattern:** Modules like `auth.py` and `id_generator.py` instantiate global manager objects (`auth_manager`, `id_generator`) that maintain state across the app's lifecycle.
* **Data Flow:** The client (browser) makes HTTP requests. The routing layer (`app.py`) processes the request, delegates authentication to `auth.py`, fetches/mutates data using the SQLAlchemy ORM (`models.py`) and custom data structures (`structures.py`), and finally responds by rendering a Jinja2 HTML template or returning JSON for AJAX calls handled by client-side JavaScript.

## 2. Technology Stack & Dependencies
* **Core Language:** Python 3.11+
* **Backend Framework:** Flask 3.0.0 (Handles routing, templating, and HTTP requests)
* **Database ORM:** Flask-SQLAlchemy / SQLAlchemy (Object-Relational Mapping for database interactions)
* **Security & Authentication:** 
  * `bcrypt==4.1.1` (Password hashing)
  * `PyJWT==2.8.0` (JSON Web Token management for secure stateless auth mechanisms)
* **Frontend:** HTML5, Vanilla JavaScript, Vanilla CSS, and Jinja2 (Flask's default templating engine)
* **Production Server:** Gunicorn==21.2.0
* **Utilities:** `python-dotenv` (Environment variable management), `flask-cors` (Cross-Origin Resource Sharing)

## 3. Folder Structure
```text
EdukaTrack/
├── static/                 # Static assets served to the client
│   ├── css/                # Stylesheets defining the visual aesthetics
│   ├── js/                 # Client-side JavaScript for interactivity
│   └── pixelbook.gif       # Image assets
├── templates/              # Jinja2 HTML templates for Server-Side Rendering
│   ├── admin/              # Views exclusively for Administrator roles
│   ├── student/            # Views exclusively for Student roles
│   ├── teacher/            # Views exclusively for Teacher roles
│   └── login.html          # Authentication entry point
├── app.py                  # Core Flask application, routing, and controllers
├── auth.py                 # Authentication logic and JWT handling
├── id_generator.py         # Utility for generating unique system IDs
├── main.py                 # Application execution entry point
├── models.py               # Database schemas and ORM definitions
├── requirements.txt        # Python dependency manifest
├── seed.py                 # Database population script (dummy/initial data)
├── structures.py           # Custom data structures (Queues, HashMaps, etc.)
└── README.md               # Project documentation and setup guide
```

## 4. File-by-File Breakdown

### Root Directory (Backend Logic)
* **[`app.py`](file:///Ubuntu/home/quo-jeric/EdukaTrack/app.py)**
  * **Core Responsibility:** The backbone of the application. Initializes the Flask app, connects the database, registers middleware, and defines all HTTP routes (both HTML rendering and JSON API endpoints) for admins, teachers, and students.
  * **Key Exports:** `create_app` function.
  * **Dependencies:** `models.py`, `auth.py`, `structures.py`, `id_generator.py`, Flask, SQLAlchemy, bcrypt.
* **[`main.py`](file:///Ubuntu/home/quo-jeric/EdukaTrack/main.py)**
  * **Core Responsibility:** A simple execution entry point that imports the Flask app instance and runs the development server.
  * **Key Exports:** Runs the app block (`if __name__ == '__main__':`).
  * **Dependencies:** `app.py`.
* **[`models.py`](file:///Ubuntu/home/quo-jeric/EdukaTrack/models.py)**
  * **Core Responsibility:** Defines the relational database schema using SQLAlchemy. It creates the tables and relationships for Users, Students, Teachers, Admins, Schedules, Enrollments, Grades, and Assignments.
  * **Key Exports:** `db` (SQLAlchemy instance), `User`, `Admin`, `Teacher`, `Student`, `ClassSchedule`, etc.
  * **Dependencies:** `flask_sqlalchemy`, `datetime`.
* **[`auth.py`](file:///Ubuntu/home/quo-jeric/EdukaTrack/auth.py)**
  * **Core Responsibility:** Manages security by handling JWT creation, validation, and user session token management.
  * **Key Exports:** `AuthManager` class, `auth_manager` instance.
  * **Dependencies:** `jwt`, `datetime`, `os`.
* **[`structures.py`](file:///Ubuntu/home/quo-jeric/EdukaTrack/structures.py)**
  * **Core Responsibility:** Implements custom data structures (likely for academic requirements) used for optimizing specific logic, such as queuing enrollments or tracking scheduling conflicts.
  * **Key Exports:** `EnrollmentQueue`, `DynamicArray`, `ConflictSet`, `HashMap`, `UniqueIDSet`, `StudentList`.
  * **Dependencies:** `collections`.
* **[`id_generator.py`](file:///Ubuntu/home/quo-jeric/EdukaTrack/id_generator.py)**
  * **Core Responsibility:** Generates and validates unique, formatted identifier strings for students and teachers (e.g., `S-20250001`).
  * **Key Exports:** `IDGenerator` class, `id_generator` instance.
  * **Dependencies:** `random`, `string`, `os`.
* **[`seed.py`](file:///Ubuntu/home/quo-jeric/EdukaTrack/seed.py)**
  * **Core Responsibility:** A developer utility script that wipes the existing database and populates it with dummy data (admin accounts, departments, sample students, and teachers) for testing.
  * **Key Exports:** Execution script block.
  * **Dependencies:** `app.py`, `models.py`, `id_generator.py`, `bcrypt`.
* **[`requirements.txt`](file:///Ubuntu/home/quo-jeric/EdukaTrack/requirements.txt)**
  * **Core Responsibility:** Lists all Python pip dependencies required to build and run the application environment.
* **[`README.md`](file:///Ubuntu/home/quo-jeric/EdukaTrack/README.md)**
  * **Core Responsibility:** The project's documentation detailing requirements, installation, use cases, and troubleshooting.

### Static Directory (Frontend Assets)
* **[`static/js/admin.js`](file:///Ubuntu/home/quo-jeric/EdukaTrack/static/js/admin.js)**
  * **Core Responsibility:** Handles client-side interactivity on the Admin dashboard, making AJAX API calls to manage users, approve enrollments, and resolve scheduling conflicts.
* **[`static/js/student.js`](file:///Ubuntu/home/quo-jeric/EdukaTrack/static/js/student.js)**
  * **Core Responsibility:** Handles student dashboard interactions, such as viewing grades, submitting assignments, and requesting enrollments asynchronously.
* **[`static/js/teacher.js`](file:///Ubuntu/home/quo-jeric/EdukaTrack/static/js/teacher.js)**
  * **Core Responsibility:** Manages teacher-specific UI logic like grading assignments, taking attendance, and updating class statuses via API endpoints.
* **[`static/css/styles.css`](file:///Ubuntu/home/quo-jeric/EdukaTrack/static/css/styles.css)**
  * **Core Responsibility:** The global stylesheet providing the visual aesthetics, layout, responsive design, and CSS variables for the entire web application.

### Templates Directory (HTML Views)
* **[`templates/login.html`](file:///Ubuntu/home/quo-jeric/EdukaTrack/templates/login.html)**
  * **Core Responsibility:** The landing page providing the authentication form for users to enter credentials and access the system.
* **[`templates/admin/dashboard.html`](file:///Ubuntu/home/quo-jeric/EdukaTrack/templates/admin/dashboard.html)**
  * **Core Responsibility:** The administrative interface layout, containing modals, tables, and navigation structures for system management.
* **[`templates/teacher/dashboard.html`](file:///Ubuntu/home/quo-jeric/EdukaTrack/templates/teacher/dashboard.html)**
  * **Core Responsibility:** The UI layout for teachers to manage their assigned classes, view student submissions, and input grades.
* **[`templates/student/dashboard.html`](file:///Ubuntu/home/quo-jeric/EdukaTrack/templates/student/dashboard.html)**
  * **Core Responsibility:** The UI layout for students to view their schedules, read announcements, track academic progress, and submit assignments.

## 5. Architectural Issues & Debt
1. **The `app.py` Monolith:** `app.py` appears to act as a "God file", containing the app factory, configurations, and *all* routing logic. In Flask, this is tightly coupled and scales poorly. **Recommendation:** Implement **Flask Blueprints** to separate routes into domain-specific modules (e.g., `routes/admin.py`, `routes/auth.py`).
2. **Reinventing the Wheel in `structures.py`:** Writing custom `HashMap`, `DynamicArray`, and `StudentList` classes in Python is generally an anti-pattern unless this is an educational/academic project. Python's built-in `dict`, `list`, and `set` are implemented in C, meaning custom Python implementations add technical debt and are drastically slower.
3. **Global Singletons:** Instantiating `id_generator` and `auth_manager` at the module level and directly importing the instances across the app can lead to race conditions in a multi-threaded server like Gunicorn if these objects maintain state.
4. **Hybrid API Strategy:** The application mixes standard form submissions (SSR rendering) with AJAX API endpoints (`jsonify`) inside the same routing file. It's best practice to separate web routes (serving HTML) from API endpoints (serving JSON) into distinct namespaces (e.g., `/api/v1/...`).
