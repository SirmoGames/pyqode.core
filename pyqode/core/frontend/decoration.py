from PyQt4 import QtGui, QtCore
from pyqode.core import logger


class _TextDecorationSignals(QtCore.QObject):
    """
    Holds the signals for a TextDecoration (as we cannot make it a QObject we
    need to store its signals in an external QObject).
    """
    clicked = QtCore.pyqtSignal(object)


class TextDecoration(QtGui.QTextEdit.ExtraSelection):
    """
    Helper class to quickly create a text decoration. The text decoration is an
    utility class that adds a few utility methods over the Qt ExtraSelection.

    In addition to the helper methods, a tooltip can be added to a decoration.
    Usefull for errors marks and so on...

    Text decoration expose 1 **clicked** signal stored in a separate QObject:
    :attr:`pyqode.core.TextDecoration.signals`

    .. code-block:: python

        deco = TextDecoration()
        deco.signals.clicked.connect(a_slot)

        def a_slot(decoration):
            print(decoration)
    """

    def __init__(self, cursor_or_bloc_or_doc, start_pos=None, end_pos=None,
                 start_line=None, end_line=None, draw_order=0, tooltip=None):
        """
        Creates a text decoration

        :param cursor_or_bloc_or_doc: Selection
        :type cursor_or_bloc_or_doc: QTextCursor or QTextBlock or QTextDocument

        :param start_pos: Selection start pos

        :param end_pos: Selection end pos

        .. note:: Use the cursor selection if startPos and endPos are none.
        """
        QtGui.QTextEdit.ExtraSelection.__init__(self)
        self.signals = _TextDecorationSignals()
        self.draw_order = draw_order
        self.tooltip = tooltip
        cursor = QtGui.QTextCursor(cursor_or_bloc_or_doc)
        if start_pos is not None:
            cursor.setPosition(start_pos)
        if end_pos is not None:
            cursor.setPosition(end_pos, QtGui.QTextCursor.KeepAnchor)
        if start_line is not None:
            cursor.movePosition(cursor.Start, cursor.MoveAnchor)
            cursor.movePosition(cursor.Down, cursor.MoveAnchor, start_line - 1)
        if end_line is not None:
            cursor.movePosition(cursor.Down, cursor.KeepAnchor,
                                end_line - start_line)
        self.cursor = cursor

    def contains_cursor(self, cursor):
        """
        Checks if the textCursor is in the decoration

        :param cursor: The text cursor to test
        :type cursor: QtGui.QTextCursor
        """
        return self.cursor.selectionStart() <= cursor.position() <= \
            self.cursor.selectionEnd()

    def set_as_bold(self):
        """ Uses bold text """
        self.format.setFontWeight(QtGui.QFont.Bold)

    def set_foreground(self, color):
        """ Sets the foreground color.
        :param color: Color
        :type color: QtGui.QColor
        """
        self.format.setForeground(color)

    def set_background(self, brush):
        """
        Sets the background brush.

        :param brush: Brush
        :type brush: QtGui.QBrush
        """
        self.format.setBackground(brush)

    def set_outline(self, color):
        """
        Uses an outline rectangle.

        :param color: Color of the outline rect
        :type color: QtGui.QColor
        """
        self.format.setProperty(QtGui.QTextFormat.OutlinePen,
                                QtGui.QPen(color))

    def set_full_width(self, flag=True, clear=True):
        """
        Sets full width selection.

        :param flag: True to use full width selection.
        :type flag: bool

        :param clear: True to clear any previous selection. Default is True.
        :type clear: bool
        """
        if clear:
            self.cursor.clearSelection()
        self.format.setProperty(QtGui.QTextFormat.FullWidthSelection, flag)

    def set_as_underlined(self, color=QtCore.Qt.blue):
        self.format.setUnderlineStyle(
            QtGui.QTextCharFormat.SingleUnderline)
        self.format.setUnderlineColor(color)

    def set_as_spell_check(self, color=QtCore.Qt.blue):
        """ Underlines text as a spellcheck error.

        :param color: Underline color
        :type color: QtGui.QColor
        """
        self.format.setUnderlineStyle(
            QtGui.QTextCharFormat.SpellCheckUnderline)
        self.format.setUnderlineColor(color)

    def set_as_error(self, color=QtCore.Qt.red):
        """ Highlights text as a syntax error.

        :param color: Underline color
        :type color: QtGui.QColor
        """
        self.format.setUnderlineStyle(
            QtGui.QTextCharFormat.SpellCheckUnderline)
        self.format.setUnderlineColor(color)

    def set_as_warning(self, color=QtGui.QColor("orange")):
        """
        Highlights text as a syntax warning

        :param color: Underline color
        :type color: QtGui.QColor
        """
        self.format.setUnderlineStyle(
            QtGui.QTextCharFormat.SpellCheckUnderline)
        self.format.setUnderlineColor(color)


def add_decoration(editor, decoration):
    """
    Adds a text decoration on a QCodeEdit instance

    :param editor: QCodeEdit instance
    :param decoration: Text decoration
    :type decoration: pyqode.core.TextDecoration
    """
    if decoration not in editor._extra_selections:
        editor._extra_selections.append(decoration)
        editor._extra_selections = sorted(
            editor._extra_selections, key=lambda sel: sel.draw_order)
        editor.setExtraSelections(editor._extra_selections)
        return True
    return False


def remove_decoration(editor, decoration):
    """
    Remove text decoration from a QCodeEdit instance.

    :param editor: QCodeEdit instance
    :param decoration: The decoration to remove
    :type decoration: pyqode.core.TextDecoration
    """
    try:
        editor._extra_selections.remove(decoration)
        editor.setExtraSelections(editor._extra_selections)
        return True
    except ValueError:
        logger.exception('cannot remove decoration %r' % decoration)
        return False


def clear_decorations(editor):
    """
    Clears all text decorations from a QCodeEdit instance.

    :param editor: QCodeEdit instance
    """
    editor._extra_selections[:] = []
    editor.setExtraSelections(editor._extra_selections)