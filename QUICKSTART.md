# Quick Start Guide

## Setup (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create `.env` file:
```bash
CANVAS_URL=https://your-canvas.com/api/v1
CANVAS_TOKEN=your_canvas_token
OPENAI_API_KEY=sk-your-openai-key
SECRET_KEY=any-random-string-for-jwt
DEBUG=True
```

### 3. Run Application
```bash
cd lms_chatbot
python main.py
```

### 4. Access Dashboard
Open browser: `http://localhost:8001`

## Demo Login

### Default Demo Users
- **Admin**: `admin` / `admin123`
- **Teacher**: `teacher` / `teacher123`
- **Student**: `student` / `student123`

## Testing the System

### 1. Test Analytics
```bash
curl "http://localhost:8001/analytics?user_role=student&canvas_user_id=1"
```

### 2. Test Chat
```bash
curl -X POST http://localhost:8001/inference \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "List my courses"}],
    "user_role": "student",
    "canvas_user_id": 1
  }'
```

### 3. Test Health
```bash
curl http://localhost:8001/health
```

## Common Commands

### Student Commands
- "List my courses"
- "Show my assignments"
- "What's my progress?"
- "Help me prioritize my work"

### Teacher Commands
- "Create a new course called 'Python 101'"
- "Create an assignment in course 123"
- "Show me course statistics"
- "List students in my course"

### Admin Commands
- "List all courses"
- "Create a new user"
- "Enroll user 456 in course 123"
- "Show system overview"

## Troubleshooting

### Port Already in Use
```bash
# Change port in main.py or use:
uvicorn lms_chatot.main:app --port 8002
```

### Canvas API Not Working
1. Verify Canvas URL format: `https://your-canvas.com/api/v1`
2. Check token has proper permissions
3. Test token: `curl -H "Authorization: Bearer YOUR_TOKEN" https://your-canvas.com/api/v1/courses`

### OpenAI API Errors
1. Verify API key is valid
2. Check quota: https://platform.openai.com/usage
3. Ensure model access (gpt-4o-mini)

### Database Errors
```bash
# Reset databases
rm lms_chatot/conversations.db
rm lms_chatot/usage_tracker.db
# Restart application to recreate
```

## Development Tips

### Enable Debug Logging
```python
# Add to main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Without Canvas
Set empty Canvas credentials in `.env`:
```bash
CANVAS_URL=
CANVAS_TOKEN=
```
System will work in demo mode.

### Clear Analytics Cache
```bash
curl -X POST http://localhost:8001/clear-analytics-cache
```

## Next Steps

1. **Customize Tools**: Edit `canvas_tools_schemas.py`
2. **Add Intents**: Modify `intent_classifier.py`
3. **Extend Canvas API**: Add methods to `canvas_integration.py`
4. **Customize UI**: Edit `templates/vue_dashboard.html`
5. **Add Analytics**: Extend `analytics_cache.py`

## Production Checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure HTTPS/SSL
- [ ] Set up reverse proxy (nginx)
- [ ] Use production database (PostgreSQL)
- [ ] Enable rate limiting
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Review security settings
- [ ] Load test the application

## Resources

- **Canvas API**: https://canvas.instructure.com/doc/api/
- **OpenAI API**: https://platform.openai.com/docs/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Vue.js 3**: https://vuejs.org/

## Support

For issues or questions:
1. Check `PROJECT_SUMMARY.md` for architecture details
2. Review logs in console output
3. Test individual components
4. Create GitHub issue with details
