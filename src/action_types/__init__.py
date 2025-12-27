"""Action types package for the hidden clicks application.

This package contains all action type implementations:
- BaseActionType: Abstract base class for all action types
- DelayActionType: Delay/wait action
- LeftClickActionType: Left mouse click action
- DoubleClickActionType: Double mouse click action
- ActionTypeRegistry: Registry for managing action types
- get_action_registry(): Function to get the global registry instance
"""

from src.action_types.base import BaseActionType
from src.action_types.registry import ActionTypeRegistry, get_action_registry
from src.action_types.delay import DelayActionType, DelayActionDialog
from src.action_types.left_click import LeftClickActionType
from src.action_types.double_click import DoubleClickActionType
from src.action_types.end_file_reader import EndFileReaderActionType, EndFileReaderDialog
from src.action_types.hotkey import HotkeyActionType, HotkeyActionDialog
from src.action_types.image_matcher import ImageMatcherActionType, ImageMatcherDialog
from src.action_types.common import CoordinateSignal, ClickActionDialog

__all__ = [
    'BaseActionType',
    'ActionTypeRegistry',
    'get_action_registry',
    'DelayActionType',
    'DelayActionDialog',
    'LeftClickActionType',
    'DoubleClickActionType',
    'EndFileReaderActionType',
    'EndFileReaderDialog',
    'HotkeyActionType',
    'HotkeyActionDialog',
    'ImageMatcherActionType',
    'ImageMatcherDialog',
    'CoordinateSignal',
    'ClickActionDialog',
]

