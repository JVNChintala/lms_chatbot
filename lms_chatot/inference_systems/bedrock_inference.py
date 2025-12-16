import os
import json
import boto3
from dotenv import load_dotenv
from .base_inference import BaseInference
from model_config import ModelConfig

load_dotenv()

class BedrockInference(BaseInference):
    """AWS Bedrock Claude 3 Sonnet inference system"""
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.model_id = ModelConfig.BEDROCK_MODEL
        if self.is_available():
            self.client = boto3.client(
                'bedrock-runtime',
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
    
    def is_available(self) -> bool:
        return bool(os.getenv('AWS_ACCESS_KEY_ID'))
    
    def call_with_tools(self, system_prompt: str, messages: list, tools: list) -> dict:
        """Call AWS Bedrock with Claude"""
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": ModelConfig.MAX_TOKENS,
            "system": system_prompt,
            "messages": messages,
            "tools": tools
        }
        
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(request_body)
        )
        
        result = json.loads(response['body'].read())
        
        # Handle tool calls
        if result.get('content') and result['content'][0].get('type') == 'tool_use':
            tool_use = result['content'][0]
            return {
                "needs_tool": True,
                "tool_name": tool_use['name'],
                "tool_args": tool_use['input'],
                "tool_use_id": tool_use['id'],
                "assistant_content": result['content']
            }
        
        # No tool use
        return {
            "needs_tool": False,
            "content": result['content'][0]['text']
        }
    
    def get_final_response(self, messages: list, tool_result: dict, tool_use_id: str) -> str:
        """Get final response after tool execution"""
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": json.dumps(tool_result)
            }]
        })
        
        final_request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": ModelConfig.MAX_TOKENS,
            "messages": messages
        }
        
        final_response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(final_request)
        )
        
        final_result = json.loads(final_response['body'].read())
        return final_result['content'][0]['text']