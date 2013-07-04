#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# PCEF - Python/Qt Code Editing Framework
# Copyright 2013, Colin Duquesnoy <colin.duquesnoy@gmail.com>
#
# This software is released under the LGPLv3 license.
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
"""
This module contains the search and replace panel
"""
import sys
from pcef.qt import QtCore, QtGui
from pcef.core import constants
from pcef.core.panel import Panel

if sys.version_info[0] == 3:
    from pcef.core.ui.search_panel_ui3 import Ui_SearchPanel
else:
    from pcef.core.ui.search_panel_ui import Ui_SearchPanel


class SearchAndReplacePanel(Panel, Ui_SearchPanel):
    """
    Search (& replace) Panel. Allow the user to search for content in the editor

    All occurrences are highlighted using text decorations.

    The occurrence under the cursor is selected using the find method of the
    plain text edit. User can go backward and forward.

    The Panel add a few actions to the editor menu(search, replace, next,
    previous, replace, replace all)

    The Panel is shown with ctrl-f for a search, ctrl-r for a search and
    replace.

    The Panel is hidden with ESC or by using the close button (white cross).

    .. note:: The widget use a custom ui designed in Qt Designer
    """
    IDENTIFIER = "searchAndReplacePanel"
    DESCRIPTION = "Search and replace text in the editor"

    def __init__(self):
        Panel.__init__(self)
        Ui_SearchPanel.__init__(self)
        self.setupUi(self)


