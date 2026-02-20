"""
LLM Provider Factory

工厂模式：根据配置创建对应的 LLM provider
"""

from typing import Type, Dict
from .base import BaseLLMProvider
from .claude_provider import ClaudeProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider


class LLMProviderFactory:
    """工厂类：根据配置创建对应的 LLM provider"""

    _providers: Dict[str, Type[BaseLLMProvider]] = {
        "claude": ClaudeProvider,
        "anthropic": ClaudeProvider,  # Alias
        "openai": OpenAIProvider,
        "gpt": OpenAIProvider,  # Alias
        "gemini": GeminiProvider,
        "google": GeminiProvider,  # Alias
    }

    # Default models for each provider
    _default_models = {
        "claude": "claude-sonnet-4-5-20250929",
        "anthropic": "claude-sonnet-4-5-20250929",
        "openai": "gpt-3.5-turbo",
        "gpt": "gpt-3.5-turbo",
        "gemini": "gemini-1.5-pro",
        "google": "gemini-1.5-pro",
    }

    @classmethod
    def create(
        cls,
        provider_name: str,
        api_key: str,
        model: str = None,
        **kwargs
    ) -> BaseLLMProvider:
        """
        创建 LLM provider 实例

        Args:
            provider_name: Provider name (claude, openai, gemini)
            api_key: API key for the provider
            model: Model ID (optional, uses default if not specified)
            **kwargs: Additional provider-specific config

        Returns:
            BaseLLMProvider instance

        Raises:
            ValueError: If provider not supported
        """
        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            raise ValueError(
                f"Unknown provider: {provider_name}. "
                f"Supported: {', '.join(cls._providers.keys())}"
            )

        provider_class = cls._providers[provider_name]

        # 使用默认 model 如果没有指定
        if model is None:
            model = cls._default_models.get(provider_name)

        return provider_class(api_key=api_key, model=model, **kwargs)

    @classmethod
    def register_provider(
        cls,
        name: str,
        provider_class: Type[BaseLLMProvider],
        default_model: str = None
    ):
        """
        注册自定义 provider（可扩展性）

        Args:
            name: Provider name
            provider_class: Provider class (must inherit from BaseLLMProvider)
            default_model: Default model ID for this provider
        """
        if not issubclass(provider_class, BaseLLMProvider):
            raise TypeError(
                f"{provider_class} must inherit from BaseLLMProvider"
            )

        cls._providers[name] = provider_class

        if default_model:
            cls._default_models[name] = default_model

    @classmethod
    def list_providers(cls) -> list:
        """返回所有支持的 provider 名称"""
        return list(cls._providers.keys())
