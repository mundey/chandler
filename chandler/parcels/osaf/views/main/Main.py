__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from osaf.framework.blocks.Views import View
from osaf.framework.notifications.Notification import Notification
import wx
import os
from application.SplashScreen import SplashScreen
from application.Parcel import Manager as ParcelManager

import osaf.framework.utils.imports.OutlookContacts as OutlookContacts
import osaf.contentmodel.tests.GenerateItems as GenerateItems

class MainView(View):
    """
      Main Chandler view contains event handlers for Chandler
    """
    def onQuitEvent (self, notification):
        Globals.wxApplication.mainFrame.Close ()
        
    def onUndoEventUpdateUI (self, notification):
        notification.data ['Text'] = "Can't Undo\tCtrl+Z"            
        notification.data ['Enable'] = False

    def onRedoEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def onCutEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def onCopyEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def onPasteEventUpdateUI (self, notification):
        notification.data ['Enable'] = False
        
    def onPreferencesEventUpdateUI (self, notification):
        notification.data ['Enable'] = False
        
    # Test Methods

    def onGenerateContentItemsEvent(self, notification):
        GenerateItems.GenerateNotes(5)
        GenerateItems.generateCalendarEventItems(5, 30)
        GenerateItems.GenerateContacts(5)
        Globals.repository.commit()

    def onGenerateCalendarEventItemsEvent(self, notification):
        GenerateItems.generateCalendarEventItems(10, 30)
        Globals.repository.commit()

    def onGenerateContactsEvent(self, notification):
        GenerateItems.GenerateContacts(10)
        Globals.repository.commit()

    def onImportContactsEvent(self, notification):
        x=OutlookContacts.OutlookContacts().processFile()

    def onGenerateNotesEvent(self, notification):
        GenerateItems.GenerateNotes(10)
        Globals.repository.commit()

    def onCheckRepositoryEvent(self, notification):

        repository = Globals.repository
        repository.logger.info('Checking repository...')
        if repository.check():
            repository.logger.info('Check completed successfully')
        else:
            repository.logger.info('Check completed with errors')

    def onShowPyCrustEvent(self, notification):
        Globals.wxApplication.ShowDebuggerWindow()

    def onReloadParcelsEvent(self, notification):
        ParcelManager.getManager().loadParcels()

    def onAddAllAdditionalViewsEvent(self, notification):
        self.onAddDemoViewEvent(notification)
        self.onAddRepositoryViewEvent(notification)
        self.onAddMixedViewEvent(notification)
        self.onAddStockQuoteEvent(notification)
        self.onAddKindViewsEvent(notification)
        
    def onAddDemoViewEvent(self, notification):
        self._addNewView('//parcels/osaf/views/demo/TabBox')

    def onAddRepositoryViewEvent(self, notification):
        self._addNewView('//parcels/osaf/views/repositoryviewer/RepositoryBox')

    def onAddMixedViewEvent(self, notification):
        self._addNewView('//parcels/osaf/views/content/MixedListView')

    def onAddStockQuoteEvent(self, notification):
        self._addNewView('//parcels/osaf/examples/stockquote/views/StockQuoteView')

    def onAddNoteViewEvent(self, notification):
        self._addNewView('//parcels/osaf/views/content/NoteListView')

    def onAddTaskViewEvent(self, notification):
        self._addNewView('//parcels/osaf/views/content/TaskListView')

    def onAddMailViewEvent(self, notification):
        self._addNewView('//parcels/osaf/views/content/MailListView')

    def onAddKindViewsEvent(self, notification):
        self.onAddNoteViewEvent(notification)
        self.onAddTaskViewEvent(notification)
        self.onAddMailViewEvent(notification)
        
    def _addNewView(self, path):
        sidebarCollection = Globals.repository.findPath('//parcels/osaf/views/main/sidebarItemCollection')
        newView = Globals.repository.findPath(path)
        sidebarCollection.include(newView)        
                
    def onAboutChandlerEvent(self, notification):
        """
          Show the splash screen in response to the about command
        """
        pageLocation = os.path.join ('application', 'welcome.html')
        splash = SplashScreen(None, _("About Chandler"), 
                              pageLocation, False, False)
        splash.Show(True)

