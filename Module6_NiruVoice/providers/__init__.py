"""
Provider management module for Module6_NiruVoice

Handles multiple STT/TTS providers with health monitoring and failover
"""

from Module6_NiruVoice.providers.provider_manager import ProviderManager, ProviderConfig
from Module6_NiruVoice.providers.health_monitor import HealthMonitor, ProviderHealth
from Module6_NiruVoice.providers.fallback_strategy import FallbackStrategy, FallbackConfig

__all__ = [
    "ProviderManager",
    "ProviderConfig",
    "HealthMonitor",
    "ProviderHealth",
    "FallbackStrategy",
    "FallbackConfig",
]

