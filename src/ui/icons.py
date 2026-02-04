"""Icon utility functions for the application.

Provides built-in system icons with Unicode fallbacks.
"""

from PyQt5.QtWidgets import QApplication, QStyle
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt


# Icon mappings: (QStyle.StandardPixmap, Unicode fallback)
ICON_MAPPINGS = {
    'delay': (QStyle.SP_FileDialogListView, '⏱️'),
    'left_click': (QStyle.SP_FileDialogListView, '🖱️'),
    'double_click': (QStyle.SP_FileDialogListView, '🖱️🖱️'),
    'play': (QStyle.SP_MediaPlay, '▶️'),
    'stop': (QStyle.SP_MediaStop, '⏸️'),
    'pause': (QStyle.SP_MediaPause, '⏸️'),
    'remove': (QStyle.SP_TrashIcon, '🗑️'),
    'delete': (QStyle.SP_TrashIcon, '🗑️'),
    'add': (QStyle.SP_FileDialogNewFolder, '➕'),
    'list': (QStyle.SP_FileDialogListView, '📋'),
    'process': (QStyle.SP_ComputerIcon, '💻'),
    'clock': (QStyle.SP_FileDialogListView, '⏱️'),
    'mouse': (QStyle.SP_FileDialogListView, '🖱️'),
    'cursor': (QStyle.SP_FileDialogListView, '🖱️'),
    'ok': (QStyle.SP_DialogOkButton, '✓'),
    'cancel': (QStyle.SP_DialogCancelButton, '✗'),
    'warning': (QStyle.SP_MessageBoxWarning, '⚠️'),
    'info': (QStyle.SP_MessageBoxInformation, 'ℹ️'),
    'keyboard': (QStyle.SP_FileDialogListView, '⌨️'),
    'hotkey': (QStyle.SP_FileDialogListView, '⌨️'),
    'image': (QStyle.SP_FileDialogListView, '🖼️'),
    'text': (QStyle.SP_FileDialogListView, '📝'),
}


def get_icon(icon_name: str, size: int = 16) -> QIcon:
    """Get an icon by name, trying system icon first, then Unicode fallback.
    
    Args:
        icon_name: Name of the icon (e.g., 'play', 'remove', 'delay')
        size: Size of the icon in pixels (default: 16)
    
    Returns:
        QIcon object
    """
    if icon_name not in ICON_MAPPINGS:
        # Return empty icon if not found
        return QIcon()
    
    style_pixmap, unicode_fallback = ICON_MAPPINGS[icon_name]
    
    # Try to get system icon
    app = QApplication.instance()
    if app:
        style = app.style()
        if style:
            system_icon = style.standardIcon(style_pixmap)
            if not system_icon.isNull():
                return system_icon
    
    # Fallback to Unicode (create a text-based icon)
    # Note: QIcon from text is complex, so we'll use a different approach
    # For now, return empty icon and handle Unicode in labels/buttons directly
    return QIcon()


def get_unicode_icon(icon_name: str) -> str:
    """Get Unicode character for an icon name.
    
    Args:
        icon_name: Name of the icon
    
    Returns:
        Unicode character string
    """
    if icon_name in ICON_MAPPINGS:
        return ICON_MAPPINGS[icon_name][1]
    return ''


def get_icon_text(icon_name: str, text: str = '') -> str:
    """Get text with icon prefix.
    
    Args:
        icon_name: Name of the icon
        text: Text to append after icon
    
    Returns:
        String with icon and text
    """
    icon_char = get_unicode_icon(icon_name)
    if icon_char and text:
        return f"{icon_char} {text}"
    elif icon_char:
        return icon_char
    return text


def create_icon_label(icon_name: str, text: str, parent=None):
    """Create a QLabel with icon and text.
    
    Args:
        icon_name: Name of the icon
        text: Text for the label
        parent: Parent widget
    
    Returns:
        QLabel with icon and text
    """
    from PyQt5.QtWidgets import QLabel, QHBoxLayout, QWidget
    
    widget = QWidget(parent)
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(5)
    
    icon_char = get_unicode_icon(icon_name)
    if icon_char:
        icon_label = QLabel(icon_char, widget)
        icon_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(icon_label)
    
    text_label = QLabel(text, widget)
    layout.addWidget(text_label)
    
    layout.addStretch()
    return widget

