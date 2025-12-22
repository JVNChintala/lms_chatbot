# Canvas LMS Chatbot - Project Summary

## Overview
This is a streamlined Canvas LMS AI Assistant built with FastAPI, OpenAI, and Canvas API integration. The project focuses on three core components:
1. **FastAPI Backend** - RESTful API server
2. **OpenAI Integration** - GPT-4 for intelligent conversations and tool calling
3. **Canvas API Integration** - Full Canvas LMS operations

## Architecture

### Core Components

#### 1. FastAPI Application (main.py)
- **Purpose**: Main application server
- **Key Endpoints**:
  - `/inference` - Chat with AI assistant
  - `/analytics` - Get Canvas analytics
  - `/conversations` - Conversation management
  - `/demo-login` - Authentication
  - `/dashboard-widgets` - Dashboard data

#### 2. Canvas Agent (canvas_agent.py)
- **Purpose**: Orchestrates AI interactions with Canvas
- **Responsibilities**:
  - Intent classification
  - Tool selection and execution
  - Analytics generation
  - Usage tracking
  - Conversation management

#### 3. OpenAI Inference (inference_systems/openai_inference.py)
- **Purpose**: OpenAI API integration using Responses API
- **Features**:
  - Tool calling with function definitions
  - Conversation handling
  - Usage tracking
  - Error handling

#### 4. Canvas Integration (canvas_integration.py)
- **Purpose**: Canvas API wrapper
- **Operations**:
  - Course management (list, create, update, publish)
  - Module management
  - Assignment management (create, list, grade, submit)
  - User management (list, create, enroll)
  - Enrollment management

#### 5. Canvas Tools (canvas_tools.py)
- **Purpose**: Tool executor for Canvas operations
- **Features**:
  - Role-based tool access
  - Tool dispatch system
  - Error handling
  - Auto-enrollment for teachers

#### 6. Intent Classifier (intent_classifier.py)
- **Purpose**: Classify user intent to determine tool usage
- **Intents**:
  - list_courses
  - get_course_details
  - create_course
  - list_assignments
  - grade_assignment
  - create_module
  - enroll_user
  - general_question

#### 7. Analytics & Caching (analytics_cache.py)
- **Purpose**: Cache Canvas analytics to reduce API calls
- **Features**:
  - 5-minute cache duration
  - Role-specific analytics
  - Quick actions for each role

#### 8. Dashboard Widgets (dashboard_widgets.py)
- **Purpose**: Generate dashboard data for different roles
- **Widgets**:
  - Student: Courses, assignments, announcements
  - Teacher: Courses, stats, quick actions
  - Admin: System overview, recent courses

## Data Flow

### Chat Request Flow
```
User Message → FastAPI (/inference)
    ↓
Canvas Agent (process_message)
    ↓
Intent Classifier (classify_intent)
    ↓
[Tool Needed?]
    ↓ Yes
Canvas Tools (execute_tool)
    ↓
Canvas API (perform operation)
    ↓
OpenAI (format response)
    ↓
Return to User (with analytics)
```

### Analytics Flow
```
Frontend Request → FastAPI (/analytics)
    ↓
[Check Cache]
    ↓ Cache Miss
Analytics Cache (get_quick_analytics)
    ↓
Canvas API (fetch data)
    ↓
Cache Result
    ↓
Return to Frontend
```

## Role-Based Access Control

### Student
- List courses
- View course details
- List modules
- List assignments
- View assignment details
- Submit assignments
- View profile

### Teacher/Faculty/Instructor
- All student permissions
- Create courses (auto-enrolled as teacher)
- Publish/unpublish courses
- Create modules
- Create assignments
- Grade assignments
- View enrollments

### Admin
- All teacher permissions
- List all courses (account-level)
- List users
- Create users
- Enroll users in courses
- Full system access

## Database Schema

### Conversations (conversations.db)
```sql
conversations
- id (INTEGER PRIMARY KEY)
- canvas_user_id (INTEGER)
- title (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

messages
- id (INTEGER PRIMARY KEY)
- conversation_id (INTEGER)
- role (TEXT) -- 'user' or 'assistant'
- content (TEXT)
- created_at (TIMESTAMP)
```

### Usage Tracking (usage_tracker.db)
```sql
usage_logs
- id (INTEGER PRIMARY KEY)
- user_id (INTEGER)
- user_role (TEXT)
- inference_system (TEXT)
- model_name (TEXT)
- input_tokens (INTEGER)
- output_tokens (INTEGER)
- tool_used (BOOLEAN)
- tool_name (TEXT)
- timestamp (TIMESTAMP)
```

## Frontend (Vue.js 3)

### Components
1. **Dashboard View**
   - Analytics cards with metrics
   - Quick actions
   - Course details
   - Student progress (for teachers)

2. **Chat View**
   - Conversation sidebar
   - Message history
   - Input area
   - Analytics widget in chat
   - File upload widget (teachers/admin)

### Key Features
- Real-time analytics display
- Conversation management
- Quick action buttons
- File upload to Canvas
- Auto-title generation
- Loading states with timeouts

## API Endpoints Reference

### Authentication
- `POST /demo-login` - Login with username/password
- `POST /register-user` - Register new user

### Chat & Inference
- `POST /inference` - Send message to AI assistant
  - Request: `{ model, messages, user_role, canvas_user_id, conversation_id }`
  - Response: `{ content, analytics, tool_used, inference_system }`

### Analytics
- `GET /analytics?user_role={role}&canvas_user_id={id}` - Get analytics
  - Response: `{ analytics: { total_courses, recent_courses, quick_actions } }`

### Conversations
- `GET /conversations?canvas_user_id={id}` - List conversations
- `POST /conversations` - Create conversation
- `GET /conversations/{id}/messages` - Get messages
- `DELETE /conversations/{id}` - Delete conversation
- `PUT /conversations/{id}/title` - Update title

### Dashboard
- `GET /dashboard-widgets?user_role={role}&canvas_user_id={id}` - Get widgets
- `GET /usage-stats?canvas_user_id={id}&days={days}` - Usage statistics

## Configuration

### Required Environment Variables
```bash
CANVAS_URL=https://your-canvas.com/api/v1
CANVAS_TOKEN=your_canvas_token
OPENAI_API_KEY=your_openai_key
SECRET_KEY=jwt_secret_key
DEBUG=True
```

## Error Handling

### Canvas API Errors
- Validation through `CanvasAPIValidator`
- Graceful fallbacks
- User-friendly error messages

### OpenAI Errors
- Timeout handling (10s for analytics, 5s for conversations)
- Fallback responses
- Usage tracking even on errors

### Frontend Errors
- Loading states
- Timeout protection
- Default empty states

## Performance Optimizations

1. **Analytics Caching** - 5-minute cache reduces Canvas API calls
2. **Pagination** - Canvas API calls use pagination (100 items per page)
3. **Parallel Loading** - Frontend loads conversations and analytics in parallel
4. **Lazy Loading** - Analytics loaded on-demand
5. **Request Timeouts** - Prevents hanging requests

## Security Features

1. **Role-Based Access Control** - Tools filtered by user role
2. **Canvas Token Validation** - Validates Canvas API access
3. **JWT Authentication** - Secure session management
4. **Input Sanitization** - Validates user inputs
5. **as_user_id Masquerading** - Admin can act as specific users

## Deployment

### Local Development
```bash
python lms_chatot/main.py
```

### Production
```bash
uvicorn lms_chatot.main:app --host 0.0.0.0 --port 8001 --workers 4
```

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "lms_chatot.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

## Future Enhancements

1. **Redis Caching** - Replace in-memory cache with Redis
2. **PostgreSQL** - Replace SQLite for production
3. **WebSocket Support** - Real-time chat updates
4. **File Processing** - AI analysis of uploaded files
5. **Batch Operations** - Bulk course/user creation
6. **Advanced Analytics** - Student performance predictions
7. **Notification System** - Email/SMS notifications
8. **Mobile App** - React Native mobile client

## Troubleshooting

### Analytics Not Showing
- Check `/analytics` endpoint returns data
- Verify Canvas API token has proper permissions
- Check browser console for errors
- Clear analytics cache: `POST /clear-analytics-cache`

### Tool Execution Fails
- Verify user role has permission for tool
- Check Canvas API token permissions
- Review intent classification output
- Check Canvas API validator logs

### OpenAI Errors
- Verify OPENAI_API_KEY is set
- Check API quota/limits
- Review model availability
- Check request/response format

## Support

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: See README.md for setup instructions
- **Canvas API Docs**: https://canvas.instructure.com/doc/api/
- **OpenAI API Docs**: https://platform.openai.com/docs/
