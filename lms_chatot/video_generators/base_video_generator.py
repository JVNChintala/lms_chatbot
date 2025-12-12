from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class BaseVideoGenerator(ABC):
    """Base class for all AI video generators"""
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this video generator is configured and available"""
        pass
    
    @abstractmethod
    def generate_video_quiz(self, topic: str, duration: int = 300, difficulty: str = "medium") -> Dict[str, Any]:
        """Generate video quiz content"""
        pass
    
    @abstractmethod
    def generate_educational_video(self, topic: str, duration: int = 300, style: str = "lecture") -> Dict[str, Any]:
        """Generate educational video content"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get status information about this video generator"""
        return {
            "name": self.name,
            "available": self.is_available(),
            "supported_formats": self.get_supported_formats(),
            "max_duration": self.get_max_duration()
        }
    
    def get_supported_formats(self) -> List[str]:
        """Get supported video formats"""
        return ["mp4", "webm"]
    
    def get_max_duration(self) -> int:
        """Get maximum video duration in seconds"""
        return 600  # 10 minutes default