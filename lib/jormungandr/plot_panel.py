import wx
from wx.lib.embeddedimage import PyEmbeddedImage

from pyembeddedimage_to_png import pyembeddedimage_to_png

import cartopy.crs as ccrs

from numpy import pi
import numpy as np

from matplotlib.figure import Figure
from matplotlib._png import read_png

from matplotlib.offsetbox import TextArea
from matplotlib.offsetbox import AnnotationBbox
from matplotlib.offsetbox import OffsetImage

from matplotlib.font_manager import FontProperties

from plottoolbar import PlotToolbar
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as PlotFigureCanvas

NUM_GRID_LINES = 5
MOTION_DISPLAY_FONT_SIZE = 3
GRID_LABEL_FONT_SIZE = 2.5


class PlotPanel(wx.Panel):

    def __init__(self, parent, statusbar):
        wx.Panel.__init__(self, parent, -1, size=(50, 50))
        self.statusbar = statusbar

        self.plot_handl = None
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.figure = Figure(None, dpi=300)
        self.ax = self.figure.add_axes([0, 0, 1, 1], frameon=False, projection=ccrs.PlateCarree())
        self.canvas = PlotFigureCanvas(self, -1, self.figure)
        self.toolbar = PlotToolbar(self.canvas, self)

        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.sizer.Add(self.toolbar, 0, wx.EXPAND)

        # Clear artifacts
        self.clear_artifacts()

        # Bind events
        self.figure.canvas.mpl_connect('button_release_event', self.onclick)
        self.ax.callbacks.connect('xlim_changed', self.on_xlims_change)
        self.ax.callbacks.connect('ylim_changed', self.on_ylims_change)

        # setup empty list of meridians and parallels
        self.meridians_w = {}
        self.meridians_b = {}
        self.parallels_w = {}
        self.parallels_b = {}

        self.labels = []

        self.nlons = NUM_GRID_LINES
        self.nlats = NUM_GRID_LINES
        self.lons = []
        self.lats = []
        self.latll = -90
        self.latur = 90
        self.lonll = -180
        self.lonur = 180

        self.motion_display_font = FontProperties()
        self.motion_display_font.set_size(MOTION_DISPLAY_FONT_SIZE)
        self.motion_display_font.set_family('monospace')

        self.grid_label_font = FontProperties()
        self.grid_label_font.set_size(GRID_LABEL_FONT_SIZE)
        self.grid_label_font.set_family('monospace')

        self.map = None
        self.motion_display = None

        self._rc_zoomed = False

        self.cursor_coordinates_enabled = True
        self.coordinate_grid_enabled = True
        self.grid_labels_enabled = True

    def set_cursor_coordinates_enabled(self, enabled):
        self.cursor_coordinates_enabled = enabled

        # apply immediately
        if not enabled:
            if self.motion_display:
                self.motion_display.remove()
                self.figure.canvas.draw()
            self.motion_display = None

    def set_coordinate_grid_enabled(self, enabled):
        self.coordinate_grid_enabled = enabled

    def set_grid_labels_enabled(self, enabled):
        self.grid_labels_enabled = enabled

    def on_xlims_change(axes):
        pass

    def on_ylims_change(axes):
        pass

    def on_mouse_move(self, event):
        if not self.map:
            return
        lon, lat = self.map(event.xdata, event.ydata, inverse=True)
        lonll = max(self.lonll, self.map.llcrnrlon)
        lonur = min(self.lonur, self.map.urcrnrlon)
        latll = max(self.latll, self.map.llcrnrlat)
        latur = min(self.latur, self.map.urcrnrlat)
        if lat >= latll and lat <= latur and \
                lon >= lonll and lon <= lonur and \
                self.map.projection == 'cyl' and \
                self.cursor_coordinates_enabled:
            if self.motion_display is None:
                # setup coordinate display for mouse motion
                self.motion_display = self.ax.annotate(
                        s="(NaN, NaN)",
                        xy=(0.995, 0.995),
                        xycoords='axes fraction',
                        fontproperties=self.motion_display_font,
                        verticalalignment='top',
                        horizontalalignment='right',
                        bbox=dict(facecolor='white', alpha=1.0, pad=0.2, lw=0.2)
                        )

            display_lon = self.wrap_lon_at_day_boundary(lon)
            self.motion_display.set_text('(%+10.5f,%+10.5f)' % (display_lon, lat))
            self.ax.draw_artist(self.motion_display)
            self.canvas.blit(self.motion_display.get_window_extent())
        else:
            if self.motion_display:
                self.motion_display.remove()
                self.figure.canvas.draw()
            self.motion_display = None

    def wrap_lon_at_day_boundary(self, lon):
        wrapped_lon = lon
        while wrapped_lon < -180:
            wrapped_lon += 360.0
        while wrapped_lon > 180:
            wrapped_lon -= 360.0
        return wrapped_lon

    def do_dynamic_update(self):
        if not self.map:
            return

        # update meridians
        self._plot_meridians_and_parallels()
        self.figure.canvas.draw()

    def set_right_click_zoomed(self):
        self._rc_zoomed = True

    def onclick(self, event):
        if event is None or event.button != 3 or not event.inaxes:
            return
        if self._rc_zoomed:
            self._rc_zoomed = False
            return
        self.click_event = event
        menu = wx.Menu()
        menu.Append(wx.ID_ANY, "Add Point Here",
                    "Adds a point where the mouse was clicked on the map",
                    wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.callback, id=wx.ID_ANY)
        if self.canvas.HasCapture():
            self.canvas.ReleaseMouse()
        wx.CallAfter(self.PopupMenu, menu)

    def callback(self, event):
        self.map.plot(self.click_event.xdata, self.click_event.ydata,
                      'r.', markersize=1.)
        self.figure.canvas.draw()

    def clear_artifacts(self):
        for artifact in ['artists', 'lines', 'patches']:
            while getattr(self.ax, 'artists') != []:
                getattr(self.ax, 'artists')[0].remove()
        self.artifacts = {'artists': [],
                          'lines': [],
                          'patches': []}

    def updatePlot(self, attrs):

        self.statusbar.SetStatusText('Plotting... (Please Be Patient)')
        self.ax.clear()
        self.plot(attrs)
        self.statusbar.SetStatusText('Ready')

    def plot(self, param):
        # Create Map
        if not param:
            self.ax.stock_img()
            self.figure.canvas.draw()

            # # Create a really simple plot to fill the void on app startup.
            # self.map = Basemap(ax=self.ax, resolution=RESOLUTION_MAP['Crude'],
            #                    ellps='WGS84', suppress_ticks=True)
            # self.map.bluemarble()
            # self._plot_meridians_and_parallels()

            # # add the motion display to the list of texts for the new axes
            # if self.motion_display:
            #     self.ax.texts.append(self.motion_display)
            # self.figure.canvas.draw()
            return

        # projection_name = param['Projection']
        # projection_key = revlookup(PROJECTIONS, 'name', projection_name)
        # resolution = RESOLUTION_MAP[param['Resolution']]
        # kwargs = {'projection': projection_key,
        #           'ellps': 'WGS84',
        #           'suppress_ticks': True,
        #           'ax': self.ax,
        #           'resolution': resolution}
        # for p in PROJECTION_PARAMS[projection_key].keys():
        #     if 'rspherex' == p:
        #         kwargs['rsphere'] = (param[OPTIONS['rspherex']['name']],
        #                              param[OPTIONS['rspherey']['name']])
        #     elif 'rspherey' == p:
        #         pass
        #     else:
        #         kwargs[p] = param[OPTIONS[p]['name']]
        # self.map = Basemap(**kwargs)

        # # Draw Circle
        # self.draw_range_circle(param["longitude"],
        #                        param["geodetic_latitude"],
        #                        param["range"],
        #                        color='r',
        #                        alpha=0.5)

        # # Draw Blue Marble Texture
        # if param.get('Blue Marble', False):
        #     self.map.bluemarble()
        # else:
        #     self.map.fillcontinents(color='coral', lake_color='aqua')

        # # Draw Coastlines, borders, lines
        # if param.get('Coastlines', False):
        #     self.map.drawcoastlines()
        # if param.get('State Borders', False):
        #     self.map.drawstates()
        # if param.get('Country Borders', False):
        #     self.map.drawcountries()
        # self._plot_meridians_and_parallels()

        # # add the motion display to the list of texts for the new axes
        # if self.motion_display:
        #     self.ax.texts.append(self.motion_display)

        # self.figure.canvas.draw()

    def draw_great_circle(self, x1, y1, x2, y2, linewidth=.5, color='r'):
        self.map.drawgreatcircle(x1, y1, x2, y2, linewidth, color)

    def draw_text(self, text, x, y, xycoords='data', color='white',
                  size='xx-small'):
        self.ax.add_artist(
            AnnotationBbox(
                TextArea(
                    text, minimumdescent=False, textprops={'color': color,
                                                           'size': size})
                (x, y), xycoords='data', frameon=False))

    def draw_image(self, image, x, y, zoom=.1, alpha=.7, xycoords='data'):
        if isinstance(image, PyEmbeddedImage):
            png = pyembeddedimage_to_png(image)
        elif isinstance(image, basestring):
            png = read_png(image)
        else:
            png = image
        self.ax.add_artist(
            AnnotationBbox(
                OffsetImage(png, zoom=zoom, alpha=alpha),
                (x, y), xycoords=xycoords, frameon=False))

    def draw_range_circle(self, lat, lon, radius, color='r', alpha=.5):
        # FIXME Use the real radius of the earth at this lat/lon
        self.map.tissot(lon, lat,
                        180./pi * radius / 6370.,
                        256,
                        facecolor=color,
                        alpha=alpha)

    def _plot_meridians_and_parallels(self):
        """
        Plots meridians and parallels appropriate for the current zoom level
        """

        # if grid is off and labels are off wipe lines
        if not self.coordinate_grid_enabled and not self.grid_labels_enabled:
            self._label_grid([], [])
            self._clear_meridians_and_parallels()
            return

        # FIXME: Get this working for other projections
        if self.map.projection != 'cyl':
            self._clear_meridians_and_parallels()

            # FIXME: Make it an option to turn on/off white or black lines
            if self.coordinate_grid_enabled:
                lats = np.linspace(-90, 90, 10)
                self.parallels_b = self.map.drawparallels(
                        lats,
                        labels=[True, False, False, False],
                        fontsize=GRID_LABEL_FONT_SIZE,
                        linewidth=0.2,
                        dashes=[],
                        color='black'
                        )
                self.parallels_w = self.map.drawparallels(
                        lats,
                        labels=[False, False, False, False],
                        linewidth=0.2,
                        dashes=[1, 1],
                        color='white'
                        )
                lons = np.linspace(-180, 180, 10)
                self.meridians_b = self.map.drawmeridians(
                        lons,
                        labels=[False, False, False, True],
                        fontsize=GRID_LABEL_FONT_SIZE,
                        linewidth=0.2,
                        dashes=[],
                        color='black'
                        )
                self.meridians_w = self.map.drawmeridians(
                        lons,
                        labels=[False, False, False, False],
                        linewidth=0.2,
                        dashes=[1, 1],
                        color='white'
                        )

            self._label_grid(lons, lats)
            return

        # get the corners of the viewport
        self.lonll, self.latll, delta_lon, delta_lat = self.ax.viewLim.bounds
        self.latur = self.latll + delta_lat
        self.lonur = self.lonll + delta_lon

        # translate to lat/lon (if needed)
        self.lonll, self.latll = self.map(self.lonll, self.latll, inverse=True)
        self.lonur, self.latur = self.map(self.lonur, self.latur, inverse=True)

        if not self._zoom_is_valid():
            return

        # get the range of lat/lon of the current viewport
        lat_range = self.latur - self.latll
        lon_range = self.lonur - self.lonll

        # get the estimated number of parallels and meridians to plot
        nlons = round(NUM_GRID_LINES * 360.0 / lon_range)
        nlats = round(NUM_GRID_LINES * 180.0 / lat_range)

        found = False
        for kv in LAT_GRID_LOOKUP:
            if nlats <= kv[0]:
                self.nlats = kv[1]
                found = True
                break
        if not found:
            self.nlats = self._scale_grid_by_twos(nlats, self.nlats)

        found = False
        for kv in LON_GRID_LOOKUP:
            if nlons <= kv[0]:
                self.nlons = kv[1]
                found = True
                break
        if not found:
            self.nlons = self._scale_grid_by_twos(nlons, self.nlons)

        # return if we've got too few to plot
        if self.nlons <= 1 or self.nlats <= 1:
            return

        # calculate the actual meridian coordinates
        lons = np.linspace(-180, 180.0, self.nlons)
        lons = np.concatenate((lons-360.0, lons, lons+360.0))
        lats = np.linspace(-90.0, 90.0, self.nlats)

        # filter them to speed plotting
        lon_condition = lons >= self.lonll
        lons = np.extract(lon_condition, lons)
        lon_condition = lons <= self.lonur
        lons = np.extract(lon_condition, lons)

        lat_condition = lats >= self.latll
        lats = np.extract(lat_condition, lats)
        lat_condition = lats <= self.latur
        lats = np.extract(lat_condition, lats)

        # plot labels for each one
        self._label_grid(lons, lats)

        self.lats = lats
        self.lons = lons

        # plot new parallels/meridians
        # these are made up of a solid black line, and a dashed white line
        self._clear_meridians_and_parallels()

        # FIXME: Make it an option to turn on/off white or black lines
        if self.coordinate_grid_enabled:
            self.parallels_b = self.map.drawparallels(
                    lats,
                    labels=[False, False, False, False],
                    linewidth=0.2,
                    dashes=[],
                    color='black'
                    )
            self.parallels_w = self.map.drawparallels(
                    lats,
                    labels=[False, False, False, False],
                    linewidth=0.2,
                    dashes=[1, 1],
                    color='white'
                    )
            self.meridians_b = self.map.drawmeridians(
                    lons,
                    labels=[False, False, False, False],
                    linewidth=0.2,
                    dashes=[],
                    color='black'
                    )
            self.meridians_w = self.map.drawmeridians(
                    lons,
                    labels=[False, False, False, False],
                    linewidth=0.2,
                    dashes=[1, 1],
                    color='white'
                    )

    def _label_grid(self, lons, lats):
        """
        Plots labels on grid lines.
        """
        degree_sign = u'\N{DEGREE SIGN}'
        for label in self.labels:
            if label in self.ax.texts:
                label.remove()
        self.labels = []

        if self.grid_labels_enabled:

            # peg the corners on the projection boundaries
            lonll = max(self.lonll, self.map.llcrnrlon)
            lonur = min(self.lonur, self.map.urcrnrlon)
            latll = max(self.latll, self.map.llcrnrlat)
            latur = min(self.latur, self.map.urcrnrlat)

            for lat in lats:
                if lat > latur or lat < latll:
                    continue
                if lat >= 0:
                    NS = 'N'
                else:
                    NS = 'S'
                (d, m, sd) = self._to_dms(lat)
                self.labels.append(self.ax.text(lonll, lat,
                                                   "%02d%s%02d'%05.2f\"%s" % (abs(d), degree_sign, m, sd, NS),
                                                   fontproperties=self.grid_label_font, verticalalignment='center',
                                                   horizontalalignment='left',
                                                   bbox=dict(facecolor='white', alpha=0.5, pad=0.2, lw=0.2)))

            for lon in lons:
                if lon > lonur or lon < lonll:
                    continue

                # normalize
                display_lon = self.wrap_lon_at_day_boundary(lon)
                if display_lon >= 0:
                    NS = 'E'
                else:
                    NS = 'W'
                (d, m, sd) = self._to_dms(display_lon)
                self.labels.append(self.ax.text(lon, latll,
                                                   "%03d%s%02d'%05.2f\"%s" % (abs(d), degree_sign, m, sd, NS),
                                                   fontproperties=self.grid_label_font, rotation='vertical',
                                                   verticalalignment='bottom', horizontalalignment='center',
                                                   bbox=dict(facecolor='white', alpha=0.5, pad=0.2, lw=0.2)))

    def _to_dms(self, deg):
        """
        Converts degrees to degrees minutes seconds
        """
        d = int(deg)
        md = abs(deg - d) * 60.0
        m = int(md)
        sd = (md - m) * 60.0
        return [d, m, sd]

    def _scale_grid_by_twos(self, n_target, n_current):
        """
        Determines number of grid lines to plot via hopping by powers of 2
        """
        half_n_current = int(n_current / 2.0) + 1
        twice_n_current = round(n_current * 2) - 1
        if n_target < n_current and n_target > 1:
            while n_target < n_current:
                n_current = half_n_current
                half_n_current = int(n_current / 2.0) + 1
                if n_current < 3:
                    break
        else:
            while n_target >= twice_n_current:
                n_current = twice_n_current
                twice_n_current = round(n_current * 2) - 1

        # should be an odd number at this point, but make sure
        if n_current % 2 == 0:
            n_current += 1

        return n_current

    def _zoom_is_valid(self):
        """
        Checks if zoom level is valid
        """
        # check if corners are valid
        try:
            delta_lon = self.lonur - self.lonll
            delta_lat = self.latur - self.latll
        except:
            return False
        return True

    def _clear_meridians_and_parallels(self):
        """
        Clears currently plotted meridians and parallels
        """
        # clear old meridians and parallels
        # these are made up of a solid black line, and a dashed white line
        for par in self.parallels_w:
            for item in self.parallels_w[par]:
                if len(item) > 0:
                    if item[0] in self.ax.lines:
                        item[0].remove()
        self.parallels_w.clear()

        for par in self.parallels_b:
            for item in self.parallels_b[par]:
                if len(item) > 0:
                    if item[0] in self.ax.lines:
                        item[0].remove()
        self.parallels_b.clear()

        for mer in self.meridians_w:
            for item in self.meridians_w[mer]:
                if len(item) > 0:
                    if item[0] in self.ax.lines:
                        item[0].remove()
        self.meridians_w.clear()

        for mer in self.meridians_b:
            for item in self.meridians_b[mer]:
                if len(item) > 0:
                    if item[0] in self.ax.lines:
                        item[0].remove()
        self.meridians_b.clear()
