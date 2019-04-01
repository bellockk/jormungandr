import wx
import re
import itertools
import wx.propgrid as wxpg

from wx.propgrid import FloatProperty
from wx.propgrid import IntProperty
from wx.propgrid import BoolProperty
from wx.propgrid import StringProperty
from wx.propgrid import ArrayStringProperty
from wx.propgrid import FileProperty
from wx.propgrid import DirProperty

# Structure of Dictionary to load

INPUT_DATA = {'PropertyCategory': [
    {'title': 'Files',
     'properties': [
         {'title': 'Input File',
          'name': 'inputfile',
          'type': 'FileProperty'},
         {'title': 'Output Directory',
          'name': 'outpath',
          'type': 'DirProperty'}
     ]},
    {'title': 'Input Data',
     'properties': [
         {'title': 'Geodetic Latitude',
          'type': 'FloatProperty',
          'name': 'geodetic_latitude',
          'default': -28.54585,
          'help': 'Geodetic Latitude',
          'units': 'deg'},
         {'title': 'Longitude',
          'type': 'FloatProperty',
          'name': 'longitude',
          'default': 45.607865,
          'help': 'Longitude',
          'units': 'deg'},
         {'title': 'Range',
          'type': 'FloatProperty',
          'name': 'range',
          'default': 800,
          'warn': lambda val: val > 1000,
          'error': lambda val: val < 0 or val > 10000,
          'help': 'Range',
          'units': 'km'}
     ]}
]}


def compiletupleregex(size):
    return re.compile(r'\s*?\(\s*?(' +
                      r')\s*?,\s*?('.join(itertools.repeat(
                          r'[-+]?(?:(?:\d*\.\d+)|(?:\d+\.?))(?:[Ee][+-]?\d+)?',
                          size)) +
                      r')\s*?\)\s*?')


class SingleChoiceDialogAdapter(wxpg.PyEditorDialogAdapter):
    """ This demonstrates use of wxpg.PyEditorDialogAdapter.
    """
    def __init__(self, choices):
        wxpg.PyEditorDialogAdapter.__init__(self)
        self.choices = choices

    def DoShowDialog(self, propGrid, property):
        s = wx.GetSingleChoice("Message", "Caption", self.choices)
        if s:
            self.SetValue(s)
            return True
        return False


class SingleChoiceProperty(wxpg.PyStringProperty):
    def __init__(self, label, name=wxpg.PG_LABEL, choices=None, value=''):
        wxpg.PyStringProperty.__init__(self, label, name, value)

        # Prepare choices
        if not choices:
            choices = []
        self.dialog_choices = choices

    def GetEditor(self):
        # Set editor to have button
        return "TextCtrlAndButton"

    def GetEditorDialog(self):
        # Set what happens on button click
        return SingleChoiceDialogAdapter(self.dialog_choices)


class PropertyGridPanel(wx.Panel):
    def __init__(self, parent, plot):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.plot = plot

        self.pg = pg = wxpg.PropertyGridManager(
            self,
            style=wxpg.PG_SPLITTER_AUTO_CENTER |
            wxpg.PG_AUTO_SORT |
            wxpg.PG_TOOLBAR)

        # Show help as tooltips
        pg.SetExtraStyle(wxpg.PG_EX_HELP_AS_TOOLTIPS)

        # Bind events
        pg.Bind(wxpg.EVT_PG_CHANGED, self.OnPropGridChange)
        pg.Bind(wxpg.EVT_PG_RIGHT_CLICK, self.OnPropGridRightClick)

        # Parse the properties to insert into the propertygrid
        for property_category_index, property_category in enumerate(
                INPUT_DATA['PropertyCategory']):
            pg.Append(wxpg.PropertyCategory(
                '%s - %s' % (property_category_index + 1,
                             property_category['title'])))
            format_string = (
                str(property_category_index + 1) + '.%0' +
                str(len(str(len(property_category['properties']) + 1))) + 'd')
            for prop_index, prop in enumerate(property_category['properties']):
                self.append(format_string % (prop_index + 1), prop)

        # pg.Append(wxpg.PropertyCategory("2 - Plot Type"))
        # projection_names = sorted([PROJECTIONS[proj]['name']
        #                            for proj in PROJECTIONS])
        # proj = 'Cylindrical Equidistant'
        # pg.Append(SingleChoiceProperty("Projection",
        #                                choices=projection_names,
        #                                value=proj))

        self.pp = pg.Append(wxpg.PropertyCategory("3 - Projection Parameters"))
        self.pp_list = []

        pg.Append(wxpg.PropertyCategory("4 - Plot Properties"))
        pg.Append(wxpg.BoolProperty("Blue Marble", value=True))
        pg.Append(wxpg.BoolProperty("Coastlines", value=False))
        pg.Append(wxpg.BoolProperty("State Borders", value=False))
        pg.Append(wxpg.BoolProperty("Country Borders", value=False))
        pg.Append(wxpg.FloatProperty("Area Threshold", value=10000))
        # pg.Append(SingleChoiceProperty("Resolution", choices=RESOLUTION_KEYS,
        #                                value='Crude'))

        # Do Layout
        sizer.Add(pg, 1, wx.EXPAND)
        rowsizer = wx.BoxSizer(wx.HORIZONTAL)
        but = wx.Button(self, -1, "Update Plot")
        but.Bind(wx.EVT_BUTTON, self.OnUpdatePlotButtonEvent)
        rowsizer.Add(but, 1)
        sizer.Add(rowsizer, 0, wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)

        self.OnUpdatePlotButtonEvent()
        # self.OnProjectionChange(proj)

    def append(self, format_string, prop, parent=None):
        pass
        # argmap = {'default': 'value'}
        # ignore = {'properties', 'title', 'units', 'help', 'type', 'warn',
        #           'error', 'prefix', 'tag'}
        # prop['prefix'] = format_string
        # kwargs = {}
        # for key, value in prop.items():
        #     if key in ignore:
        #         continue
        #     if key in argmap:
        #         kwargs[argmap[key]] = value
        #     else:
        #         kwargs[key] = value
        # if prop['title'].isdigit():
        #     title = format_string
        # else:
        #     title = format_string + ' - ' + prop['title']
        # if 'units' in prop and prop['units']:
        #     title = '%s [%s]' % (title, prop['units'])
        # if parent:
        #     prop['pgid'] = self.pg.AppendIn(parent, globals()[prop['type']](
        #         title, **kwargs))
        # else:
        #     prop['pgid'] = self.pg.Append(globals()[prop['type']](
        #         title, **kwargs))
        # if 'help' in prop and prop['help']:
        #     self.pg.SetPropertyHelpString(prop['pgid'], prop['help'])
        # if 'properties' in prop:
        #     format_string = (
        #         format_string + '.%0' +
        #         str(len(str(len(prop['properties']) + 1))) + 'd')
        #     for prop_index, sub_prop in enumerate(prop['properties']):
        #         self.append(format_string % (prop_index + 1), sub_prop,
        #                     parent=prop['pgid'])

    def OnPropGridChange(self, event):
        p = event.GetProperty()
        field = p.GetName()
        value = p.GetValue()
        if p.GetName() == "Projection":
            self.OnProjectionChange(p.GetValueAsString())
        if field in INPUT_DATA:
            if 'warn' in INPUT_DATA[field]:
                try:
                    if not INPUT_DATA[field]['warn'](value):
                        p.SetBackgroundColour('yellow')
                except:
                    p.SetBackgroundColour('yellow')
            if 'error' in INPUT_DATA[field]:
                try:
                    if not INPUT_DATA[field]['error'](value):
                        p.SetBackgroundColour('red')
                except:
                    p.SetBackgroundColour('red')

    def OnPropGridRightClick(self, event):
        pass

    def OnProjectionChange(self, projection_value):
        for p in self.pp_list:
            self.pg.DeleteProperty(p)
        self.pp_list = []
        projection_key = revlookup(PROJECTIONS, 'name', projection_value)
        for param in PROJECTION_PARAMS[projection_key].keys():
            option = OPTIONS[param]
            self.pp_list.append(self.pg.AppendIn(self.pp, option['type'](
                option['name'],
                value=PROJECTION_PARAMS[projection_key][param])))

    def OnUpdatePlotButtonEvent(self, event=None):
        if not event:
            self.plot({})
        else:
            self.plot(self.pg.GetPropertyValues(inc_attributes=True))
