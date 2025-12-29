# Hugging Face Open Source Models Integration

## 🚀 Overview

The Canvas LMS AI Assistant now uses **completely free** open-source models from Hugging Face that run locally without requiring any API keys or paid services.

## 🆓 Free Models Available

### Recommended Models (No API Keys Required)

1. **microsoft/DialoGPT-medium** (Default)
   - Size: ~350MB
   - Good conversational abilities
   - Fast inference on CPU

2. **microsoft/DialoGPT-large**
   - Size: ~1.4GB
   - Better quality responses
   - Requires more RAM

3. **facebook/blenderbot-400M-distill**
   - Size: ~400MB
   - Optimized for conversations
   - Good performance

4. **google/flan-t5-base**
   - Size: ~250MB
   - Instruction-following model
   - Excellent for tasks

5. **distilgpt2** (Fallback)
   - Size: ~80MB
   - Very fast
   - Basic capabilities

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Hugging Face Configuration (Free Open Source Models)
HF_MODEL=microsoft/DialoGPT-medium    # Model to use
HF_DEVICE=cpu                         # cpu or cuda
HF_MAX_LENGTH=512                     # Response length
HF_TEMPERATURE=0.7                    # Creativity (0.1-1.0)
HF_DO_SAMPLE=true                     # Enable sampling

# Tool Calling Configuration
TOOL_CALLING_ENABLED=true
MAX_TOOL_ITERATIONS=3
```

### Model Selection Guide

**For CPU-only systems:**
```bash
HF_MODEL=microsoft/DialoGPT-medium
HF_DEVICE=cpu
```

**For systems with GPU:**
```bash
HF_MODEL=microsoft/DialoGPT-large
HF_DEVICE=cuda
```

**For low-memory systems:**
```bash
HF_MODEL=distilgpt2
HF_DEVICE=cpu
```

## 🛠️ Features

### Automatic Model Loading
- Downloads models automatically on first use
- Caches models locally for future use
- Automatic fallback to smaller models if loading fails

### Tool Detection
- Pattern-based tool detection (no AI required)
- Supports all Canvas LMS operations
- Fast and reliable

### Available Commands
- **"list courses"** - Show user's courses
- **"create course [name]"** - Create new course
- **"list modules"** - Show course modules
- **"create module [name]"** - Add new module
- **"create assignment [name]"** - Create assignment
- **"list users"** - Show users (admin only)

### Role-Based Access
- **Admin**: Full access to all tools
- **Teacher**: Course and content management
- **Student**: Read-only access

## 📊 Performance

### Expected Performance
- **Model Loading**: 30-60 seconds first time
- **Response Time**: 2-5 seconds on CPU
- **Memory Usage**: 500MB - 2GB depending on model
- **Storage**: 250MB - 1.4GB per model

### Optimization Tips
1. **Use GPU if available**: Set `HF_DEVICE=cuda`
2. **Choose appropriate model size**: Balance quality vs speed
3. **Adjust temperature**: Lower for consistent responses
4. **Set reasonable max_length**: Avoid very long responses

## 🔒 Privacy & Security

### Complete Privacy
- **No API calls**: Everything runs locally
- **No data sharing**: Your conversations stay on your machine
- **No internet required**: After initial model download
- **No usage tracking**: Completely private

### Benefits
- **Zero cost**: No API fees ever
- **Offline capable**: Works without internet
- **Data privacy**: Complete control over your data
- **No rate limits**: Use as much as you want

## 🚀 Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Model
```bash
# Edit .env file
HF_MODEL=microsoft/DialoGPT-medium
HF_DEVICE=cpu
```

### 3. First Run
```bash
python lms_chatot/main.py
```

The model will download automatically (may take a few minutes).

### 4. GPU Setup (Optional)
If you have NVIDIA GPU:
```bash
# Install CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Update .env
HF_DEVICE=cuda
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
    "status": "Hugging Face integration active",
    "model": "microsoft/DialoGPT-medium",
    "device": "cpu",
    "temperature": "0.7",
    "max_length": "512"
  }
}
```

## 🛠️ Troubleshooting

### Common Issues

1. **Model Download Fails**
   - Check internet connection
   - Try smaller model (distilgpt2)
   - Clear cache: `rm -rf ~/.cache/huggingface/`

2. **Out of Memory**
   - Use smaller model
   - Reduce max_length
   - Use CPU instead of GPU

3. **Slow Performance**
   - Enable GPU if available
   - Use smaller model
   - Reduce temperature

4. **Poor Responses**
   - Try larger model
   - Adjust temperature
   - Use instruction-tuned model (flan-t5)

### Model Recommendations by System

**Low-end systems (4GB RAM):**
```bash
HF_MODEL=distilgpt2
HF_DEVICE=cpu
HF_MAX_LENGTH=256
```

**Mid-range systems (8GB RAM):**
```bash
HF_MODEL=microsoft/DialoGPT-medium
HF_DEVICE=cpu
HF_MAX_LENGTH=512
```

**High-end systems (16GB+ RAM):**
```bash
HF_MODEL=microsoft/DialoGPT-large
HF_DEVICE=cpu
HF_MAX_LENGTH=512
```

**Systems with GPU:**
```bash
HF_MODEL=microsoft/DialoGPT-large
HF_DEVICE=cuda
HF_MAX_LENGTH=512
```

## 🎉 Benefits

### Cost Savings
- **$0 monthly costs**: No API fees
- **One-time setup**: Download once, use forever
- **No usage limits**: Unlimited conversations
- **No subscription**: Completely free

### Technical Benefits
- **Local processing**: No network dependency
- **Fast responses**: No API latency
- **Customizable**: Full control over model behavior
- **Scalable**: Add more models as needed

### Privacy Benefits
- **Complete privacy**: Data never leaves your system
- **GDPR compliant**: No external data processing
- **Secure**: No API keys to manage
- **Audit-friendly**: Full transparency

The Hugging Face integration provides a completely free, private, and powerful alternative to paid AI services while maintaining all Canvas LMS functionality.