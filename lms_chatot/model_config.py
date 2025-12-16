import os
from dotenv import load_dotenv
load_dotenv()

class ModelConfig:
    """Centralized model configuration"""
    
    # OpenAI Models
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    # Google Gemini Models
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    
    # AWS Bedrock Models
    BEDROCK_MODEL = os.getenv('BEDROCK_MODEL', 'anthropic.claude-3-sonnet-20240229-v1:0')
    
    # Model Parameters
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', '1000'))
    TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))
    
    @classmethod
    def get_model_name(cls, provider: str) -> str:
        """Get model name for specific provider"""
        models = {
            'openai': cls.OPENAI_MODEL,
            'gemini': cls.GEMINI_MODEL,
            'bedrock': cls.BEDROCK_MODEL
        }
        return models.get(provider.lower(), '')
    
    @classmethod
    def get_all_models(cls) -> dict:
        """Get all configured models"""
        return {
            'openai': cls.OPENAI_MODEL,
            'gemini': cls.GEMINI_MODEL,
            'bedrock': cls.BEDROCK_MODEL
        }