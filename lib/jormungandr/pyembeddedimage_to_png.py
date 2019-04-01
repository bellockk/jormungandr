import os
import tempfile
import wx
from matplotlib._png import read_png


def pyembeddedimage_to_png(img):
    f_handle, tf = tempfile.mkstemp()
    f_obj = os.fdopen(f_handle)
    f_obj.close()
    img.GetBitmap().SaveFile(tf, wx.BITMAP_TYPE_PNG)
    png = read_png(tf)
    os.remove(tf)
    return png
