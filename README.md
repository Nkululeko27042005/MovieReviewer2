Movie Reviewer Application
A full-featured social platform for movie enthusiasts to share, discover, and discuss movie reviews.

🚀 Quick Start
bash
# Clone and setup
git clone https://github.com/yourusername/movie-reviewer-app.git
cd movie-reviewer-app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python reset_db.py

# Run application
python run.py
✨ Features
User System: Register/Login with roles (Regular, Reviewer, Admin)

Reviews: Create detailed reviews with ratings, pros/cons, and images

Social: Like, save, comment, follow users

Feed: Personalized feed based on favorite genres

Notifications: Real-time alerts for social activity

Analytics: User and review performance metrics

Admin: Dashboard, report management, user moderation

🛠️ Tech Stack
Backend: Flask, SQLAlchemy, Flask-Login

Database: SQLite (dev) / PostgreSQL (prod)

Frontend: HTML, CSS, JavaScript (vanilla)

Icons: Font Awesome

👤 Default Login
Email: admin@moviereviewer.com

Password: admin123

Demo Users: movie_buff, film_critic, casual_viewer, cinephile (all password: password123)

📁 Project Structure
text
app/
├── api/          # API routes
├── forms/        # WTForms
├── models/       # Database models
├── services/     # Business logic
├── static/       # CSS, JS, uploads
└── templates/    # HTML templates
🔧 Commands
bash
# Database reset
python reset_db.py

# Run development server
python run.py

# Create migration
flask db migrate -m "message"

# Apply migration
flask db upgrade
🔒 Environment Variables
Create .env file:

env
FLASK_APP=run.py
FLASK_CONFIG=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///movie_reviewer.db
📝 License
MIT License

Built with ❤️ for movie lovers
