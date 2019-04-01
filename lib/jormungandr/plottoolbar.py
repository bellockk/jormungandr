import wx
from matplotlib.backends.backend_wx import NavigationToolbar2Wx as NavigationToolbar


class PlotToolbar(NavigationToolbar):

    def __init__(self, plotCanvas, plot):

        # create the default toolbar
        NavigationToolbar.__init__(self, plotCanvas)
        self.plot = plot

        # remove the sub-plots button
        POSITION_OF_CONFIGURE_SUBPLOTS_BTN = 7
        self.DeleteToolByPos(POSITION_OF_CONFIGURE_SUBPLOTS_BTN)

        # add check-boxes for grid overlay, coordinate labels
        # and cursor coordinates
        self._checkboxes = {}
        self._checkboxes['cursor'] = wx.CheckBox(self, label='&Cursor Coords')
        self._checkboxes['grid'] = wx.CheckBox(self, label='Coord &Grid')
        self._checkboxes['gridlabel'] = wx.CheckBox(self, label='Grid &Labels')
        self.AddSeparator()
        self.AddControl(self._checkboxes['cursor'])
        self.AddControl(self._checkboxes['grid'])
        self.AddControl(self._checkboxes['gridlabel'])

        # bind the checkboxes
        self.Bind(
                wx.EVT_CHECKBOX, self.on_checkbox,
                id=self._checkboxes['cursor'].GetId()
                )
        self.Bind(
                wx.EVT_CHECKBOX, self.on_checkbox,
                id=self._checkboxes['grid'].GetId()
                )
        self.Bind(
                wx.EVT_CHECKBOX, self.on_checkbox,
                id=self._checkboxes['gridlabel'].GetId()
                )

        # default values for checkboxes
        self._checkboxes['cursor'].SetValue(wx.CHK_CHECKED)
        self._checkboxes['grid'].SetValue(wx.CHK_CHECKED)
        self._checkboxes['gridlabel'].SetValue(wx.CHK_CHECKED)

        self._zoom_pressed = False

        self.Realize()

    def on_checkbox(self, event):
        self.plot.set_cursor_coordinates_enabled(self._checkboxes['cursor'].GetValue())
        self.plot.set_coordinate_grid_enabled(self._checkboxes['grid'].GetValue())
        self.plot.set_grid_labels_enabled(self._checkboxes['gridlabel'].GetValue())
        self.plot.do_dynamic_update()

    def press_pan(self, event):
        """
        Callback for mouse button press in pan mode
        """
        # disable any buttons except 1 and 3
        if event.button != 1 and event.button != 3:
            return
        NavigationToolbar.press_pan(self, event)

    def drag_pan(self, event):
        """
        Callback for mouse motion in pan mode
        """
        NavigationToolbar.drag_pan(self, event)
        if event.button == 3:
            self.plot.set_right_click_zoomed()

    def release_pan(self, event):
        """
        Callback for mouse button release in pan mode
        """
        # disable any buttons except 1 and 3
        if event.button != 1 and event.button != 3:
            return
        NavigationToolbar.release_pan(self, event)

    def dynamic_update(self):
        """
        Dynamic updater for plot
        """
        NavigationToolbar.dynamic_update(self)
        self.plot.do_dynamic_update()

    def press_zoom(self, event):
        """
        Callback for mouse button press in zoom mode
        """
        # disable the weird right-click zoom rectangle
        if event.button != 1:
            return
        self._zoom_pressed = True
        NavigationToolbar.press_zoom(self, event)

    def release_zoom(self, event):
        """
        Callback for mouse button release in zoom mode
        """
        # disable the weird right-click zoom rectangle
        if event.button != 1:
            return
        self._zoom_pressed = False
        NavigationToolbar.release_zoom(self, event)
        self.plot.do_dynamic_update()

    def mouse_move(self, event):
        """
        Mouse motion callback
        """
        # update the text box with coordinates of cursor
        # FIXME: Make this a method
        if not self._zoom_pressed and event.inaxes:
            self.plot.on_mouse_move(event)

        # call the parent handler also
        NavigationToolbar.mouse_move(self, event)

    def home(self, *args):
        """
        Overloaded home method that resets the zoom, and re-draws meridians
        """
        NavigationToolbar.home(self, args)
        self.plot.do_dynamic_update()

    def back(self, *args):
        """
        Callback for the "back" button
        """
        NavigationToolbar.back(self, args)
        self.plot.do_dynamic_update()

    def forward(self, *args):
        """
        Callback for the "forward" button
        """
        NavigationToolbar.forward(self, args)
        self.plot.do_dynamic_update()
