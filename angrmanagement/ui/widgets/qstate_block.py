
from PySide.QtGui import QColor, QPen
from PySide.QtCore import Qt

from ...config import Conf
from ...utils import locate_function
from .qgraph_object import QGraphObject


class QStateBlock(QGraphObject):

    HORIZONTAL_PADDING = 5
    VERTICAL_PADDING = 5
    LINE_MARGIN = 3

    def __init__(self, is_selected, symexec_view, state=None, history=None):
        super(QStateBlock, self).__init__()

        self.symexec_view = symexec_view
        self._workspace = self.symexec_view.workspace
        self._config = Conf

        self.state = state
        self.history = history
        if history is None and state is not None:
            self.history = state.history
        if history is not None and state is None:
            self.state = history.state.state
        self.selected = is_selected

        # widgets
        self._label_str = None
        self._function_str = None

        self._init_widgets()
        self._update_size()

    def _init_widgets(self):

        addr = None
        if self.state.regs._ip.symbolic:
            self._label_str = str(self.state.regs._ip)
        else:
            addr = self.state.regs._ip._model_concrete.value
            self._label_str = "%#x" % addr
        self._label_str = "State " + self._label_str

        if addr is None:
            self._function_str = "Unknown"
        else:
            the_func = locate_function(self._workspace.instance, addr)
            if the_func is None:
                # is it a SimProcedure?
                if self._workspace.instance.project.is_hooked(addr):
                    hooker = self._workspace.instance.project.hooked_by(addr)
                    self._function_str = "SimProcedure " + hooker.__class__.__name__.split('.')[-1]
                else:
                    self._function_str = "Unknown"
            else:
                offset = addr - the_func.addr
                if not the_func.name:
                    self._function_str = "%#x%+x" % (the_func.addr, offset)
                else:
                    self._function_str = "%s%+x" % (the_func.name, offset)
        self._function_str = "Function: %s" % self._function_str

    def paint(self, painter):
        """
        Paint a state block on the scene.

        :param painter:
        :return: None
        """

        normal_background = QColor(0xfa, 0xfa, 0xfa)
        selected_background = QColor(0xcc, 0xcc, 0xcc)

        # The node background
        if self.selected:
            painter.setBrush(selected_background)
        else:
            painter.setBrush(normal_background)
        painter.setPen(QPen(QColor(0xf0, 0xf0, 0xf0), 1.5))
        painter.drawRect(self.x, self.y, self.width, self.height)

        x = self.x
        y = self.y

        # The addr label
        addr_label_x = x + self.HORIZONTAL_PADDING
        addr_label_y = y + self.VERTICAL_PADDING
        painter.setPen(Qt.black)
        painter.drawText(addr_label_x, addr_label_y + self._config.symexec_font_ascent, self._label_str)

        y += self._config.symexec_font_height + self.LINE_MARGIN
        x = self.x

        # The function label
        function_label_x = x + self.HORIZONTAL_PADDING
        function_label_y = y + self.VERTICAL_PADDING
        painter.drawText(function_label_x, function_label_y + self._config.symexec_font_ascent, self._function_str)

    #
    # Events
    #

    def on_mouse_pressed(self, button, pos):
        if not self.selected:
            self.selected = True
            self.symexec_view.select_state_block(self)
            if self.state is not None:
                self.symexec_view.view_state(self.state)
            elif self.history is not None:
                weak_state = self.history.state
                state = weak_state.state
                self.symexec_view.view_state(state)
        else:
            self.selected = False
            self.symexec_view.deselect_state_block(self)
            self.symexec_view.view_state(None)
        self.symexec_view.redraw_graph()

    def on_mouse_doubleclicked(self, button, pos):
        if self.state is not None:
            self._workspace.viz(self.state.addr)
        elif self.history is not None:
            self._workspace.viz(self.history.state.addr)

    #
    # Private methods
    #

    def _update_size(self):
        width_candidates = [ self.HORIZONTAL_PADDING * 2 + len(self._label_str) * self._config.symexec_font_width,
                             self.HORIZONTAL_PADDING * 2 + len(self._function_str) * self._config.symexec_font_width
                             ]
        height_candidates = [ 0 ]
        self._width = max(width_candidates)
        self._height = max(height_candidates)

        self._width = max(100, self._width)
        self._height = max(50, self._height)
