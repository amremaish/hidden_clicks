"""Double click action type."""

from PyQt5.QtWidgets import QDialog

from src.action_types.base import BaseActionType
from src.action_types.common import ClickActionDialog


class DoubleClickActionType(BaseActionType):
    """Action type for double clicks"""
    
    def get_type_id(self) -> str:
        return "double_click"
    
    def get_display_name(self) -> str:
        return "Double Click"
    
    def create_dialog(self, parent=None) -> QDialog:
        return ClickActionDialog("double_click", parent)
    
    def format_action_display(self, action_data: dict) -> str:
        return f"Double Click at ({action_data['x']}, {action_data['y']})"
    
    def validate_action_data(self, action_data: dict) -> bool:
        return "x" in action_data and "y" in action_data

