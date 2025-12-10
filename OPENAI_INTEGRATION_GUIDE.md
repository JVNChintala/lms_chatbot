# OpenAI API Integration Guide

## 🚀 Overview

The Canvas LMS AI Assistant now uses OpenAI's API with native function calling capabilities for enhanced tool execution and natural language processing.

## 🔧 Configuration

### Environment Variables (.env)
```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o                    # Recommended: gpt-4o, gpt-4-turbo, gpt-3.5-turbo
OPENAI_TEMPERATURE=0.1                 # Low for consistent tool calling
OPENAI_MAX_TOKENS=1000                 # Response length limit
OPENAI_TIMEOUT=60                      # Request timeout in seconds

# Tool Calling Configuration
TOOL_CALLING_ENABLED=true
MAX_TOOL_ITERATIONS=3
```

## 🛠️ Supported Models

### Recommended Models
- **gpt-4o** - Latest and most capable model with excellent function calling
- **gpt-4-turbo** - Fast and reliable for complex tasks
- **gpt-3.5-turbo** - Cost-effective option with good performance

### Model Capabilities
- Native function calling support
- JSON mode for structured responses
- Large context windows (up to 128k tokens)
- Excellent instruction following

## 🎯 Features

### Function Calling
- **Native Support**: OpenAI's built-in function calling
- **Automatic Tool Selection**: AI decides when to use tools
- **Multi-step Operations**: Chain multiple function calls
- **Error Handling**: Robust error recovery

### Available Tools
- `list_courses` - Show user's courses
- `create_course` - Create new courses
- `list_modules` - Display course modules
- `create_module` - Add new modules
- `create_assignment` - Create assignments
- `create_user` - Add new users (admin only)
- `list_users` - Show all users (admin only)
- `enroll_user` - Enroll users in courses (admin only)

### Role-Based Access
- **Admin**: Full access to all tools
- **Teacher**: Course and content management
- **Student**: Read-only access to enrolled content

## 📊 Performance Benefits

### Advantages over Previous System
- **Faster Response Times**: Direct API calls, no local model overhead
- **Better Accuracy**: Advanced language understanding
- **Reliable Function Calls**: Native OpenAI function calling
- **Scalability**: Cloud-based processing
- **Consistency**: Deterministic responses with low temperature

### Expected Performance
- **Response Time**: 1-3 seconds typical
- **Function Call Accuracy**: 95%+ success rate
- **Context Handling**: Up to 128k tokens
- **Concurrent Users**: Scales with OpenAI API limits

## 🔒 Security

### API Key Management
- Store API key securely in environment variables
- Never commit API keys to version control
- Use separate keys for development/production
- Monitor API usage and costs

### Best Practices
- Set reasonable token limits
- Implement request timeouts
- Log function calls for debugging
- Monitor API usage costs

## 💰 Cost Optimization

### Token Usage
- **Input Tokens**: System prompt + conversation history
- **Output Tokens**: AI responses
- **Function Calls**: Additional tokens for tool definitions

### Cost-Saving Tips
- Use `gpt-3.5-turbo` for simpler tasks
- Optimize system prompts for brevity
- Set appropriate `max_tokens` limits
- Clear conversation history when not needed

### Estimated Costs (per 1000 requests)
- **gpt-4o**: ~$15-30 depending on conversation length
- **gpt-4-turbo**: ~$10-20 depending on conversation length
- **gpt-3.5-turbo**: ~$2-5 depending on conversation length

## 🚀 Setup Instructions

### 1. Get OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com)
2. Create account or sign in
3. Go to API Keys section
4. Create new API key
5. Copy the key securely

### 2. Update Configuration
```bash
# Update .env file
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4o
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Test the Integration
```bash
python lms_chatot/main.py
```

## 🔍 Monitoring

### Performance Endpoint
```bash
GET /performance
```

Returns:
```json
{
  "performance": {
    "status": "OpenAI API integration active",
    "model": "gpt-4o",
    "temperature": "0.1",
    "max_tokens": "1000"
  }
}
```

### Logging
- Function calls are logged with arguments and results
- Errors are captured with full stack traces
- API response times can be monitored

## 🛠️ Troubleshooting

### Common Issues

1. **API Key Errors**
   - Verify API key is correct
   - Check API key has sufficient credits
   - Ensure key has proper permissions

2. **Rate Limiting**
   - Implement exponential backoff
   - Monitor API usage limits
   - Consider upgrading API tier

3. **Function Call Failures**
   - Check function definitions are correct
   - Verify Canvas API connectivity
   - Review function arguments

### Error Handling
- Automatic retry for transient failures
- Graceful degradation when tools fail
- Clear error messages for users

## 🎉 Migration Benefits

### From Previous System
- **Simplified Architecture**: No local model management
- **Better Reliability**: Cloud-based processing
- **Enhanced Capabilities**: Advanced language understanding
- **Easier Maintenance**: No model updates or optimization needed
- **Cost Predictability**: Pay-per-use pricing model

### Immediate Improvements
- Faster response times
- More accurate tool selection
- Better conversation flow
- Reduced infrastructure requirements
- Simplified deployment

The OpenAI integration provides a robust, scalable foundation for the Canvas LMS AI Assistant with enterprise-grade reliability and performance.