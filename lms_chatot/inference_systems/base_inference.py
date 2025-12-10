from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseInference(ABC):
    """Base class for all inference systems"""
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this inference system is configured and available"""
        pass
    
    @abstractmethod
    def call_with_tools(self, system_prompt: str, messages: List[Dict], tools: List[Dict]) -> Dict[str, Any]:
        """Call the inference system with tool support"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get status information about this inference system"""
        return {
            "name": self.name,
            "available": self.is_available()
        }