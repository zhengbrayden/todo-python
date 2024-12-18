# To-Do List API

A Django REST API for managing personal to-do lists with user authentication and CRUD functionality.

## Features
- User registration and authentication using JWT tokens
- Create, read, update, and delete todo items
- User-specific todo lists
- RESTful API endpoints

## API Endpoints

### Authentication

#### Register User
- **POST** `/api/register/`
- **Body**:
```json
{
    "name": "username",
    "email": "user@example.com",
    "password": "yourpassword"
}
```
- **Response**: JWT access token and user details

#### Login
- **POST** `/api/login/`
- **Body**:
```json
{
    "name": "username",  // or email address
    "password": "yourpassword"
}
```
- **Response**: JWT access token and user details

### Todo Operations

All todo operations require authentication. Include the JWT token in the Authorization header:
`Authorization: Bearer <your_jwt_token>`

#### Get All Todos
- **GET** `/api/todos/`
- **Query Parameters**: 
  - `page`: Page number (optional)
  - `limit`: Items per page (optional)
- **Response**:
```json
{
    "data": [
        {
            "id": 1,
            "title": "Task Title",
            "description": "Task Description",
            "created_at": "timestamp",
            "updated_at": "timestamp"
        }
    ],
    "page": 1,
    "limit": 10,
    "total": 1
}
```

#### Create Todo
- **POST** `/api/todos/`
- **Body**:
```json
{
    "title": "Task Title",
    "description": "Task Description"
}
```

#### Update Todo
- **PUT** `/api/todos/{id}/`
- **Body**:
```json
{
    "title": "Updated Title",
    "description": "Updated Description"
}
```

#### Delete Todo
- **DELETE** `/api/todos/{id}/`

## Local Setup

1. Clone the repository
```bash
git clone <repository-url>
```

2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
Create a `.env` file in the root directory with:
```
SECRET_KEY=your_secret_key
```

5. Run migrations
```bash
python manage.py migrate
```

6. Start the development server
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

## Testing
You can use the provided `api-tests.http` file to test the endpoints if you're using VS Code with the REST Client extension.
