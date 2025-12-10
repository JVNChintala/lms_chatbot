# Canvas LMS AI Assistant with AWS Bedrock

A powerful AI-powered assistant for Canvas LMS integration using AWS Bedrock and Claude 3 Sonnet.

## 🚀 Features

- **Canvas LMS Integration**: Full API integration with Canvas Learning Management System
- **AWS Bedrock AI**: Claude 3 Sonnet for intelligent tool calling and conversations
- **Role-Based Access**: Support for Admin, Teacher, and Student roles
- **Real-time Analytics**: Performance monitoring and Canvas data insights
- **Smart Tool Detection**: AI-powered intent recognition and Canvas operations
- **Conversation Management**: Persistent chat history and sessions

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.8+
- **AI Model**: Claude 3 Sonnet via AWS Bedrock
- **LMS Integration**: Canvas API
- **Database**: SQLite for conversations
- **Frontend**: Vue.js dashboard
- **Authentication**: JWT tokens

## 📋 Prerequisites

- Python 3.8+
- AWS Account with Bedrock access
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
   # Edit .env with your Canvas URL, token, and AWS credentials
   ```

4. **Run the application**
   ```bash
   cd lms_chatot
   python main.py
   ```

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# Canvas LMS Configuration
CANVAS_URL=https://your-canvas-instance.com/api/v1
CANVAS_TOKEN=your_canvas_api_token

# AWS Bedrock Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Application Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### AWS Bedrock Setup

1. **Enable Claude 3 Sonnet** in AWS Bedrock console
2. **Configure IAM permissions** for Bedrock access
3. **Set AWS credentials** in environment variables

## 🎯 Usage

### Web Interface
- Navigate to `http://localhost:8001`
- Login with Canvas credentials or demo account
- Start chatting with the AI assistant

### API Endpoints
- `POST /inference` - Chat with AI assistant
- `GET /performance` - Performance metrics
- `GET /analytics` - Canvas analytics
- `GET /conversations` - Chat history

### Supported Commands
- "List my courses" - Show enrolled courses
- "Create a new course" - Create course in Canvas
- "Show modules in course X" - Display course modules
- "Create assignment" - Add new assignment
- "Add student to course" - Enroll users (admin only)

## 📊 Performance Features

### AWS Bedrock Advantages
- **High Accuracy**: Claude 3 Sonnet for precise tool calling
- **Fast Response**: Optimized for educational workflows
- **Scalable**: AWS infrastructure handles load
- **Secure**: Enterprise-grade security and compliance

### Monitoring
Access real-time performance metrics at `/performance`:
- Response times and accuracy
- Tool usage statistics
- Canvas API performance
- System health insights

## 🔒 Security

- AWS IAM-based authentication
- Role-based access control
- Canvas API token validation
- Secure session management

## 🏗️ Architecture

```
├── lms_chatot/
│   ├── main.py              # FastAPI application
│   ├── canvas_agent.py      # AWS Bedrock agent with Claude
│   ├── canvas_integration.py # Canvas API wrapper
│   ├── auth.py              # Authentication
│   └── templates/           # Web interface
├── requirements.txt         # Dependencies
└── .env                     # Configuration
```

## 🚀 Deployment

### Local Development
```bash
python lms_chatot/main.py
```

### Production
```bash
uvicorn lms_chatot.main:app --host 0.0.0.0 --port 8001
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

- **Documentation**: Check AWS Bedrock documentation
- **Issues**: Create an issue on GitHub
- **Performance**: Check `/performance` endpoint for metrics

## 🙏 Acknowledgments

- AWS Bedrock and Claude 3 Sonnet
- Canvas LMS API
- FastAPI framework