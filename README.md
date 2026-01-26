# 📚 GCSE Progress Tracker

A comprehensive web application for tracking GCSE exam preparation progress, built with Django and powered by Anthropic's Claude AI for personalised learning roadmaps.

![Python](https://img.shields.io/badge/python-3.13.5-blue.svg)
![Django](https://img.shields.io/badge/django-6.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🎯 Overview

GCSE Progress Tracker helps students monitor their academic progress, set goals, and receive AI-powered personalized study recommendations. The application supports students and parents with role-specific dashboards.

### ✨ Key Features

**For Students**
- 📊 Progress dashboard with analytics (study streak, hours, completion %)
- 🤖 AI-powered personalised study roadmaps using Claude AI
- 📝 Subject management for all GCSE subjects
- 🎯 Term goal setting with deadline tracking
- 📚 Study session logging
- ✅ Interactive checklists with real-time progress
- 📈 Visual analytics with charts and graphs

**For Parents**
- 👨‍👩‍👧 Multi-student monitoring dashboard
- 🔔 Smart alerts (low activity, goals at risk, milestones, etc.)
- 📧 Email notifications with digest options
- 📊 Detailed progress views for each child
- 📜 Alert history with filtering

## 🚀 Quick Start

### Prerequisites

- Python 3.13.5 or higher
- pip (Python package manager)
- PostgreSQL (for production) or SQLite (for development)
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/gcse-progress-tracker.git
   cd gcse-progress-tracker
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your configuration:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ANTHROPIC_API_KEY=your-anthropic-api-key
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Create demo users (optional)**
   ```bash
   python manage.py create_demo_users
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   - Open your browser and go to `http://127.0.0.1:8000`
   - Admin panel: `http://127.0.0.1:8000/admin`

## 🏗️ Project Structure

```
gcse-progress-tracker/
├── config/                      # Project configuration
│   ├── settings.py             # Django settings with environment variables
│   ├── urls.py                 # Root URL configuration
│   └── wsgi.py                 # WSGI configuration
├── tracker/                     # Main application
│   ├── models.py               # Database models (11 models)
│   ├── views.py                # Views (35+ views)
│   ├── forms.py                # Forms (7 forms)
│   ├── urls.py                 # App URL patterns
│   ├── ai_service.py           # Claude AI integration
│   ├── alerts.py               # Alert generation system
│   ├── admin.py                # Admin interface customisation
│   ├── migrations/             # Database migrations (6 migrations)
│   ├── management/commands/    # Custom management commands
│   ├── templates/tracker/      # HTML templates (20+ templates)
│   ├── static/tracker/         # Static files (CSS, JS)
│   └── tests/                  # Test files (11 test modules)
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── README.md                  # This file
└── DEPLOYMENT.md              # Deployment guide
```

## 🗄️ Database Models

The application uses 11 core models organized into logical groups:

### User Management
- **UserProfile**: Extends Django User with role (student/parent), full name, year group, alert preferences

### Academic Tracking
- **Subject**: GCSE subjects (maths, english, science, etc.)
- **Feedback**: Teacher assessments with strengths, weaknesses, areas to improve
- **TermGoal**: Current level → target level with deadline tracking
- **StudySession**: Log study time with notes

### AI Roadmaps
- **Roadmap**: AI-generated study plan with title and overview
- **RoadmapStep**: Individual steps with category, difficulty, estimated hours
- **ChecklistItem**: Granular tasks with completion tracking
- **Resource**: Study materials (video/article/exercise)

### Parent Features
- **ProgressAlert**: 6 alert types with severity levels and preferences

## 🛠️ Core Technologies

- **Backend**: Django 6.0, Python 3.13.5
- **Database**: PostgreSQL (production), SQLite (development)
- **AI**: Anthropic Claude API (claude-sonnet-4-20250514)
- **Frontend**: HTML5, CSS3, JavaScript (Chart.js for visualizations)
- **Deployment**: Render.com with WhiteNoise for static files

## 📦 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Django secret key | Yes | - |
| `DEBUG` | Debug mode | No | False |
| `ANTHROPIC_API_KEY` | Claude AI API key | Yes | - |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | Yes | - |
| `DATABASE_URL` | PostgreSQL connection string | Production | - |
| `EMAIL_HOST` | SMTP server | Optional | - |
| `EMAIL_PORT` | SMTP port | Optional | 587 |
| `EMAIL_HOST_USER` | SMTP username | Optional | - |
| `EMAIL_HOST_PASSWORD` | SMTP password | Optional | - |
| `DEFAULT_FROM_EMAIL` | From email address | Optional | - |

## 🎓 Demo Users

After running `python manage.py create_demo_users`, you can log in with:

**Student Account**
- Username: `student_brother`
- Password: `password123`

**Parent Account**
- Username: `parent_mum`
- Password: `password123`

## 📚 Management Commands

```bash
# Create demo users
python manage.py create_demo_users

# Load sample data (subjects, feedback, goals, sessions, roadmaps)
python manage.py load_sample_data

# Send progress alerts to parents (use --dry-run to test)
python manage.py send_progress_alerts [--dry-run]
```

## 🧪 Testing

Run tests with:

```bash
# Run all tests
python manage.py test

# Run specific test file
python manage.py test tracker.tests.test_models

# Run with coverage report
coverage run --source='.' manage.py test
coverage report
```

**Test Coverage**: 150+ test cases, ~85% coverage

## 🔒 Security Features

- CSRF protection on all forms
- Secure password hashing with Django's default PBKDF2
- Role-based access control
- SQL injection protection via Django ORM
- XSS protection with template auto-escaping
- HTTPS enforcement in production
- Secure session cookies

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Anthropic**: For providing the Claude AI API
- **Django**: For the excellent web framework
- **Render**: For easy deployment and hosting

## 📞 Support

- **Documentation**: See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment help
- **Issues**: Open an issue on GitHub

---
