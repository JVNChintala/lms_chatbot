import os
import requests
import json
from typing import Dict, List, Any
from .base_video_generator import BaseVideoGenerator

class StableVideoGenerator(BaseVideoGenerator):
    """Stable Video Diffusion generator (Open Source)"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('STABILITY_API_KEY')
        self.base_url = "https://api.stability.ai/v2beta"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def generate_video_quiz(self, topic: str, duration: int = 300, difficulty: str = "medium") -> Dict[str, Any]:
        """Generate video quiz using Stable Video Diffusion"""
        try:
            # Generate quiz content
            quiz_content = self._generate_quiz_content(topic, difficulty)
            
            # Create educational video with quiz overlay
            video_result = self._create_stable_video(
                prompt=f"Educational quiz presentation about {topic}, clean background, professional style",
                duration=min(duration, 120)  # Stable Video has shorter limits
            )
            
            return {
                "success": True,
                "video_url": video_result.get("video_url"),
                "video_id": video_result.get("id"),
                "quiz_questions": quiz_content["questions"],
                "topic": topic,
                "duration": duration,
                "generator": "Stable Video"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "generator": "Stable Video"
            }
    
    def generate_educational_video(self, topic: str, duration: int = 300, style: str = "lecture") -> Dict[str, Any]:
        """Generate educational video using Stable Video Diffusion"""
        try:
            prompt = self._create_video_prompt(topic, style)
            
            video_result = self._create_stable_video(
                prompt=prompt,
                duration=min(duration, 120)
            )
            
            return {
                "success": True,
                "video_url": video_result.get("video_url"),
                "video_id": video_result.get("id"),
                "topic": topic,
                "duration": duration,
                "style": style,
                "generator": "Stable Video"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "generator": "Stable Video"
            }
    
    def _generate_quiz_content(self, topic: str, difficulty: str) -> Dict[str, Any]:
        """Generate quiz questions for video"""
        questions = [
            {
                "question": f"What is the fundamental concept behind {topic}?",
                "options": ["Concept A", "Concept B", "Concept C", "Concept D"],
                "correct_answer": "Concept A",
                "explanation": f"The fundamental concept of {topic} is..."
            },
            {
                "question": f"How is {topic} implemented in practice?",
                "options": ["Method A", "Method B", "Method C", "Method D"],
                "correct_answer": "Method B",
                "explanation": f"{topic} is typically implemented using..."
            }
        ]
        
        return {
            "topic": topic,
            "difficulty": difficulty,
            "questions": questions,
            "total_questions": len(questions)
        }
    
    def _create_video_prompt(self, topic: str, style: str) -> str:
        """Create optimized prompt for Stable Video Diffusion"""
        style_prompts = {
            "lecture": f"Professional educational presentation about {topic}, clean whiteboard, academic setting",
            "tutorial": f"Step-by-step tutorial demonstration of {topic}, hands-on approach, clear visuals",
            "animated": f"Animated explanation of {topic}, colorful graphics, engaging visual elements",
            "documentary": f"Documentary style video about {topic}, real-world examples, professional narration"
        }
        
        return style_prompts.get(style, f"Educational content about {topic}, professional presentation")
    
    def _create_stable_video(self, prompt: str, duration: int) -> Dict[str, Any]:
        """Create video using Stable Video Diffusion API"""
        if not self.is_available():
            raise Exception("Stability AI API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "duration": min(duration, 120),  # Max 2 minutes for Stable Video
            "aspect_ratio": "16:9",
            "motion_bucket_id": 127
        }
        
        # Simulated response - replace with actual API call
        return {
            "id": "stable_video_789",
            "status": "processing",
            "video_url": f"https://stability.ai/videos/stable_video_789.mp4"
        }
    
    def get_max_duration(self) -> int:
        """Stable Video max duration"""
        return 120  # 2 minutes
    
    def get_supported_formats(self) -> List[str]:
        """Supported formats for Stable Video"""
        return ["mp4", "gif"]