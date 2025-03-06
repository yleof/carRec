# app/llm_service.py
import requests
import json
import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """Abstract base class for LLM API providers."""
    
    @abstractmethod
    def generate_completion(self, prompt: str) -> str:
        """
        Generate a completion using the LLM.
        
        Args:
            prompt: The input prompt for the LLM
            
        Returns:
            The LLM's response text
        """
        pass


class DeepSeekProvider(LLMProvider):
    """DeepSeek LLM API provider implementation."""
    
    def __init__(self, api_key: str, model: str = "deepseek-ai/DeepSeek-V3"):
        """
        Initialize DeepSeek provider.
        
        Args:
            api_key: DeepSeek API key
            model: Model identifier to use
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.siliconflow.cn/v1/chat/completions"
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def generate_completion(self, prompt: str) -> str:
        """
        Generate a completion using DeepSeek API.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Model's text response
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "stream": False,
            "max_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "frequency_penalty": 0.5,
            "n": 1,
            "messages": [
                {
                    "content": prompt,
                    "role": "user"
                }
            ]
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            
            response_data = response.json()
            if 'choices' in response_data and len(response_data['choices']) > 0:
                return response_data['choices'][0]['message']['content']
            else:
                self.logger.error(f"Unexpected API response structure: {response_data}")
                return ""
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request error: {str(e)}")
            return ""
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing API response: {str(e)}")
            return ""


class OpenAIProvider(LLMProvider):
    """OpenAI API provider implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model identifier to use
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def generate_completion(self, prompt: str) -> str:
        """
        Generate a completion using OpenAI API.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Model's text response
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            
            response_data = response.json()
            if 'choices' in response_data and len(response_data['choices']) > 0:
                return response_data['choices'][0]['message']['content']
            else:
                self.logger.error(f"Unexpected API response structure: {response_data}")
                return ""
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request error: {str(e)}")
            return ""
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing API response: {str(e)}")
            return ""


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider implementation."""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        """
        Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key
            model: Model identifier to use
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def generate_completion(self, prompt: str) -> str:
        """
        Generate a completion using Anthropic API.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Model's text response
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 500
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            
            response_data = response.json()
            if 'content' in response_data and len(response_data['content']) > 0:
                return response_data['content'][0]['text']
            else:
                self.logger.error(f"Unexpected API response structure: {response_data}")
                return ""
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request error: {str(e)}")
            return ""
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing API response: {str(e)}")
            return ""


class LLMService:
    """Service for managing LLM provider interactions."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM service with configuration.
        
        Args:
            config: Configuration dictionary with provider details
        """
        self.config = config
        self.provider = self._initialize_provider()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _initialize_provider(self) -> Optional[LLMProvider]:
        """Initialize the appropriate LLM provider based on configuration."""
        provider_type = self.config.get('provider', 'deepseek').lower()
        api_key = self.config.get('api_key', '')
        
        if not api_key:
            self.logger.error("No API key provided for LLM provider")
            return None
        
        if provider_type == 'deepseek':
            return DeepSeekProvider(
                api_key=api_key,
                model=self.config.get('model', 'deepseek-ai/DeepSeek-V3')
            )
        elif provider_type == 'openai':
            return OpenAIProvider(
                api_key=api_key,
                model=self.config.get('model', 'gpt-4')
            )
        elif provider_type == 'anthropic':
            return AnthropicProvider(
                api_key=api_key,
                model=self.config.get('model', 'claude-3-opus-20240229')
            )
        else:
            self.logger.error(f"Unsupported LLM provider: {provider_type}")
            return None
    
    def analyze_car(self, car_data: Dict[str, Any], preferences: Optional[Dict[str, Any]] = None) -> str:
        """
        Analyze a car listing using the LLM.
        
        Args:
            car_data: Car data dictionary
            preferences: Optional user preferences
            
        Returns:
            Analysis text from LLM
        """
        if not self.provider:
            self.logger.error("No LLM provider initialized")
            return "Error: LLM provider not available"
        
        # Construct prompt with car data and preferences
        prompt = self._build_car_analysis_prompt(car_data, preferences)
        
        # Get completion from LLM
        return self.provider.generate_completion(prompt)
    
    def rank_cars(self, cars: List[Dict[str, Any]], preferences: Optional[Dict[str, Any]] = None) -> str:
        """
        Rank a list of cars based on user preferences.
        
        Args:
            cars: List of car dictionaries
            preferences: Optional user preferences
            
        Returns:
            Ranking analysis from LLM
        """
        if not self.provider:
            self.logger.error("No LLM provider initialized")
            return "Error: LLM provider not available"
        
        # Construct prompt with cars and preferences
        prompt = self._build_car_ranking_prompt(cars, preferences)
        
        # Get completion from LLM
        return self.provider.generate_completion(prompt)
    
    def _build_car_analysis_prompt(self, car_data: Dict[str, Any], preferences: Optional[Dict[str, Any]]) -> str:
        """
        Build a prompt for car analysis.
        
        Args:
            car_data: Car data dictionary
            preferences: Optional user preferences
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""
Analyze the following pre-owned car listing and provide your professional assessment:

CAR DETAILS:
- Year: {car_data.get('year', 'Unknown')}
- Make: {car_data.get('make', 'Unknown')}
- Model: {car_data.get('model', 'Unknown')}
- Price: ${car_data.get('price', 'Unknown')}
- Source: {car_data.get('source', 'Unknown')}
"""
        
        # Add additional details if available
        if 'details' in car_data and car_data['details']:
            prompt += "\nADDITIONAL DETAILS:\n"
            for key, value in car_data['details'].items():
                prompt += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        # Add user preferences if provided
        if preferences:
            prompt += "\nUSER PREFERENCES:\n"
            for key, value in preferences.items():
                prompt += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        prompt += """
Please provide a concise analysis of this vehicle covering:
1. Value assessment (is this price reasonable for this vehicle?)
2. Potential concerns or red flags based on the listing
3. Key benefits of this vehicle
4. Overall recommendation (avoid, consider, or recommended)

Keep your analysis brief but insightful, focusing on the most important factors a buyer should consider.
"""
        
        return prompt
    
    def _build_car_ranking_prompt(self, cars: List[Dict[str, Any]], preferences: Optional[Dict[str, Any]]) -> str:
        """
        Build a prompt for ranking multiple cars.
        
        Args:
            cars: List of car dictionaries
            preferences: Optional user preferences
            
        Returns:
            Formatted prompt string
        """
        prompt = """
You are a pre-owned car buying expert. Analyze and rank the following vehicles based on value, reliability, and overall quality.
"""
        
        # Add user preferences if provided
        if preferences:
            prompt += "\nUSER PREFERENCES:\n"
            for key, value in preferences.items():
                prompt += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        # Add car listings
        prompt += "\nCAR LISTINGS:\n"
        
        for i, car in enumerate(cars, 1):
            prompt += f"\nCAR {i}:\n"
            prompt += f"- Year: {car.get('year', 'Unknown')}\n"
            prompt += f"- Make: {car.get('make', 'Unknown')}\n"
            prompt += f"- Model: {car.get('model', 'Unknown')}\n"
            prompt += f"- Price: ${car.get('price', 'Unknown')}\n"
            
            # Add additional details if available
            if 'details' in car and car['details']:
                for key, value in car['details'].items():
                    if key not in ['year', 'make', 'model', 'price']:
                        prompt += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        prompt += """
Please rank these vehicles from best to worst overall value, considering:
1. Price relative to market value
2. Expected reliability and maintenance costs
3. Alignment with user preferences
4. Overall condition and potential issues

For each of your top 3 recommendations, provide a brief justification (1-2 sentences).
For the remaining vehicles, simply list them in ranked order.
"""
        
        return prompt