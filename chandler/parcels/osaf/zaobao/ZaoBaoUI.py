#!/usr/bin/env python
# generated by wxGlade 0.2 on Mon Feb 17 15:00:47 2003
"""This file contains the UI classes of the ZaoBao parcel. The 2 main classes are:
    wxZaoBaoIndexView: this is the index view of the parcel
    wxZaoBaoItemView: this is the content view representing the selected RSS feed
"""

__is_standalone__ = 0 #are we running this module as part of a stand-alone app or as a Chandler parcel?

#Standard Python modules
import webbrowser
import re
import threading
import time
import os

#wxPython modules
from wxPython.wx import *
from wxPython.lib.mixins.listctrl import *
from wxPython.html import *
#from wxPython.lib.dialogs import *

if __is_standalone__:
    import RSSData
    from Observable import Observable
    from wxScrolledEditDialog import scrolledEditDialog
    from wxPython.lib.dialogs import *
else:    
    #Chandler modules
    from application.ViewerParcel import *
    from application.model.LocalRepository import LocalRepository
    
    #ZaoBao modules
    from OSAF.zaobao import RSSData
    from OSAF.zaobao.wxScrolledEditDialog import scrolledEditDialog
    from OSAF.zaobao.Observable import Observable1
    from OSAF.zaobao.dialogs import *

def getChangedStatus(data):
    """function used by list control to display if this feed has been read or not.
    Could also make it a anonymous lambda function
    """
    if data.hasNewItems(): return __is_standalone__ and unichr(0x25CF) or '*' # @@@ Chandler doesn't coerce unicode to text?!
    else: return ''
    
class wxZaoBaoIndexView(wxListCtrl, wxListCtrlAutoWidthMixin, wxColumnSorterMixin, Observable1):
    """This is the index view of all the subscribed RSS channels
    """
    
    """_columnInfo contains meta data about the columns of the index view. It's hard-
    coded for now, but in the future, we can easily change it to be created on the fly
    or to be stored.
    'name' is the string name of the column
    'stringFunc' specifies a function to get string data for each column of the indexView
    'sorterFunc' specifies a sort function each column of the indexView
    """
    _columnInfo = {0:{'name':'*' , # @@@ Chandler doesn't coerce unicode to text?!
                        'stringFunc':getChangedStatus,
                        'sorterFunc':getChangedStatus,
                        'defaultWidth':10,
                        'sortFlag':0},
                    1:{'name':'Channel',
                        'stringFunc':RSSData.RSSData.getTitle,
                        'sorterFunc':RSSData.RSSData.getTitle,
                        'defaultWidth':125,
                        'sortFlag':1},
                    2:{'name':'Creator',
                        'stringFunc':RSSData.RSSData.getCreator,
                        'sorterFunc':RSSData.RSSData.getCreator,
                        'defaultWidth':100,
                        'sortFlag':1},
                    3:{'name':'Modified Date',
                        'stringFunc':RSSData.RSSData.getModifiedDateString,
                        'sorterFunc':RSSData.RSSData.getModifiedDate,
                        'defaultWidth':75,
                        'sortFlag':0}}
                        
    def __init__(self, parent, ID, pos=wxDefaultPosition,
                 size=wxDefaultSize, style=0):
        wxListCtrl.__init__(self, parent, ID, pos, size, style)
        wxListCtrlAutoWidthMixin.__init__(self)
        EVT_LIST_COL_CLICK(self, ID, self.OnColClick) # MUST BE called before ColumnSorterMixin.__init__
        wxColumnSorterMixin.__init__(self,len(self._columnInfo))
        Observable1.__init__(self)
        self._colSortFlag[0] = 1 #read status defaults to sorting in descending order
        self._colSortFlag[3] = 1 #modified date defaults to sorting in descending order
        
        self.SetSizeHints(50,50)
        self.itemView = None
        EVT_LIST_ITEM_SELECTED(self,ID, self.onSelected)
        EVT_LIST_ITEM_ACTIVATED(self,ID,self.onActivated)
        EVT_RIGHT_DOWN(self, self.onRightDown)
        # for wxMSW
        EVT_COMMAND_RIGHT_CLICK(self, ID, self.onRightClick)
        # for wxGTK
        EVT_RIGHT_UP(self, self.onRightClick)
        EVT_KEY_UP(self, self.onDeleteKey)
        
        for (index,colInfo) in self._columnInfo.items():
            self.InsertColumn(index,colInfo['name'])
        self.rssDict = {}
        self.remoteAddress = None
        self.remoteLoadInProgress = false
        #self.populateFeeds()
    
    def GetListCtrl(self):
        # required by wxColumnSorterMixin
        return self
    
    def GetColumnSorter(self):
        # required by wxColumnSorterMixin
        return self.columnSorter
    
    def OnColClick(self, evt):
        oldCol = self._col
        self._col = col = evt.GetColumn()
        if (oldCol == col):
            self._colSortFlag[col] = not self._colSortFlag[col]
        self.SortItems(self.GetColumnSorter())
        #self.__updateImages(oldCol)
        evt.Skip()
    
    def columnSorter(self, key1, key2):
        """use for sorting the list by wxColumnSorterMixin"""
        col = self._col
        ascending = self._colSortFlag[col]
        data1 = self.getRSSDataFromKey(key1)
        data2 = self.getRSSDataFromKey(key2)
        item1 = self._columnInfo[col]['sorterFunc'](data1)
        item2 = self._columnInfo[col]['sorterFunc'](data2)

        cmpVal = cmp(item1, item2)

        # If the items are equal then pick modified date as secondary sort key
        if cmpVal == 0:
            cmpVal = cmp(data1.getModifiedDate(), data2.getModifiedDate())

        if ascending:
            return cmpVal
        else:
            return -cmpVal
    
    def setReadStatus(self,row, readStatus):
        """ a row is set to bold if it has new RSS feeds that has not been read yet."""
        anItem = self.GetItem(row)
        if readStatus: weight = wxBOLD
        else: weight = wxNORMAL
        font = wxSWISS_FONT
        font.SetWeight(weight)
        anItem.SetFont(font)
        self.SetItem(anItem)
    
    def _updateRSSFeeds(self):
        for anRSSFeed in self.rssDict.values():
            #statusObservable.broadcast({'event':'Opening ' + anRSSFeed.getRSSURL()})
            anRSSFeed.update(0)
    
    def updateRSSFeeds(self):
       threading.Thread(target=self._updateRSSFeeds).start()
            
    def addRSS(self,data):
        """ adds a new RSS data feed to the List Control"""
        i = self.GetItemCount()
        for (col,colInfo) in self._columnInfo.items():
            if (col ==0):
                self.InsertStringItem(i,colInfo['stringFunc'](data))
            else:
                self.SetStringItem(i,col,colInfo['stringFunc'](data))
        self.SetItemData(i,id(data))
        self.setReadStatus(i,data.hasNewItems())
        data.register(self) 
        self.rssDict[id(data)] = data
     
    def loadObjects(self, remoteAddress, url):
        rssDict = self.rssDict = {}
        self.remoteAddress = remoteAddress
        if (remoteAddress):
            self.remoteLoadInProgress = app.jabberClient.RequestRemoteObjects(remoteAddress, url)
            if (not self.remoteLoadInProgress):
                wxMessageBox(_("Sorry, but %s is not present!") % remoteAddress)
        else:
            self.rssDict = RSSData.loadLocalObjects()
            self.populateFeeds()
            
    def populateFeeds(self):
        """ Populate the List Control with a set of RSS feeds"""
        for data in self.rssDict.values():
            self.addRSS(data)
        
        doAutoWidth = self.GetItemCount() > 0
        for (col,colInfo) in self._columnInfo.items():
            self.SetColumnWidth(col, doAutoWidth and wxLIST_AUTOSIZE or colInfo['defaultWidth'])
            self._colSortFlag[col] = colInfo['sortFlag']
    
    def deactivate(self):
        for anRSSFeed in self.rssDict.values():
            anRSSFeed.unregister(self)
            
    def alreadySubscribed(self, rssURL):
        """check to see if rss URL is already in list of subscribed URLs"""
        for anRSSFeed in self.rssDict.values():
            if anRSSFeed.getRSSURL() == rssURL: return 1
        return None
    
    def isLocal(self):
        return self.remoteAddress == None
    
    def getCurrentItem(self):
        return self.GetFirstSelected(-1)
    
    def deleteRSSDataFromKey(self, key):
        """Delete the corresponding RSSData object given a key"""
        if (self.isLocal()):
            repository = LocalRepository()
            assert (isinstance(self.rssDict[key],RSSData.RSSData))
            repository.deleteObject(self.rssDict[key])
            repository.commit()
        del self.rssDict[key]

    def getRSSDataFromKey(self, key):
        return self.rssDict[key]
    
    def getRSSDataFromIndex(self,index):
        """Given an row number, return the instance of RSSData associated with the row"""
        return self.getRSSDataFromKey(self.GetItemData(index))
        
    def getCurrentRSSData(self):
        """Return the instance of RSSData associated with the selected row"""
        index = self.getCurrentItem()
        if (index != -1):
            return self.getRSSDataFromIndex(self.getCurrentItem())
        return None
    
    def refreshIndex(self,index):
        """Refresh the display of the row in the indexView"""
        data = self.getRSSDataFromIndex(index)
        for (col,colInfo) in self._columnInfo.items():
            self.SetStringItem(index,col,colInfo['stringFunc'](data))
        self.setReadStatus(index,data.hasNewItems())
        
    def refreshKey(self,key):
        """Refresh the display of the row given a key stored in the ItemData field of
        indexView"""
        index = self.FindItemData(-1,key)
        self.refreshIndex(index)
    
    def selectKey(self,key):
        """Selects the item with the given key"""
        index = self.FindItemData(-1,key)
        self.SetItemState(index,wxLIST_STATE_SELECTED,wxLIST_STATE_SELECTED)
        
    def update(self, updateObj, args):
        """called by Observable, when underlying list item data (instance of RSSData)
        is updated (changed)"""
        if isinstance(updateObj, RSSData.RSSData):
            try:
                key = args['key']
                index = self.FindItemData(-1,key)
                self.refreshIndex(index)
                if (index == self.getCurrentItem()):
                    self.updateItemView()
                if self._col != -1: self.SortItems(self.GetColumnSorter())
            except KeyError, e:
                assert(0)
                print e
            
    def setItemView(self,anItemView):
        """ItemView is the HTML content view that reflects the content of an RSS feed
        of the selected list item"""
        self.itemView = anItemView
    
    def updateItemView(self):
        """Tell the ItemView to refresh its content based on the selected row"""
        inRightDown = hasattr(self,'inRightDown') and self.inRightDown
        if self.itemView and not inRightDown:
            data = self.getCurrentRSSData()
            if data:
                self.SetCursor(wxHOURGLASS_CURSOR)
                #print ('*** setting page ')
                self.itemView.SetData(data)
                #print ('completed setting page ')
                self.SetCursor(wxNullCursor)
            else:
                self.itemView.SetData(None)
        
    def onDeleteKey(self, event):
        if event.GetKeyCode() == WXK_DELETE:
            self.onDeleteItem(event)
        else: event.Skip()
        
    def onSelected(self,event):
        """A new row (RSS channel) has been selected"""
        self.broadcast(self.getCurrentRSSData())
        self.updateItemView()
        
    def onActivated(self, event):
        """Double-clicking opens the web site of the RSS feed on the default browser"""
        if self.itemView:
            currentItem = event.m_itemIndex
            data = self.getCurrentRSSData()
            if data:
                webbrowser.open(data.getSiteLink())
                data.setHasNewItems(0)
    
    def onRightDown(self, event):
        """record x,y coordinate of right click to show right click menu later"""
        self.x = event.GetX()
        self.y = event.GetY()
        self.inRightDown = true
        item, flags = self.HitTest((self.x, self.y))
        if flags & wxLIST_HITTEST_ONITEM:
            self.Select(item)
        event.Skip()
        
    def onActivated(self, event):
        """Double-clicking opens the web site of the RSS feed on the default browser"""
        if self.itemView:
            currentItem = event.m_itemIndex
            data = self.getCurrentRSSData()
            if data:
                webbrowser.open(data.getSiteLink())
                data.setHasNewItems(0)
    
    def deleteIndex(self, index):
        """Deletes the RSS feed represented by the index or row num"""
        key = self.GetItemData(index) # need to get key before it is deleted!
        if self.DeleteItem(index):
            self.deleteRSSDataFromKey(key)
            self.updateItemView()
            
    def onRightClick(self, event):
        """show right click context menu.
        There is a wxWindows bug that I've had to work around:
            if wxHTMLWindow.SetPage() is called with HTML code that loads an image,
            the right click handler cannot call wxHTMLWindow.SetPage(); otherwise,
            it results in an infinite loop
        The work-around is to have use a variable 'inRightDown' which is set to true
        until the right mouseup happens. When inRightDown is true, we make sure
        wxHTMLWindow.SetPage() is not called."""
        
        # only do this part the first time
        if not hasattr(self,'popupIDs'):
            self.popupIDs = [wxNewId() for i in range(3)]
            EVT_MENU(self, self.popupIDs[0], self.onMarkItem)
            EVT_MENU(self, self.popupIDs[1], self.onDeleteItem)
            EVT_MENU(self, self.popupIDs[2], self.onRefreshItem)

        data = self.getCurrentRSSData()
        if data:
            menu = wxMenu()
            menuName = _("Mark as ")
            if data.hasNewItems(): menuName += _("Read")
            else: menuName += _("Unread")
            menu.Append(self.popupIDs[0], menuName)
            menu.Append(self.popupIDs[1], _("Delete"))
            menu.Append(self.popupIDs[2], _("Refresh"))
            self.PopupMenu(menu, wxPoint(self.x,self.y))
            menu.Destroy()
            if self.inRightDown:
                self.inRightDown = false
                self.updateItemView()
            
    def onMarkItem(self, event):
        """Mark selected row as read or unread (toggle)"""
        self.inRightDown = false
        data = self.getCurrentRSSData()
        if data:
            data.setHasNewItems(not data.hasNewItems())
    
    def onDeleteItem(self, event):
        """Deletes selected row on confirmation"""
        currentItem = self.getCurrentItem()
        if currentItem != -1:
            self.inRightDown = false
            answer = wxMessageBox(_("Do you really want to delete this item?"),style=wxYES_NO)
            if (answer == wxYES):
                self.deleteIndex(currentItem)
            
    def onRefreshItem(self, event):
        """Pings RSS feed for new data"""
        self.inRightDown = false
        data = self.getCurrentRSSData()
        if data:
            data.update()
    
    def onCopyRSSURL(self, event):
        """Copies selected RSS feed URL to clipboard"""
        self.inRightDown = false
        data = self.getCurrentRSSData()
        if data:
            wxTheClipboard.SetData(wxTextDataObject(data.getRSSURL()))
        

class wxZaoBaoItemView(wxHtmlWindow):
    """This view shows the RSS items of the selected RSS channel in HTML
    format"""
    _regex = None
    _translationDict = {'<%title>':'title',
                        '<%description>':'description',
                        '<%itemLink>':'link'}
    _defaultItemHTML = "<b><%title> </b><%description> <a href='<%itemLink>'>More...</a><hr>"
    _defaultPageHTML = "<html><body><%items></body></html>"


    def loadTemplate(self, filename, silent=0):
        """Loads a template file for editing"""
        try:
            templateText = None
            templateFile = open(filename,'r')
            try:
                templateText = templateFile.read()
            finally:
                templateFile.close()
        except IOError, e:
            if not silent:
                messageDialog(message=_("Unable to read file '") + filename + "'\n" + e.strerror,
                              title=_("ZaoBao error"),aStyle = wx.wxOK)
        return templateText
    
    def saveTemplate(self, filename, templateText,silent=0):
        """Saves templateText back to filename"""
        try:
            templateFile = open(filename,'w')
            try:
                templateFile.write(templateText)
            finally:
                templateFile.close()
        except IOError, e:
            if not silent:
                messageDialog(message=_("Unable to write to file '") + filename + "'\n" + e.strerror,
                                title=_("ZaoBao error"),aStyle = wx.wxOK)
        
    def editTemplate(self, filename,defaultText):
        """Show dialog box to edit template text"""
        templateText = self.loadTemplate(filename)
        if (not templateText): templateText = defaultText
        result = scrolledEditDialog(message=templateText,title=_("Edit Template: ") + filename)
        if result: self.saveTemplate(filename, result)
        return result
    
    def editItemTemplate(self,path=''):
        result = self.editTemplate(path + 'ZaoBaoItem.html',self._defaultItemHTML)
        if (result):
            self._defaultItemHTML = result
            if (self.data): self.SetPage(self.getNewItemsHTML())
        
    def editPageTemplate(self,path=''):
        result = self.editTemplate(path + 'ZaoBaoPage.html',self._defaultPageHTML)
        if (result):
            self._defaultPageHTML = result
            if (self.data): self.SetPage(self.getNewItemsHTML())
        
    def subItemsForHTML(self,item,text):
        def translate(match):
            return item.get(self._translationDict[match.group(0)],'')
        
        return self._regex.sub(translate, text)

    def getNewItemsHTML(self):
        """returns the HTML text of the selected RSS channel using regex"""
        
        if (not self.data): return ''
        if (not self._regex):
            self._regex = re.compile("|".join(map(re.escape, self._translationDict.keys())))
            
        bodyHTML =  ''.join([self.subItemsForHTML(item,self._defaultItemHTML)
                            for item in self.data.getItems()])
        return re.sub('<%items>',bodyHTML,self._defaultPageHTML)

    def SetData(self, data):
        """Set the RSSData that this content view should represent"""
        if self.data != data:
            self.data = data
            self.SetPage(self.getNewItemsHTML())
        
    def __init__(self,parent,id,path=''):
        wxHtmlWindow.__init__(self,parent,id)
        self.data = None
        templateText = self.loadTemplate(path+'ZaoBaoItem.html',silent=1)
        if templateText: self._defaultItemHTML = templateText
        templateText= self.loadTemplate(path+'ZaoBaoPage.html',silent=1)
        if templateText: self._defaultPageHTML = templateText
        templateText = self.loadTemplate(path+'AboutZaoBao.html',silent=1)
        if not templateText: templateText = "<html><body>Hello, world!</body></html>"
        self.SetSizeHints(50,50)
        self.SetPage(templateText)
    
    def OnLinkClicked(self, linkinfo):
        webbrowser.open(linkinfo.GetHref())
        if (self.data): self.data.setHasNewItems(0)
