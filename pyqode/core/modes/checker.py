#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Colin Duquesnoy
#
# This file is part of pyQode.
#
# pyQode is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# pyQode is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with pyQode. If not, see http://www.gnu.org/licenses/.
#
"""
This module contains the checker mode, a base class for code checker modes.
"""
import multiprocessing
from pyqode.core import logger
from pyqode.core.mode import Mode
from pyqode.core.system import DelayJobRunner
from pyqode.core.panels.marker import Marker
from pyqode.core.decoration import TextDecoration
from pyqode.qt import QtCore, QtGui


#: Status value for an information message
MSG_STATUS_INFO = 0
#: Status value for a warning message
MSG_STATUS_WARNING = 1
#: Status value for an error message
MSG_STATUS_ERROR = 2

#: Check is triggered when text has changed
CHECK_TRIGGER_TXT_CHANGED = 0
#: Check is triggered when text has been saved.
CHECK_TRIGGER_TXT_SAVED = 1


class CheckerMessage(object):
    """
    A message associates a description with a status and few other information
    such as line and column number, custom icon (to override the status icon).

    A message will be displayed in the editor's marker panel and/or as a
    TextDecoration (if status is error or warning).
    """
    ICONS = {MSG_STATUS_INFO: ("marker-info",
                               ":/pyqode-icons/rc/dialog-info.png"),
             MSG_STATUS_WARNING: ("marker-warning",
                                  ":/pyqode-icons/rc/dialog-warning.png"),
             MSG_STATUS_ERROR: ("marker-error",
                                ":/pyqode-icons/rc/dialog-error.png")}

    COLORS = {MSG_STATUS_INFO: "#4040DD",
              MSG_STATUS_WARNING: "#DDDD40",
              MSG_STATUS_ERROR: "#DD4040"}

    @classmethod
    def statusToString(cls, status):
        strings = {MSG_STATUS_INFO: "Info", MSG_STATUS_WARNING: "Warning",
                   MSG_STATUS_ERROR: "Error"}
        return strings[status]

    @property
    def statusString(self):
        return self.statusToString(self.status)

    def __init__(self, description, status, line, col=None, icon=None,
                 color=None, filename=None):
        """
        :param description: The message description (used as a tooltip)
        :param status:
        :param line:
        :param col:
        :param icon:
        :param color:
        """
        assert 0 <= status <= 2
        self.description = description
        self.status = status
        self.line = line
        self.col = col
        self.color = color
        if self.color is None:
            self.color = self.COLORS[status]
        self.icon = icon
        if self.icon is None:
            self.icon = self.ICONS[status]
        self._marker = None
        self._decoration = None
        self.filename = filename

    def __repr__(self):
        return "{0} {1}".format(self.description, self.line)


class CheckerMode(Mode, QtCore.QObject):
    """
    This mode is an abstract base class for code checker modes.

    The checker will run an analysis job (in a background thread when the
    editor's text changed and will take care of displaying messages emitted by
    the addMessageRequested.

    To create a concrete checker you must override the run method and use the
    addMessageRequested signal to add messages to the ui from the background
    thread.

    The run method will receive a clone of the editor's text document and the
    current file path.
    """

    addMessagesRequested = QtCore.Signal(object, bool)
    clearMessagesRequested = QtCore.Signal()

    def __init__(self, process_func,
                 delay=500,
                 clearOnRequest=True, trigger=CHECK_TRIGGER_TXT_CHANGED,
                 showEditorTooltip=True):
        Mode.__init__(self)
        QtCore.QObject.__init__(self)
        self.__jobRunner = DelayJobRunner(self, nbThreadsMax=1, delay=delay)
        self.__messages = []
        self.__process_func = process_func
        self.__trigger = trigger
        self.__mutex = QtCore.QMutex()
        self.__clearOnRequest = clearOnRequest
        self.__showTooltip = showEditorTooltip

    def addMessage(self, messages, clear=False):
        """
        Adds a message.

        .. warning: Do not use this method from the run method, use
                    addMessageRequested signal instead.

        :param messages: A list of messages or a single message
        """
        if clear:
            self.clearMessages()
        if isinstance(messages, CheckerMessage):
            messages = [messages]
        nbMsg = len(messages)
        if nbMsg > 20:
            nbMsg = 20
        for message in messages[0:nbMsg]:
            self.__messages.append(message)
            if message.line:
                if hasattr(self.editor, "markerPanel"):
                    message._marker = Marker(message.line, message.icon,
                                             message.description)
                    self.editor.markerPanel.addMarker(message._marker)
                tooltip = None
                if self.__showTooltip:
                    tooltip = message.description
                message._decoration = TextDecoration(self.editor.textCursor(),
                                                     startLine=message.line,
                                                     tooltip=tooltip,
                                                     draw_order=3)
                message._decoration.setFullWidth(True)
                message._decoration.setError(color=QtGui.QColor(message.color))
                self.editor.addDecoration(message._decoration)
        if hasattr(self.editor, "markerPanel"):
            self.editor.markerPanel.repaint()

    def removeMessage(self, message):
        """
        Remove the message

        :param message: Message to remove
        """
        self.__messages.remove(message)
        if message._marker:
            self.editor.markerPanel.removeMarker(message._marker)
        if message._decoration:
            self.editor.removeDecoration(message._decoration)

    def clearMessages(self):
        """
        Clears all messages.

        .. warning: Do not use this method from the run method, use
                    clearMessagesRequested signal instead.
        """
        while len(self.__messages):
            self.removeMessage(self.__messages[0])
        if hasattr(self.editor, "markerPanel"):
            self.editor.markerPanel.repaint()

    def _onStateChanged(self, state):
        if state:
            if self.__trigger == CHECK_TRIGGER_TXT_CHANGED:
                self.editor.textChanged.connect(self.requestAnalysis)
            elif self.__trigger == CHECK_TRIGGER_TXT_SAVED:
                self.editor.textSaved.connect(self.requestAnalysis)
                self.editor.newTextSet.connect(self.requestAnalysis)
            self.addMessagesRequested.connect(self.addMessage)
            self.clearMessagesRequested.connect(self.clearMessages)
        else:
            if self.__trigger == CHECK_TRIGGER_TXT_CHANGED:
                self.editor.textChanged.disconnect(self.requestAnalysis)
            elif self.__trigger == CHECK_TRIGGER_TXT_SAVED:
                self.editor.textSaved.disconnect(self.requestAnalysis)
                self.editor.newTextSet.disconnect(self.requestAnalysis)
            self.addMessagesRequested.disconnect(self.addMessage)
            self.clearMessagesRequested.disconnect(self.clearMessages)

    def __runAnalysis(self, code, filePath, fileEncoding):
        """
        Creates a subprocess. The subprocess receive a queue for storing
        results and the code and filePath parameters. The subprocess must fill
        the queue with the message it wants to be displayed.
        """
        try:
            q = multiprocessing.Queue()
            p = multiprocessing.Process(
                target=self.__process_func, name="%s process" % self.name,
                args=(q, code, filePath, fileEncoding))
            p.start()
            try:
                self.addMessagesRequested.emit(q.get(), True)
            except IOError:
                pass
            p.join()
        except OSError as e:
            logger.error("%s: failed to run analysis, %s" (self.name, e))

    def requestAnalysis(self):
        """ Request an analysis job. """
        if self.__clearOnRequest:
            self.clearMessages()
        self.__jobRunner.requestJob(self.__runAnalysis, True,
                                    self.editor.toPlainText(),
                                    self.editor.filePath,
                                    self.editor.fileEncoding)


if __name__ == "__main__":
    import sys
    import random
    from pyqode.core import QGenericCodeEdit, MarkerPanel

    try:
        import faulthandler
        faulthandler.enable()
    except ImportError:
        pass

    class FancyChecker(CheckerMode):
        """
        Example checker. Clear messages and add a message of each status on a
        randome line.
        """
        IDENTIFIER = "fancyChecker"
        DESCRIPTION = "An example checker, does not actually do anything " \
                      "usefull"

        def run(self, document, filePath):
            self.clearMessagesRequested.emit()
            msg = CheckerMessage(
                "A fancy info message", MSG_STATUS_INFO,
                random.randint(1, self.editor.lineCount()))
            self.addMessagesRequested.emit(msg)
            msg = CheckerMessage(
                "A fancy warning message", MSG_STATUS_WARNING,
                random.randint(1, self.editor.lineCount()))
            self.addMessagesRequested.emit(msg)
            msg = CheckerMessage(
                "A fancy error message", MSG_STATUS_ERROR,
                random.randint(1, self.editor.lineCount()))
            self.addMessagesRequested.emit(msg)

    def main():
        app = QtGui.QApplication(sys.argv)
        win = QtGui.QMainWindow()
        edit = QGenericCodeEdit()
        win.setCentralWidget(edit)
        edit.installMode(FancyChecker(trigger=CHECK_TRIGGER_TXT_CHANGED))
        edit.installPanel(MarkerPanel())
        edit.openFile(__file__)
        win.show()
        app.exec_()

    sys.exit(main())
