# Canvas LMS AI Assistant with OpenAI

A streamlined AI-powered assistant for Canvas LMS integration using OpenAI and FastAPI.

## 🚀 Features

- **Canvas LMS Integration**: Full API integration with Canvas Learning Management System
- **OpenAI Integration**: GPT-4 for intelligent tool calling and conversations
- **Role-Based Access**: Support for Admin, Teacher, and Student roles
- **Real-time Analytics**: Performance monitoring and Canvas data insights
- **Smart Tool Detection**: AI-powered intent recognition and Canvas operations
- **Conversation Management**: Persistent chat history and sessions

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.8+
- **AI Model**: OpenAI GPT-4 (via Responses API)
- **LMS Integration**: Canvas API
- **Database**: SQLite for conversations and usage tracking
- **Frontend**: Vue.js 3 dashboard
- **Authentication**: JWT tokens

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- Canvas LMS instance with API access
- Valid Canvas API token

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/lms_chatbot.git
   cd lms_chatbot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Canvas URL, token, and OpenAI API key
   ```

4. **Run the application**
   ```bash
   cd lms_chatbot
   python main.py
   ```

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# Canvas LMS Configuration
CANVAS_URL=https://your-canvas-instance.com/api/v1
CANVAS_TOKEN=your_canvas_api_token

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Application Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
```

## 🎯 Usage

### Web Interface
- Navigate to `http://localhost:8001`
- Login with Canvas credentials or demo account
- Start chatting with the AI assistant

### API Endpoints

#### Core Endpoints
- `POST /inference` - Chat with AI assistant
- `GET /analytics` - Get Canvas analytics
- `GET /conversations` - Chat history
- `GET /health` - Health check

#### Authentication
- `POST /demo-login` - Login endpoint
- `POST /register-user` - User registration

#### Conversations
- `GET /conversations` - List user conversations
- `POST /conversations` - Create new conversation
- `GET /conversations/{id}/messages` - Get conversation messages
- `DELETE /conversations/{id}` - Delete conversation
- `PUT /conversations/{id}/title` - Update conversation title

#### Analytics & Widgets
- `GET /analytics?user_role={role}&canvas_user_id={id}` - Get analytics
- `GET /dashboard-widgets?user_role={role}&canvas_user_id={id}` - Get dashboard widgets
- `GET /usage-stats?canvas_user_id={id}&days={days}` - Usage statistics

### Supported Commands
- "List my courses" - Show enrolled courses
- "Create a new course" - Create course in Canvas
- "Show modules in course X" - Display course modules
- "Create assignment" - Add new assignment
- "Add student to course" - Enroll users (admin only)
- "Grade assignment" - Grade student work (teacher only)

## 📊 Architecture

```
lms_chatbot/
├── lms_chatot/
│   ├── main.py                    # FastAPI application
│   ├── canvas_agent.py            # Main agent orchestrator
│   ├── canvas_integration.py      # Canvas API wrapper
│   ├── canvas_tools.py            # Canvas tool executor
│   ├── canvas_tools_schemas.py    # Tool definitions
│   ├── intent_classifier.py       # Intent classification
│   ├── analytics_cache.py         # Analytics caching
│   ├── dashboard_widgets.py       # Dashboard data
│   ├── conversations_db.py        # Conversation storage
│   ├── usage_tracker.py           # Usage tracking
│   ├── auth.py                    # Authentication
│   ├── user_store.py              # User management
│   ├── session_manager.py         # Session handling
│   ├── inference_systems/
│   │   ├── base_inference.py      # Base inference class
│   │   └── openai_inference.py    # OpenAI integration
│   └── templates/
│       ├── canvas_login.html      # Login page
│       └── vue_dashboard.html     # Main dashboard
├── requirements.txt               # Dependencies
└── .env                          # Configuration
```

## 🔒 Security

- Canvas API token validation
- Role-based access control (RBAC)
- Secure session management
- JWT-based authentication
- Input validation and sanitization

## 🚀 Deployment

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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check OpenAI and Canvas API documentation
- **Issues**: Create an issue on GitHub
- **Analytics**: Check `/analytics` endpoint for metrics

## 🙏 Acknowledgments

- OpenAI GPT-4
- Canvas LMS API
- FastAPI framework
- Vue.js 3