#!/usr/bin/env python3
"""
Ollama Qwen2.5 7B Optimization Script
Configures Ollama server for optimal tool calling performance
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def optimize_ollama_model():
    """Configure Ollama server with optimized Qwen2.5 parameters"""
    
    ollama_url = os.getenv('OLLAMA_URL', 'http://10.21.34.238:11434')
    ollama_model = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')
    
    print(f"🚀 Optimizing Ollama server at {ollama_url}")
    print(f"📦 Model: {ollama_model}")
    
    # Check if model exists
    try:
        response = requests.get(f"{ollama_url}/api/tags")
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            
            if ollama_model not in model_names:
                print(f"❌ Model {ollama_model} not found on server")
                print(f"📋 Available models: {', '.join(model_names)}")
                return False
            else:
                print(f"✅ Model {ollama_model} found on server")
        else:
            print(f"❌ Cannot connect to Ollama server: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        return False
    
    # Test optimized parameters
    test_prompts = [
        {
            "name": "Tool Detection Test",
            "prompt": "Analyze this request: 'list my courses'. Respond with TOOL:list_courses or NO_TOOL",
            "expected": "TOOL:list_courses",
            "params": {
                "temperature": 0.05,
                "top_p": 0.8,
                "num_predict": 50,
                "repeat_penalty": 1.1,
                "stop": ["\n", "Examples:", "User:"]
            }
        },
        {
            "name": "General Response Test", 
            "prompt": "You are a Canvas LMS assistant. Respond to: 'Hello, how can you help me?'",
            "expected": "canvas",  # Should mention Canvas
            "params": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 100,
                "repeat_penalty": 1.05
            }
        }
    ]
    
    print("\n🧪 Testing optimized parameters...")
    
    for test in test_prompts:
        print(f"\n📝 {test['name']}")
        print(f"   Prompt: {test['prompt'][:50]}...")
        
        try:
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": test['prompt'],
                    "stream": False,
                    "options": test['params']
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()
                
                # Check if response contains expected content
                if test['expected'].lower() in response_text.lower():
                    print(f"   ✅ Response: {response_text[:100]}...")
                else:
                    print(f"   ⚠️  Response: {response_text[:100]}...")
                    print(f"   Expected to contain: {test['expected']}")
                
                # Performance metrics
                eval_count = result.get('eval_count', 0)
                eval_duration = result.get('eval_duration', 0)
                if eval_count > 0 and eval_duration > 0:
                    tokens_per_sec = eval_count / (eval_duration / 1e9)
                    print(f"   📊 Performance: {tokens_per_sec:.1f} tokens/sec")
                
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
    
    # Create optimized Modelfile
    print(f"\n📄 Creating optimized Modelfile for {ollama_model}...")
    
    modelfile_content = f"""FROM {ollama_model}

# Qwen2.5 7B Tool Calling Optimization
PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.05
PARAMETER num_ctx 8192
PARAMETER num_predict 512
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"
PARAMETER stop "\\n\\nUser:"
PARAMETER stop "\\n\\nHuman:"

# System message for Canvas LMS
SYSTEM \"\"\"You are a Canvas LMS assistant powered by Qwen2.5. You excel at understanding user intent and using tools effectively.

TOOL CALLING RULES:
1. Always analyze user intent first
2. Use tools when specific Canvas operations are requested  
3. Provide natural, conversational responses
4. Never invent or assume data - always use real API results

RESPONSE FORMAT:
- Be concise but helpful
- Use bullet points for lists
- Include relevant IDs and details from API responses
- Ask clarifying questions when needed\"\"\"
"""
    
    # Save Modelfile
    with open('Modelfile.qwen-optimized', 'w') as f:
        f.write(modelfile_content)
    
    print("✅ Modelfile created: Modelfile.qwen-optimized")
    print("\n🔧 To apply optimizations, run:")
    print(f"   ollama create {ollama_model}-optimized -f Modelfile.qwen-optimized")
    print(f"   Then update OLLAMA_MODEL={ollama_model}-optimized in .env")
    
    return True

def benchmark_performance():
    """Benchmark current vs optimized performance"""
    
    ollama_url = os.getenv('OLLAMA_URL', 'http://10.21.34.238:11434')
    ollama_model = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')
    
    print(f"\n⚡ Benchmarking {ollama_model} performance...")
    
    benchmark_prompts = [
        "List all my courses in Canvas LMS",
        "Create a new course called 'Introduction to AI'", 
        "Show me the modules in course 123",
        "Hello, what can you help me with?",
        "How do I create an assignment?"
    ]
    
    # Test with default parameters
    print("\n📊 Testing with default parameters...")
    default_params = {"temperature": 0.7, "num_predict": 200}
    default_times = []
    
    for prompt in benchmark_prompts:
        try:
            import time
            start = time.time()
            
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": default_params
                },
                timeout=60
            )
            
            end = time.time()
            response_time = (end - start) * 1000
            default_times.append(response_time)
            
            if response.status_code == 200:
                print(f"   ✅ {response_time:.0f}ms - {prompt[:30]}...")
            else:
                print(f"   ❌ Error - {prompt[:30]}...")
                
        except Exception as e:
            print(f"   ❌ Failed - {prompt[:30]}... ({e})")
    
    # Test with optimized parameters  
    print("\n🚀 Testing with optimized parameters...")
    optimized_params = {
        "temperature": 0.1,
        "top_p": 0.9,
        "top_k": 40,
        "repeat_penalty": 1.05,
        "num_predict": 200
    }
    optimized_times = []
    
    for prompt in benchmark_prompts:
        try:
            import time
            start = time.time()
            
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": optimized_params
                },
                timeout=60
            )
            
            end = time.time()
            response_time = (end - start) * 1000
            optimized_times.append(response_time)
            
            if response.status_code == 200:
                print(f"   ✅ {response_time:.0f}ms - {prompt[:30]}...")
            else:
                print(f"   ❌ Error - {prompt[:30]}...")
                
        except Exception as e:
            print(f"   ❌ Failed - {prompt[:30]}... ({e})")
    
    # Compare results
    if default_times and optimized_times:
        avg_default = sum(default_times) / len(default_times)
        avg_optimized = sum(optimized_times) / len(optimized_times)
        improvement = ((avg_default - avg_optimized) / avg_default) * 100
        
        print(f"\n📈 Performance Comparison:")
        print(f"   Default avg:    {avg_default:.0f}ms")
        print(f"   Optimized avg:  {avg_optimized:.0f}ms")
        print(f"   Improvement:    {improvement:+.1f}%")
        
        if improvement > 0:
            print("   🎉 Optimization successful!")
        else:
            print("   ⚠️  Consider adjusting parameters")

if __name__ == "__main__":
    print("🔧 Qwen2.5 7B Ollama Optimization Tool")
    print("=" * 50)
    
    if optimize_ollama_model():
        benchmark_performance()
    
    print("\n✨ Optimization complete!")
    print("\n💡 Next steps:")
    print("   1. Apply the optimized Modelfile")
    print("   2. Update your .env file")
    print("   3. Restart your application")
    print("   4. Monitor /performance endpoint")