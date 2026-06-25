"""
SHIELD — The Barrier of the OBLISK

The shield sits between the SymbolicPlanner/Apex and the Agents.
It ensures that no vault data leaks through inference, no unauthorized
data leaves the device, and no agent behaves maliciously.

Components:
    - data_guardian.py: Monitors outbound data, blocks unauthorized exfiltration
    - inference_filter.py: Intercepts LLM calls, ensures no vault data leaks
    - exfiltration_detect.py: Behavioral analysis — is an agent trying to phone home?
    - user_alert.py: Real-time notification to human of blocked actions

Principle: Default deny. Every data movement is suspicious until proven innocent.
"""

from .data_guardian import DataGuardian
from .inference_filter import InferenceFilter
from .exfiltration_detect import ExfiltrationDetector
from .user_alert import UserAlertSystem

__all__ = ["DataGuardian", "InferenceFilter", "ExfiltrationDetector", "UserAlertSystem"]
