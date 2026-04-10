# Movie Review & Recommendation System

A full-featured web application that allows users to explore movies, write reviews, maintain favorites, and receive personalized movie recommendations based on their preferences. The system includes admin capabilities for content moderation.

## Features

### User Features
- **User Authentication**: Secure signup, login, and logout functionality
- **Movie Browsing**: Browse top-rated movies and personalized recommendations
- **Movie Search**: Search for movies using the TMDB (The Movie Database) API
- **Favorites Management**: Add or remove movies from personal favorites list
- **Reviews & Ratings**: Submit movie reviews with ratings (1-5 stars)
- **Personalized Recommendations**: Get movie recommendations based on favorite movies
- **Account Management**: Update username and password
- **Review Reporting**: Report inappropriate reviews to administrators

### Admin Features
- **Admin Dashboard**: View all reported reviews
- **Review Moderation**: Dismiss false reports or delete inappropriate reviews
- **User Management**: Admin privileges for content moderation

## Technology Stack

### Backend
- **Framework**: Flask with Flask-RESTful
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Session-based with password hashing (Werkzeug)
- **API Integration**: TMDB (The Movie Database) API

### Frontend
- **Templates**: HTML templates with Jinja2
- **Static Files**: CSS, JavaScript, images
- **Routing**: Flask URL routing

## Project Structure

```
project/
├── app.py                 # Main application file
├── models.py             # Database models (User, Favourites, Review, Report)
├── auth.py               # Authentication decorators
├── tmdb.py               # TMDB API integration functions
├── backend_auth.py       # Backend authentication utilities
├── test.py               # Token management
├── html/
│   └── template/         # HTML templates directory
│       ├── index.html    # Landing page
│       ├── login.html    # Login page
│       ├── signup.html   # Registration page
│       ├── home.html     # User dashboard
│       ├── account.html  # User account page
│       ├── info.html     # Movie details page
│       ├── search.html   # Search results page
│       ├── editUser.html # Edit username form
│       ├── editPass.html # Edit password form
│       ├── admin_review.html # Admin review moderation page
│       └── login_error.html # Error page
├── static/               # Static files (CSS, JS, images)
└── database/            # Database directory (auto-created)
    └── database.db      # SQLite database file
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- TMDB API key (free tier available)

### Step 1: Clone the Repository
```bash
git clone (https://github.com/OliverRob06/Web-Application-Implementation.git)
cd Web-Application-Implementation
```

### Step 2: Install Dependencies
Create a `requirements.txt` file with the following content:

```txt
Flask==2.3.3
Flask-RESTful==0.3.9
Flask-SQLAlchemy==3.0.5
SQLAlchemy==2.0.19
requests==2.31.0
Werkzeug==2.3.7
```

Then install:
```bash
pip install -r requirements.txt
```

## Database Setup

The application automatically creates the database and tables on first run. The database will be created in the `database/` folder as `database.db`.

### Database Models

1. **User**: Stores user information
   - `id`: Primary key
   - `username`: Unique username
   - `password`: Hashed password
   - `admin`: Boolean flag for admin privileges

2. **Favourites**: Stores user favorite movies
   - `id`: Primary key
   - `userID`: Foreign key to User
   - `movieID`: TMDB movie ID

3. **Review**: Stores movie reviews
   - `id`: Primary key
   - `userID`: Foreign key to User
   - `movieID`: TMDB movie ID
   - `content`: Review text
   - `rating`: Integer rating (1-5)

4. **Report**: Stores review reports
   - `id`: Primary key
   - `reviewID`: Foreign key to Review
   - `userID`: Foreign key to User (who reported)

## Running the Application

### Start the Flask Server
```bash
python app.py
```

The server will start on:
- **URL**: `http://0.0.0.0:8000`
- **Debug Mode**: Enabled (auto-reloads on code changes)

### Access the Application
Open your web browser and navigate to: `http://localhost:8000`

## API Endpoints

The application provides a RESTful API for various operations:

### User API (`/api/users`)
- `GET /api/users` - Get all users
- `GET /api/users?username={username}` - Get specific user
- `POST /api/users` - Create new user
- `PUT /api/users/{userid}` - Update user (username or password)
- `DELETE /api/users` - Delete user

### Login API (`/api/login`)
- `POST /api/login` - Authenticate user and return token

### Favourites API (`/api/favourites`)
- `GET /api/favourites` - Get favorites (filter by username)
- `POST /api/favourites` - Add movie to favorites
- `DELETE /api/favourites` - Remove movie from favorites

### Reviews API (`/api/reviews`)
- `GET /api/reviews` - Get reviews (filter by movieID, userID, or username)
- `POST /api/reviews` - Submit a review
- `DELETE /api/reviews` - Delete a review

### Reports API (`/api/reports`)
- `GET /api/reports` - Get all reported reviews with counts
- `POST /api/reports` - Report a review
- `DELETE /api/reports` - Dismiss or delete reported reviews

## Usage Guide

### For Regular Users

1. **Sign Up**: Create a new account at `/signup`
2. **Login**: Access your account at `/login`
3. **Browse Movies**: View personalized recommendations on the home page
4. **Search**: Use the search feature to find specific movies
5. **View Movie Details**: Click on any movie to see:
   - Movie information (title, overview, genres, etc.)
   - Cast and crew details
   - User reviews and ratings
   - Add/remove from favorites
   - Submit your own review
6. **Manage Account**: Update username or password at `/account`
7. **Report Reviews**: Flag inappropriate reviews for admin review

### For Administrators

1. **Login** with admin credentials
2. **Access Admin Panel**: Automatically redirected to `/reviews` after login
3. **Review Reports**: View all reported reviews with report counts
4. **Take Action**:
   - **Dismiss**: Remove reports while keeping the review
   - **Delete**: Remove both reports and the review

## Features in Detail

### Personalized Recommendations
- Based on user's favorite movies
- Fetches recommendations from TMDB
- Randomly selects up to 20 recommendations
- Falls back to top-rated movies if no favorites exist

### Review System
- Rate movies from 1-10 points
- Write detailed reviews
- Edit/delete own reviews (future feature)
- View all reviews on movie pages

### Favorites System
- Save movies to personal collection
- Access favorites from account page
- Recommendations based on favorites

### Security Features
- Password hashing using Werkzeug
- Session-based authentication
- Login required for protected routes
- Admin-only routes for moderation
- CSRF protection (via session)

## Troubleshooting

### Common Issues

1. **Database errors**: Delete the `database/database.db` file and restart the application
2. **Port already in use**: Change the port in `app.run()` or kill the process using port 8000
3. **TMDB API errors**: Verify your API key and internet connection
4. **Template not found**: Ensure templates are in `html/template/` folder
5. **Static files not loading**: Check that static folder is at the correct path

### Debug Mode
The application runs in debug mode, which provides:
- Automatic server reload on code changes
- Detailed error pages with stack traces
- Interactive debugger in the browser

## Future Enhancements

Potential features to add:
- Email verification for new accounts
- Social media sharing for reviews
- Advanced search filters (genre, year, rating)
- User profile pictures
- Watchlist feature
- Friend system and social features
- Average rating display for movies
- Sorting and filtering for reviews

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- [The Movie Database (TMDB)](https://www.themoviedb.org/) for providing the movie data API
- Flask and SQLAlchemy communities for excellent documentation

## Support

For issues, questions, or contributions, please open an issue in the repository or contact the development team.

---

**Note**: This application is for educational purposes. Ensure you comply with TMDB's API terms of service and implement proper security measures before deploying to production.
