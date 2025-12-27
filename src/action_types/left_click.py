"""Left click action type."""

from PyQt5.QtWidgets import QDialog

from src.action_types.base import BaseActionType
from src.action_types.common import ClickActionDialog


class LeftClickActionType(BaseActionType):
    """Action type for left clicks"""
    
    def get_type_id(self) -> str:
        return "left_click"
    
    def get_display_name(self) -> str:
        return "Left Click"
    
    def create_dialog(self, parent=None) -> QDialog:
        return ClickActionDialog("left_click", parent)
    
    def format_action_display(self, action_data: dict) -> str:
        return f"Left Click at ({action_data['x']}, {action_data['y']})"
    
    def validate_action_data(self, action_data: dict) -> bool:
        return "x" in action_data and "y" in action_data

