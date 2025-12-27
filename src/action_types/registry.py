"""Action type registry for managing all action types."""

from src.action_types.base import BaseActionType
from src.action_types.delay import DelayActionType
from src.action_types.left_click import LeftClickActionType
from src.action_types.double_click import DoubleClickActionType


class ActionTypeRegistry:
    """Registry for managing all action types"""
    
    def __init__(self):
        self._action_types: dict[str, BaseActionType] = {}
        self._register_default_types()
    
    def _register_default_types(self):
        """Register default action types"""
        self.register(DelayActionType())
        self.register(LeftClickActionType())
        self.register(DoubleClickActionType())
    
    def register(self, action_type: BaseActionType):
        """Register an action type"""
        self._action_types[action_type.type_id] = action_type
    
    def get_by_type_id(self, type_id: str) -> BaseActionType:
        """Get action type by type ID"""
        return self._action_types.get(type_id)
    
    def get_by_display_name(self, display_name: str) -> BaseActionType:
        """Get action type by display name"""
        for action_type in self._action_types.values():
            if action_type.display_name == display_name:
                return action_type
        return None
    
    def get_all_display_names(self) -> list[str]:
        """Get all display names for populating the action type list"""
        return [action_type.display_name for action_type in self._action_types.values()]
    
    def get_all_types(self) -> list[BaseActionType]:
        """Get all registered action types"""
        return list(self._action_types.values())


# Global registry instance
_action_registry = None

def get_action_registry() -> ActionTypeRegistry:
    """Get the global action type registry"""
    global _action_registry
    if _action_registry is None:
        _action_registry = ActionTypeRegistry()
    return _action_registry

