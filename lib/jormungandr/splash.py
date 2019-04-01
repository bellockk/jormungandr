import wx
import wx.lib.agw.advancedsplash as wxAS


class Splash(wxAS.AdvancedSplash):
    def __init__(self, pn, parent=None, display=True):

        # Splash Screen
        if display:
            bitmap = wx.Bitmap(pn, wx.BITMAP_TYPE_PNG)
            wxAS.AdvancedSplash.__init__(
                self, None, bitmap=bitmap, timeout=4000,
                agwStyle=wxAS.AS_TIMEOUT | wxAS.AS_CENTER_ON_PARENT)
            self.Show()
            wx.Yield()
