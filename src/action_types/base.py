"""Base class for all action types."""

from abc import ABC, abstractmethod
from PyQt5.QtWidgets import QDialog


class BaseActionType(ABC):
    """Base class for all action types"""
    
    def __init__(self):
        self.type_id = self.get_type_id()
        self.display_name = self.get_display_name()
    
    @abstractmethod
    def get_type_id(self) -> str:
        """Return the unique type identifier (e.g., 'delay', 'left_click')"""
        pass
    
    @abstractmethod
    def get_display_name(self) -> str:
        """Return the display name shown in the UI (e.g., 'Delay', 'Left Click')"""
        pass
    
    @abstractmethod
    def create_dialog(self, parent=None) -> QDialog:
        """Create and return the dialog for this action type"""
        pass
    
    @abstractmethod
    def format_action_display(self, action_data: dict) -> str:
        """Format the action for display in the action list"""
        pass
    
    def validate_action_data(self, action_data: dict) -> bool:
        """Validate action data. Override if needed."""
        return True

