"""Transparent screen overlay for selecting a crop area."""

from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
import win32gui
import win32con


class ScreenSelector(QDialog):
    """Transparent full-screen overlay for selecting a rectangle area"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_point = None
        self.end_point = None
        self.selection_rect = None
        self.selected_area = None
        
        # Make window transparent and frameless
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        
        # Make window transparent
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        
        # Set modal
        self.setModal(True)
        
        # Enable mouse tracking for selection
        self.setMouseTracking(True)
        
        # Set cursor to crosshair
        self.setCursor(Qt.CrossCursor)
        
        # Set window title for identification
        self.setWindowTitle("Screen Area Selector")
        
        # Set window to cover entire screen (but don't show yet)
        self._set_fullscreen()
    
    def _set_fullscreen(self):
        """Set window to cover all screens"""
        from PyQt5.QtWidgets import QApplication
        # Get primary screen geometry
        screen = QApplication.desktop().screenGeometry()
        self.setGeometry(0, 0, screen.width(), screen.height())
    
    def paintEvent(self, event):
        """Draw the selection rectangle"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw semi-transparent overlay
        overlay_color = QColor(0, 0, 0, 100)  # Semi-transparent black
        painter.fillRect(self.rect(), overlay_color)
        
        # Draw selection rectangle if we have one
        if self.selection_rect:
            # Clear the selected area (make it brighter)
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(self.selection_rect, QColor(0, 0, 0, 0))
            
            # Draw border around selection
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            pen = QPen(QColor(42, 165, 245, 255), 2, Qt.SolidLine)  # Blue border
            painter.setPen(pen)
            painter.drawRect(self.selection_rect)
            
            # Draw corner handles
            handle_size = 8
            handle_color = QColor(42, 165, 245, 255)
            brush = QBrush(handle_color)
            painter.setBrush(brush)
            painter.setPen(Qt.NoPen)
            
            # Top-left
            painter.drawRect(
                self.selection_rect.left() - handle_size // 2,
                self.selection_rect.top() - handle_size // 2,
                handle_size, handle_size
            )
            # Top-right
            painter.drawRect(
                self.selection_rect.right() - handle_size // 2,
                self.selection_rect.top() - handle_size // 2,
                handle_size, handle_size
            )
            # Bottom-left
            painter.drawRect(
                self.selection_rect.left() - handle_size // 2,
                self.selection_rect.bottom() - handle_size // 2,
                handle_size, handle_size
            )
            # Bottom-right
            painter.drawRect(
                self.selection_rect.right() - handle_size // 2,
                self.selection_rect.bottom() - handle_size // 2,
                handle_size, handle_size
            )
            
            # Draw size info
            width = self.selection_rect.width()
            height = self.selection_rect.height()
            info_text = f"{width} × {height}"
            
            # Position text above selection, or below if near top
            text_y = self.selection_rect.top() - 20
            if text_y < 20:
                text_y = self.selection_rect.bottom() + 20
            
            painter.setPen(QPen(QColor(255, 255, 255, 255), 1))
            painter.setFont(self.font())
            text_rect = painter.fontMetrics().boundingRect(info_text)
            text_x = self.selection_rect.center().x() - text_rect.width() // 2
            
            # Draw text background
            painter.fillRect(
                text_x - 4, text_y - text_rect.height() - 2,
                text_rect.width() + 8, text_rect.height() + 4,
                QColor(0, 0, 0, 180)
            )
            painter.drawText(text_x, text_y, info_text)
    
    def mousePressEvent(self, event):
        """Start selection"""
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.selection_rect = QRect(self.start_point, self.end_point)
            self.update()
    
    def mouseMoveEvent(self, event):
        """Update selection while dragging"""
        if self.start_point is not None:
            self.end_point = event.pos()
            # Create normalized rectangle
            self.selection_rect = QRect(
                min(self.start_point.x(), self.end_point.x()),
                min(self.start_point.y(), self.end_point.y()),
                abs(self.end_point.x() - self.start_point.x()),
                abs(self.end_point.y() - self.start_point.y())
            )
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Finish selection"""
        if event.button() == Qt.LeftButton and self.start_point is not None:
            if self.selection_rect and self.selection_rect.width() > 10 and self.selection_rect.height() > 10:
                # Store the selected area (screen coordinates)
                self.selected_area = (
                    self.selection_rect.x(),
                    self.selection_rect.y(),
                    self.selection_rect.width(),
                    self.selection_rect.height()
                )
                # Reset start point to prevent further dragging
                self.start_point = None
                # Accept the selection
                self.accept()
            else:
                # Selection too small, cancel
                self.start_point = None
                self.reject()
    
    def keyPressEvent(self, event):
        """Handle keyboard events"""
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            if self.selection_rect and self.selection_rect.width() > 10 and self.selection_rect.height() > 10:
                # Finalize selection
                self.selected_area = (
                    self.selection_rect.x(),
                    self.selection_rect.y(),
                    self.selection_rect.width(),
                    self.selection_rect.height()
                )
                self.accept()
            else:
                self.reject()
        else:
            super().keyPressEvent(event)
    
    def accept(self):
        """Close and return selected area"""
        # Ensure selected_area is set before accepting
        if self.selection_rect and not self.selected_area:
            self.selected_area = (
                self.selection_rect.x(),
                self.selection_rect.y(),
                self.selection_rect.width(),
                self.selection_rect.height()
            )
        # Call parent accept to set result code properly
        super().accept()
    
    def reject(self):
        """Cancel selection"""
        self.selected_area = None
        # Call parent reject to set result code properly
        super().reject()
    
    def get_selected_area(self):
        """Get the selected area coordinates (x, y, width, height) in screen coordinates"""
        return self.selected_area
    
    @staticmethod
    def select_area(parent=None, target_hwnd=None):
        """
        Static method to show the selector and return selected area.
        
        Args:
            parent: Parent widget
            target_hwnd: Optional window handle to convert coordinates to client coordinates
        
        Returns:
            Tuple (x, y, width, height) in screen coordinates, or None if cancelled.
            If target_hwnd is provided, coordinates are relative to the window client area.
        """
        try:
            from PyQt5.QtWidgets import QApplication, QMainWindow
            
            # Hide all application windows EXCEPT the parent dialog (to preserve its exec_() loop)
            hidden_windows = []
            
            # Find and hide ALL visible top-level windows (main windows, widgets)
            # but DO NOT hide the parent dialog if it's modal
            main_window = None
            was_minimized = False
            
            # First, collect all visible top-level widgets
            all_widgets = QApplication.topLevelWidgets()
            
            # Find main window first (if any)
            for widget in all_widgets:
                if isinstance(widget, QMainWindow) and widget.isVisible():
                    main_window = widget
                    was_minimized = widget.isMinimized()
                    if not was_minimized:
                        hidden_windows.append(('main', widget))
                        widget.showMinimized()
                        QApplication.processEvents()
                    break
            
            # Hide ALL other visible top-level widgets (including QWidget windows)
            # BUT skip the parent dialog to preserve its modal exec_() loop
            for widget in all_widgets:
                # Skip if it's the main window (already handled), the parent dialog, or not visible
                if widget == main_window or widget == parent or not widget.isVisible():
                    continue
                
                # Hide any visible top-level widget (QWidget, QDialog, etc.)
                # This includes the "Capture Actions" window which is a QWidget
                hidden_windows.append(('other', widget))
                widget.hide()
                QApplication.processEvents()
            
            # Also check parent chain for main window if not found yet
            if not main_window and parent:
                widget = parent
                while widget:
                    if isinstance(widget, QMainWindow):
                        main_window = widget
                        was_minimized = widget.isMinimized()
                        if not was_minimized:
                            hidden_windows.append(('main', widget))
                            widget.showMinimized()
                            QApplication.processEvents()
                        break
                    widget = widget.parent()
            
            selector = ScreenSelector(None)  # Don't set parent to avoid event loop conflicts
            # Show and bring to front
            selector.show()
            selector.raise_()
            selector.activateWindow()
            selector.setFocus()
            
            # Run the event loop
            result = selector.exec_()
            
            # Restore all hidden windows (but parent dialog should still be visible)
            for window_type, window in hidden_windows:
                if window_type == 'main' and not was_minimized:
                    window.showNormal()
                    window.raise_()
                    window.activateWindow()
                elif window_type in ('other',):  # Changed from ('dialog', 'other') to just ('other',)
                    window.show()
                    window.raise_()
                    window.activateWindow()
            
            # Bring parent dialog back to front if it exists
            if parent and parent.isVisible():
                parent.raise_()
                parent.activateWindow()
                parent.setFocus()
            
            QApplication.processEvents()
            
            # Check if dialog was accepted
            if result == QDialog.Accepted:
                area = selector.get_selected_area()
            else:
                area = None
            if area and target_hwnd:
                # Convert screen coordinates to client coordinates
                try:
                    screen_x, screen_y = area[0], area[1]
                    # Convert screen point to client point
                    client_point = win32gui.ScreenToClient(target_hwnd, (screen_x, screen_y))
                    # Return client coordinates
                    return (client_point[0], client_point[1], area[2], area[3])
                except:
                    # If conversion fails, return screen coordinates
                    return area
            
            return area
        except Exception as e:
            import traceback
            traceback.print_exc()
            # Try to restore window even on error
            try:
                from PyQt5.QtWidgets import QApplication, QMainWindow
                for widget in QApplication.topLevelWidgets():
                    if isinstance(widget, QMainWindow):
                        widget.showNormal()
                        break
            except:
                pass
            return None

