"""
User Alert — Real-Time Human Notification

The UserAlertSystem notifies the human in real-time when the shield
blocks actions, detects exfiltration attempts, or requires human decision.

Alerts are:
    - Immediate: Real-time notification of critical events
    - Persistent: Stored for review until acknowledged
    - Actionable: Include clear options for human response
    - Auditable: Every alert is logged in the consent trail

Principle: The human is always in the loop. Silence is not consent.
"""

from __future__ import annotations

import time
from typing import Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class AlertPriority(Enum):
    """Priority levels for user alerts."""
    INFO = "info"           # Informational, no action needed
    WARNING = "warning"     # Attention recommended
    URGENT = "urgent"       # Action required soon
    EMERGENCY = "emergency" # Immediate action required


class AlertCategory(Enum):
    """Categories of alerts."""
    DATA_BLOCKED = "data_blocked"       # DataGuardian blocked outbound data
    INFERENCE_BLOCKED = "inference_blocked"  # InferenceFilter blocked LLM call
    EXFIL_DETECTED = "exfil_detected"   # ExfiltrationDetector found anomaly
    INTENT_REVOKED = "intent_revoked"   # Intent was revoked
    CONSENT_REQUESTED = "consent_requested"  # Human approval needed
    AGENT_ERROR = "agent_error"         # Agent encountered error
    POLICY_VIOLATION = "policy_violation"  # Constraint engine blocked plan
    SYSTEM = "system"                   # General system notification


@dataclass
class UserAlert:
    """
    A single alert for the human user.
    
    Attributes:
        alert_id: Unique identifier
        priority: How urgent this is
        category: What kind of alert
        title: Short headline
        message: Detailed explanation
        actions: Available actions the human can take
        source: Which component generated the alert
        timestamp: When the alert was created
        acknowledged: Whether the human has seen it
        escalation_count: How many times this was re-sent
    """
    alert_id: str
    priority: AlertPriority
    category: AlertCategory
    title: str
    message: str
    actions: list[str] = field(default_factory=list)
    source: str = "system"
    timestamp: float = field(default_factory=time.time)
    acknowledged: bool = False
    escalation_count: int = 0
    
    def to_notification(self) -> dict:
        """Convert to a notification format for display."""
        return {
            "id": self.alert_id,
            "priority": self.priority.value,
            "category": self.category.value,
            "title": self.title,
            "message": self.message,
            "actions": self.actions,
            "source": self.source,
            "time": time.ctime(self.timestamp),
            "requires_action": self.priority in (
                AlertPriority.URGENT, AlertPriority.EMERGENCY
            ),
        }


class UserAlertSystem:
    """
    Real-time notification system for the human user.
    
    The UserAlertSystem ensures the human is always informed about
    what the agents are doing, what was blocked, and what requires
    their attention. Silence is not consent — if the human isn't
    aware, the system defaults to deny.
    
    Attributes:
        alert_queue: Pending alerts awaiting human attention
        alert_history: All alerts (including acknowledged)
        handlers: Registered notification handlers
    """
    
    def __init__(self):
        self.alert_queue: list[UserAlert] = []
        self.alert_history: list[UserAlert] = []
        self.handlers: list[Callable[[UserAlert], None]] = []
        self._counter: int = 0
    
    def register_handler(self, handler: Callable[[UserAlert], None]) -> None:
        """
        Register a handler for real-time alert delivery.
        
        Handlers could be:
            - Desktop notification
            - WebSocket push
            - Email/SMS for emergencies
            - Logging for audit trail
        
        Args:
            handler: Function called with each new alert
        """
        self.handlers.append(handler)
    
    def send_alert(
        self,
        priority: AlertPriority,
        category: AlertCategory,
        title: str,
        message: str,
        actions: Optional[list[str]] = None,
        source: str = "system",
    ) -> UserAlert:
        """
        Send an alert to the human.
        
        This creates the alert, adds it to the queue, notifies all
        registered handlers, and logs it in the audit trail.
        
        Args:
            priority: How urgent
            category: What kind of alert
            title: Short headline
            message: Detailed explanation
            actions: Available human actions (e.g., ["approve", "deny", "review"])
            source: Which component generated this
            
        Returns:
            The created UserAlert
        """
        self._counter += 1
        alert = UserAlert(
            alert_id=f"ALERT_{self._counter:04d}_{int(time.time())}",
            priority=priority,
            category=category,
            title=title,
            message=message,
            actions=actions or [],
            source=source,
        )
        
        # Add to queues
        self.alert_queue.append(alert)
        self.alert_history.append(alert)
        
        # Notify all handlers
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                # Handler failure shouldn't block the alert
                print(f"Alert handler failed: {e}")
        
        return alert
    
    def acknowledge(self, alert_id: str) -> bool:
        """
        Mark an alert as acknowledged by the human.
        
        Args:
            alert_id: The alert to acknowledge
            
        Returns:
            True if found and acknowledged
        """
        for alert in self.alert_queue:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                self.alert_queue.remove(alert)
                return True
        
        # Also check history for already-removed alerts
        for alert in self.alert_history:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        
        return False
    
    def get_pending(self, min_priority: Optional[AlertPriority] = None) -> list[UserAlert]:
        """
        Get pending (unacknowledged) alerts.
        
        Args:
            min_priority: Only return alerts at this priority or higher
            
        Returns:
            List of pending alerts
        """
        pending = [a for a in self.alert_queue if not a.acknowledged]
        
        if min_priority:
            priority_order = {
                AlertPriority.INFO: 0,
                AlertPriority.WARNING: 1,
                AlertPriority.URGENT: 2,
                AlertPriority.EMERGENCY: 3,
            }
            min_val = priority_order[min_priority]
            pending = [a for a in pending if priority_order[a.priority] >= min_val]
        
        return pending
    
    def escalate_unacknowledged(self, max_age_seconds: float = 300) -> list[UserAlert]:
        """
        Escalate alerts that haven't been acknowledged for too long.
        
        Args:
            max_age_seconds: How long before escalation
            
        Returns:
            List of escalated alerts
        """
        now = time.time()
        escalated = []
        
        for alert in self.alert_queue:
            if alert.acknowledged:
                continue
            
            age = now - alert.timestamp
            if age > max_age_seconds:
                alert.escalation_count += 1
                
                # Escalate priority
                escalation_map = {
                    AlertPriority.INFO: AlertPriority.WARNING,
                    AlertPriority.WARNING: AlertPriority.URGENT,
                    AlertPriority.URGENT: AlertPriority.EMERGENCY,
                    AlertPriority.EMERGENCY: AlertPriority.EMERGENCY,
                }
                alert.priority = escalation_map[alert.priority]
                
                # Re-notify handlers
                for handler in self.handlers:
                    try:
                        handler(alert)
                    except Exception:
                        pass
                
                escalated.append(alert)
        
        return escalated
    
    # Convenience methods for specific alert types
    
    def data_blocked(self, agent_id: str, reason: str) -> UserAlert:
        """Alert that the DataGuardian blocked outbound data."""
        return self.send_alert(
            priority=AlertPriority.WARNING,
            category=AlertCategory.DATA_BLOCKED,
            title=f"Data Transfer Blocked",
            message=f"Agent {agent_id} attempted to send data that was blocked: {reason}",
            actions=["review", "approve_once", "update_policy"],
            source="DataGuardian",
        )
    
    def inference_blocked(self, agent_id: str, reason: str) -> UserAlert:
        """Alert that the InferenceFilter blocked an LLM call."""
        return self.send_alert(
            priority=AlertPriority.WARNING,
            category=AlertCategory.INFERENCE_BLOCKED,
            title="LLM Call Blocked",
            message=f"Agent {agent_id}'s inference call was blocked: {reason}",
            actions=["review_prompt", "allow_override"],
            source="InferenceFilter",
        )
    
    def exfiltration_detected(self, agent_id: str, details: str) -> UserAlert:
        """Alert that the ExfiltrationDetector found suspicious behavior."""
        return self.send_alert(
            priority=AlertPriority.EMERGENCY,
            category=AlertCategory.EXFIL_DETECTED,
            title=f"Suspicious Activity: Agent {agent_id}",
            message=f"Potential data exfiltration detected: {details}",
            actions=["halt_agent", "investigate", "revoke_intent"],
            source="ExfiltrationDetector",
        )
    
    def consent_required(self, agent_id: str, description: str) -> UserAlert:
        """Alert that human consent is needed for an action."""
        return self.send_alert(
            priority=AlertPriority.URGENT,
            category=AlertCategory.CONSENT_REQUESTED,
            title="Approval Required",
            message=f"Agent {agent_id} requests permission to: {description}",
            actions=["approve", "deny", "review_details"],
            source="FlowController",
        )
