__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os
import application.Globals
import wx

# A helper method and class for allowing the user to modify an item's attributes

def promptForItemValues(frame, title, item, attrList):
    """ Given an item and a list of attributes, display a modal dialog with
        a text field per attribute, with each field populated directly from
        the item's attribute values.  If the user OK's the dialog, the new
        values are applied to the item's attributes.

        @param frame: A wx parent frame
        @type frame: wx frame
        @param title: The title string for the dialog
        @type title: String
        @param item:  A chandler item
        @type item:  Item
        @param attrList: A list of dictionaries, each one having the following
         keys::

            "attr": an attribute name
            "label": a label to display for the field
            "password": an optional key, set to True if you want this field to be displayed like a password (with asterisks)

    """
    win = ItemValuesDialog(frame, -1, title, item, attrList)
    win.CenterOnScreen()
    val = win.ShowModal()

    if val == wx.ID_OK:
        # Assign the new values
        win.AssignNewValues()

    win.Destroy()
    return val == wx.ID_OK

class ItemValuesDialog(wx.Dialog):
    def __init__(self, parent, ID, title, item, attrList, size=wx.DefaultSize,
     pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(parent, ID, title, pos, size, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        textControls = []
        for valueDict in attrList:
            box = wx.BoxSizer(wx.HORIZONTAL)

            label = wx.StaticText(self, -1, valueDict["label"])
            box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

            if valueDict.get("password", False):
                text = wx.TextCtrl(self, -1,
                 item.getAttributeValue(valueDict["attr"]),
                 wx.DefaultPosition, [400,-1], wx.TE_PASSWORD)
            else:
                text = wx.TextCtrl(self, -1,
                 item.getAttributeValue(valueDict["attr"]),
                 wx.DefaultPosition, [400,-1])
            box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

            sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
            textControls.append(text)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        btn = wx.Button(self, wx.ID_OK, " OK ")
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, wx.ID_CANCEL, " Cancel ")
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        # Store these, using attribute names that hopefully wont collide with
        # any wx attributes
        self.chandlerTextControls = textControls
        self.chandlerItem = item
        self.chandlerAttrs = attrList

    def AssignNewValues(self):
        i = 0
        for (valueDict) in self.chandlerAttrs:
            self.chandlerItem.setAttributeValue(valueDict["attr"],
             self.chandlerTextControls[i].GetValue())
            i += 1


# A simple "prompt-the-user-for-a-string" dialog

def promptUser(frame, title, message, value):
    """ Prompt the user to enter in a string.  Return None if cancel is hit.

        @param frame: A wx parent frame
        @type frame: wx frame
        @param title: The title string for the dialog
        @type title: String
        @param message:  A message prompting the user for input
        @type item:  String
        @param value:  A value to populate the text field with
        @type item:  String

    """
    win = promptUserDialog(frame, -1, title, message, value)
    win.CenterOnScreen()
    val = win.ShowModal()

    if val == wx.ID_OK:
        # Assign the new values
        value = win.GetValue()
    else:
        value = None

    win.Destroy()
    return value

class promptUserDialog(wx.Dialog):
    def __init__(self, parent, ID, title, message, value, isPassword=False,
     size=wx.DefaultSize, pos=wx.DefaultPosition,
     style=wx.DEFAULT_DIALOG_STYLE):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(parent, ID, title, pos, size, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, -1, message)
        sizer.Add(label, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        if isPassword:
            text = wx.TextCtrl(self, -1, value, wx.DefaultPosition, [500,-1],
             wx.TE_PASSWORD)
        else:
            text = wx.TextCtrl(self, -1, value, wx.DefaultPosition, [500,-1])

        box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        # sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        btn = wx.Button(self, wx.ID_OK, " OK ")
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, wx.ID_CANCEL, " Cancel ")
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        # Store these, using attribute names that hopefully wont collide with
        # any wx attributes
        self.textControl = text

    def GetValue(self):
        return self.textControl.GetValue()



# A simple "ok/cancel" dialog

def okCancel(parent, caption, message):
    """ Prompt the user with a Ok/Cancel dialog.  Return True if Ok,
        False if Cancel.
        @param parent: A wx parent
        @type frame: wx frame
        @param caption: The caption string for the dialog
        @type caption: String
        @param message:  A message prompting the user for input
        @type item:  String
    """

    dlg = wx.MessageDialog(parent, message, caption, 
     wx.OK | wx.CANCEL | wx.ICON_QUESTION)
    val = dlg.ShowModal()

    if val == wx.ID_OK:
        value = True
    else:
        value = False

    dlg.Destroy()
    return value



# A simple "yes/no" dialog

def yesNo(parent, caption, message):
    """ Prompt the user with a Yes/No dialog.  Return True if Yes, False if No.
        @param parent: A wx parent
        @type frame: wx frame
        @param caption: The caption string for the dialog
        @type caption: String
        @param message:  A message prompting the user for input
        @type item:  String
    """

    dlg = wx.MessageDialog(parent, message, caption, 
     wx.YES_NO | wx.ICON_QUESTION)
    val = dlg.ShowModal()

    if val == wx.ID_YES:
        value = True
    else:
        value = False

    dlg.Destroy()
    return value



# A simple alert dialog

def ok(parent, caption, message):
    """ Display a message dialog with an OK button
        @param parent: A wx parent
        @type frame: wx frame
        @param caption: The caption string for the dialog
        @type caption: String
        @param message:  A message
        @type item:  String
    """

    dlg = wx.MessageDialog(parent, message, caption,
     wx.OK | wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()
