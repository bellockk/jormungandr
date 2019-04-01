import wx
import wx.adv
import os
import sys
import yaml

from wx.lib.wordwrap import wordwrap

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, SCRIPT_PATH)

from plot_panel import PlotPanel
from propertygrid_panel import PropertyGridPanel
from splash import Splash

MEDIA_PATH = os.path.join(os.path.dirname(
    os.path.dirname(SCRIPT_PATH)), 'media')
ID_FILE_LOAD = wx.ID_ANY
ID_FILE_SAVE = wx.ID_ANY
ID_HELP_ABOUT = wx.ID_ANY


class MainFrame(wx.Frame):
    def __init__(self, parent, title):

        wx.Frame.__init__(self, parent, title=title, size=(1200, 600))

        self.splash = Splash(
            os.path.normpath(os.path.join(MEDIA_PATH, "Jormungandr.jpg")),
            parent=self)

        # Icon
        _icon = wx.NullIcon
        _icon.CopyFromBitmap(wx.Bitmap(os.path.normpath(os.path.join(
            MEDIA_PATH, "icon.png")), wx.BITMAP_TYPE_ANY))
        self.SetIcon(_icon)

        # Status Bar
        self.statusbar = self.CreateStatusBar()

        # Menu Bar
        self.frame_1_menubar = wx.MenuBar()

        # File menu
        wxglade_tmp_menu = wx.Menu()
        ID_FILE_OPEN = wxglade_tmp_menu.Append(
            wx.ID_ANY, "&Open\tCTRL+O", "Open a previous session",
            wx.ITEM_NORMAL).GetId()
        ID_FILE_SAVE = wxglade_tmp_menu.Append(
            wx.ID_ANY, "&Save\tCTRL+S", "Save this session",
            wx.ITEM_NORMAL).GetId()
        ID_FILE_SAVEAS = wxglade_tmp_menu.Append(
            wx.ID_ANY, "Save &As\tALT+SHIFT+S", "Save this session as...",
            wx.ITEM_NORMAL).GetId()
        ID_FILE_QUIT = wxglade_tmp_menu.Append(
            wx.ID_ANY, "&Quit\tCTRL+Q", "Quit this session",
            wx.ITEM_NORMAL).GetId()
        self.frame_1_menubar.Append(wxglade_tmp_menu, "&File")

        # Help menu
        wxglade_tmp_menu = wx.Menu()
        ID_HELP_ABOUT = wxglade_tmp_menu.Append(wx.ID_ANY, "&About",
                                                "Display about dialog",
                                                wx.ITEM_NORMAL).GetId()
        self.frame_1_menubar.Append(wxglade_tmp_menu, "&Help")
        self.SetMenuBar(self.frame_1_menubar)

        # Splitter Window
        self.sp = wx.SplitterWindow(self, style=wx.SUNKEN_BORDER)
        self.p2 = PlotPanel(self.sp, self.statusbar)
        self.p1 = PropertyGridPanel(self.sp, self.p2.updatePlot)
        self.sp.SplitVertically(self.p1, self.p2, 400)

        # Event Bindings
        self.Bind(wx.EVT_MENU, self.OnOpen, id=ID_FILE_OPEN)
        self.Bind(wx.EVT_MENU, self.OnSave, id=ID_FILE_SAVE)
        self.Bind(wx.EVT_MENU, self.OnSaveAs, id=ID_FILE_SAVEAS)
        self.Bind(wx.EVT_MENU, self.OnExit, id=ID_FILE_QUIT)
        self.Bind(wx.EVT_MENU, self.OnAbout, id=ID_HELP_ABOUT)

        # Open Menu Wildcard
        self.wildcard = "GUI Save File (*.map)|*.map"

        # Current Working File
        self.working_file = None

        # update the plot
        self.p2.plot(self.p1.pg.GetPropertyValues())

        # Set Statusbar text
        self.statusbar.SetStatusText('Ready')

    def OnOpen(self, event):
        dlg = wx.FileDialog(self,
                            message="Choose a file",
                            defaultDir=os.getcwd(),
                            defaultFile="",
                            wildcard=self.wildcard,
                            style=wx.OPEN)

        # Show the dialog and retrieve the user response.  If it is the OK
        # response, process the data.
        if dlg.ShowModal() == wx.ID_OK:
            # This returns a Python list of files that were selected.
            try:
                with open(dlg.GetPath()) as f:
                    yaml.full_load(f)

                # Reset Appended Data Objects and create placeholders as needed

                # Set Properties
                for key, value in d.iteritems():
                    self.p1.pg.SetPropertyValue(RUN_DATA[key]['pgid'], value)
                # TODO: This should work, but is not...
                # self.p1.pg.SetPropertyValues(obj)
            except:
                dlg = wx.MessageDialog(self,
                                       'Unable to load input file.',
                                       'Error',
                                       wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
        # Destroy the dialog.  Do not do this until you are done with it!  BAD
        # things can happen otherwise!
        dlg.Destroy()
        # TODO: Update Plot...

    def OnSave(self, event=None):
        if not self.working_file:
            self.OnSaveAs()

        # Save Data
        data = self.p1.pg.GetPropertyValues()
        with open(self.working_file, 'w') as f:
            f.write(yaml.safe_dump(data, default_flow_style=False))

    def OnSaveAs(self, event=None):
        dlg = wx.FileDialog(
            self, message="Save file as ...",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard=self.wildcard,
            style=wx.SAVE | wx.OVERWRITE_PROMPT)

        # This sets the default filter that the user will initially see.
        # Otherwise, the first filter in the list will be used by default.
        dlg.SetFilterIndex(0)

        # Show the dialog and retrieve the user response.  If it is the OK
        # response, process the data.
        if dlg.ShowModal() == wx.ID_OK:
            # data = self.p1.pg.GetPropertyValues(inc_attributes=True)
            self.working_file = dlg.GetPath()
            self.OnSave()

        # Destroy the dialog.  Do not do this until you are donw ith it!  BAD
        # things can happen otherwise!
        dlg.Destroy()

    def OnExit(self, event):
        self.Close()

    def OnAbout(self, event):

        # First we create and fill the info object
        info = wx.adv.AboutDialogInfo()
        info.Name = "Map GUI"
        info.Version = "1.2.3"
        info.Copyright = "(C) 2016 Systems Engineering Group (SEG)"
        info.Description = wordwrap(
            "A \"hello world\" program is a software program that prints out "
            "\"Hello world!\" on a display device. It is used in many "
            "introductory "
            "tutorials for teaching a programming language."
            "\n\nSuch a program is typically one of the simplest programs "
            "possible "
            "in a computer language. A \"hello world\" program can be a "
            "useful "
            "sanity test to make sure that a language's compiler, development "
            "environment, and run-time environment are correctly installed.",
            350, wx.ClientDC(self))
        info.WebSite = ("https://www.example.com")
        info.Developers = ["Kenneth E. Bellock"]
        licenseText = "blah " * 250 + "\n\n" + "yadda " * 100
        info.License = wordwrap(licenseText, 500, wx.ClientDC(self))

        # Then we call wx.AboutBox giving it that info object
        wx.adv.AboutBox(info)
