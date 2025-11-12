"""Mistral API client with LangChain integration."""
from typing import Dict, Any, Optional
import json
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage, SystemMessage
from src.utils.config import Config


class MistralClient:
    """Wrapper for Mistral API with LangChain."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize Mistral client.
        
        Args:
            api_key: Mistral API key (defaults to Config.MISTRAL_API_KEY)
            model: Model name (defaults to Config.MISTRAL_MODEL)
        """
        self.api_key = api_key or Config.MISTRAL_API_KEY
        self.model = model or Config.MISTRAL_MODEL
        
        self.llm = ChatMistralAI(
            api_key=self.api_key,
            model=self.model,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS
        )
    
    def generate(self, prompt: str, system_message: Optional[str] = None) -> str:
        """Generate text using Mistral.
        
        Args:
            prompt: The user prompt
            system_message: Optional system message
            
        Returns:
            Generated text
        """
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))
        
        response = self.llm.invoke(messages)
        return response.content
    
    def generate_structured(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        retry_on_error: bool = True
    ) -> Dict[str, Any]:
        """Generate structured JSON output.
        
        Args:
            prompt: The user prompt
            system_message: Optional system message
            retry_on_error: Whether to retry once if JSON parsing fails
            
        Returns:
            Parsed JSON as dictionary
        """
        response_text = self.generate(prompt, system_message)
        
        try:
            # Try to parse the entire response as JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                return json.loads(json_str)
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                return json.loads(json_str)
            
            # If retry is enabled and we haven't tried yet, try once more
            if retry_on_error:
                enhanced_prompt = f"{prompt}\n\nIMPORTANT: Return ONLY valid JSON, no markdown formatting or additional text."
                return self.generate_structured(enhanced_prompt, system_message, retry_on_error=False)
            
            raise ValueError(f"Could not parse JSON from response: {response_text}")
    
    def generate_with_template(self, template, **kwargs) -> str:
        """Generate using a LangChain template.
        
        Args:
            template: LangChain PromptTemplate or ChatPromptTemplate
            **kwargs: Template variables
            
        Returns:
            Generated text
        """
        chain = template | self.llm
        response = chain.invoke(kwargs)
        
        # Handle different response types
        if hasattr(response, 'content'):
            return response.content
        return str(response)

