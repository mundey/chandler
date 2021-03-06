__version__ = "$Revision: 6326 $"
__date__ = "$Date: 2005-08-02 00:00:02Z $"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

""" Provide Scripting Global Functions """

"""
  NOTE:
  ----
  All globals in this file become attributes of the user's script,
    unless the name starts with an underscore '_'.
  This includes things that you import here.
  Hence imports are done into the private name space.
"""
import wx as _wx
import logging as _logging
import osaf.framework.blocks.Block as _Block
import application.Globals as _Globals
from repository.item.Item import Item as _Item

_logger = _logging.getLogger(__name__)

"""
Named lookup of General Items
"""
def FindByName(itemClass, itemName):
    for item in itemClass.iterItems():
        if _itemName(item) == itemName:
            return item
    return None

def _itemName(item):
    try:
        return item.about
    except AttributeError:
        pass
    try:
        return item.blockName
    except AttributeError:
        pass
    try:
        return item.displayName
    except AttributeError:
        pass
    try:
        return item.itsName
    except AttributeError:
        pass
    return None

"""
Block lookup by name must be handled specially, because
they come and go from view when they are rendered by CPIA
"""

# Functions that return a named block
def FindNamedBlock(blockName):
    block = _Block.Block.findBlockByName(blockName)
    if not block:
        _logger.warning("Can't find block named %s" % blockName)
    return block

def Sidebar():
    return FindNamedBlock("Sidebar")

def SummaryView():
    return FindNamedBlock("TableSummaryView")

def CalendarView():
    return FindNamedBlock("CalendarSummaryView")

def DetailView():
    return FindNamedBlock("DetailView")

def StartTime():
    # The Start time edit field of the Detail View
    return FindNamedBlock("EditCalendarStartTime")

def EndTime():
    # The End time edit field of the Detail View
    return FindNamedBlock("EditCalendarEndTime")

def DisplayName():
    # The Display name block of the Detail View
    return FindNamedBlock("HeadlineBlock")

def Location():
    # The Location block of the Detail View
    return FindNamedBlock("AECalendarLocation")

def StartDate():
    # The Start date edit field of the Detail View
    return FindNamedBlock("EditCalendarStartDate")

def EndDate():
    # The End date edit field of the Detail View
    return FindNamedBlock("EditCalendarEndDate")

def AllDay():
    # The Allday block of the Detail View
    return FindNamedBlock("EditAllDay")

"""
Special functions, including wxWidgets-related operations

All attributes in this file get added to the builtin module
for script execution, except for ones that start with "_".
"""
def Focus(block):
    # Set the input focus to the given block
    try:
        widget = block.widget
    except AttributeError:
        _logger.warning("Can't set focus to block %s" % block)
    else:
        widget.SetFocus()

def SidebarSelect(itemOrName):
    """ Select the item in the Sidebar """
    # can pass in an item or a name
    if isinstance(itemOrName, _Item):
        params = {'item':itemOrName}
    else:
        params = {'itemName':itemOrName}
    _Globals.mainViewRoot.postEventByName ('RequestSelectSidebarItem', params)
    Focus(Sidebar())

def SidebarAdd(itemCollection):
    """ Adds the given itemCollection to the sidebar """
    _Globals.mainViewRoot.postEventByName ( 'AddToSidebarWithoutCopying', {'items' : [itemCollection]} )

def SummaryViewSelect(item):
    # Tell the ActiveView to select our item
    _Globals.mainViewRoot.postEventByName ('SelectItemBroadcastInsideActiveView', {'item':item})
    Focus(SummaryView())

def StampAsMailMessage():
    PressStampButton('MailMessageButton')

def StampAsTask():
    PressStampButton('TaskStamp')

def StampAsCalendarEvent():
    PressStampButton('CalendarStamp')

def PressStampButton(buttonName):
    """ Press a Stamp button in the markup bar, by firing its event"""
    uiView = _wx.GetApp().UIRepositoryView
    for block in _Block.Block.iterItems(uiView):
        # Find the live button, by name, and make sure its parent is live too"""
        try:
            blockName = block.blockName
        except AttributeError:
            continue
        if blockName == buttonName:
            if hasattr(block, 'widget') and hasattr(block.dynamicParent, 'widget'):
                block.post(block.event, {})
                break

def ButtonPressed(toolBlockName):
    uiView = _wx.GetApp().UIRepositoryView
    for block in _Block.Block.iterItems(uiView):
        if getattr(block, 'blockName', None) == toolBlockName:
            if hasattr(block, 'widget'):
                toolbarWidget = getattr(block.dynamicParent, 'widget', None)
                if toolbarWidget is not None:
                    break
    else:
        return False
    return toolbarWidget.GetToolState(block.toolID) 

def GetWindow(label):
    """ Returns the window with the given label """
    return _wx.FindWindowByLabel(label)
    
def Type(string, ctrlFlag = False, altFlag = False, shiftFlag = False):
    """ Types the string into the current focused widget, returns True if successful """
    stringSuccess = True
    for char in string:
        try:
            keyPressMethod = _wx.Window_FindFocus().EmulateKeyPress
        except AttributeError:
            return False
        else:
            keyCode = ord(char)  # returns ASCII value of char
            keyPress = _wx.KeyEvent(_wx.wxEVT_KEY_DOWN)
            keyPress.m_keyCode = keyCode
            keyPress.m_shiftDown = char.isupper() or shiftFlag
            keyPress.m_controlDown = keyPress.m_metaDown = ctrlFlag
            keyPress.m_altDown = altFlag
            charSuccess = keyPressMethod(keyPress)
            stringSuccess = stringSuccess and charSuccess
    return stringSuccess

def LeftClick(block):
    """ Simulates a left mouse click on the block or widget """
    mouseEnter = _wx.MouseEvent(_wx.wxEVT_ENTER_WINDOW)
    mouseDown = _wx.MouseEvent(_wx.wxEVT_LEFT_DOWN)
    mouseDown.m_leftDown = True
    mouseUp = _wx.MouseEvent(_wx.wxEVT_LEFT_UP)
    mouseLeave = _wx.MouseEvent(_wx.wxEVT_LEAVE_WINDOW)
    try:
        widget =  block.widget
    except AttributeError:
        widget = block
    mouseEnter.SetEventObject(widget)
    mouseDown.SetEventObject(widget)
    mouseUp.SetEventObject(widget)
    mouseLeave.SetEventObject(widget)    
    widget.ProcessEvent(mouseEnter)
    widget.ProcessEvent(mouseDown)
    widget.ProcessEvent(mouseUp)
    widget.ProcessEvent(mouseLeave)
    _wx.GetApp().Yield()
    ev = _wx.IdleEvent()
    _wx.GetApp().ProcessEvent(ev)
     
"""
TO BE DONE
* Type(<string>) function to take the string and tell wx
    to act like the user typed it in.
    (Could add modifier flags using optional parameters)
* Look at Select(item) method on Block, for SummaryView,
    Sidebar, etc.  I think Table.GotoItem() method or something
    like that might work.
* RunScript(<script> | <scriptNameString>) - run a script
* Click(<location>) should be possible.
"""
