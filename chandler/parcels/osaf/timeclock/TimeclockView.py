__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

"""
Timeclock's main purpose is to be an example of a simple parcel.
As such, it is not intended to be The Perfect Industrial-Strength
Timeclock.  It demonstrates simple buttons, radio buttons,
text entry boxes, simple menu items (in both the parcel menu
and the Help menu), and multi-level menu items.  It also shows
how to connect a parcel to the Chandler framework and how
to connect XRC widgets to event handlers.
"""

# @@@ To Be Done eventually, maybe, when we get around to it: 
# @@@ Show elapsed time clock 
# @@@ Dynamically add and remove customers 
# @@@ Persist the customer data
# @@@ Use customers from the Contacts list
# @@@ Make start time not reset when leaving and re-entering the parcel

from application.ViewerParcel import *
from application.SplashScreen import SplashScreen
from persistence.list import PersistentList
from time import *
from OSAF.timeclock.CustomerModel import *

"""
Chandler uses a model-view-controller (MVC) way of splitting up 
responsibilities between classes.  TimeclockView is the model, wxTimeclockView 
(in conjunction with TimeclockView.xrc) is the View, and Application is 
the controller.
"""
class TimeclockView(ViewerParcel):
    def __init__(self):
        """
        displayName is the name of the parcel as displayed in the Sidebar
        customerSelection remembers which customer is selected in radioBox
        startTime is the (most recent) time that the startTime button was 
                pushed
        customerList is the list of customers
        """
        ViewerParcel.__init__ (self)
        self.displayName = _('Timeclock')
        self.currencyName = "dollars"
        self.startTime = 0
        self.InitializeCustomerList()

    def InitializeCustomerList(self):
        self.customerSelection = 0        
        """
        If I make customerList a normal python list, the first version
        would get into the repository, but I wouldn't ever be able to
        append to the list.  Worse, if I later changed customerList from
        a normal list to a PersistentList, I would need to change 
        VERSION in applications/Application.py -- which would invalidate
        any previous data stored in Chandler.  Note that it's *only* variables
        that are in *this* class that need to be persistent.  For example,
        variables in CustomerModel.py do not need to persist.
        """
        self.customerList = PersistentList()
        """
        Yes, yes, I know that hardcoding the customer list is bad bad bad.
        Remember that this is, more than anything else, a *demo*.
        """
        self.customerList.append(CustomerModel("Floss Recycling Incorporated", billingRate=20.778))
        self.customerList.append(CustomerModel("Northside Cowbell Foundry Corp.", billingRate=31))
        self.customerList.append(CustomerModel("Cuneiform Designs, Ltd.", billingRate=17))
        self.currentCustomer = self.customerList[0]

            
"""
The initialization of wxTimeclockView wires up the View to events; the other
methods handle those events.  (There are also two little "helper" methods.)
"""
class wxTimeclockView(wxViewerParcel):
    def OnInit(self):
        """
          General initialization goes here, e.g. wiring up menus, etc.
        """
        self.radioBox = self.FindWindowById(XRCID('CustomerBox'))
        self.radioBox.SetSelection(self.model.customerSelection)
        # Set the rate default to the rate for the current customer
        self.rateTextDisplay = XRCCTRL(self, "ChangeRateText")
        self.rateTextDisplay.AppendText(str(self.CurrentCustomer().GetBillingRate()))
        self.rateTextDisplay.SetInsertionPoint(0)
        self.currencyPerHourTextDisplay = XRCCTRL(self, "CurrencyPerHourLabel")
        assert(self.radioBox != None)
        
        # Events generated by the buttons
        EVT_BUTTON(self, XRCID('StartClockButton'), self.OnStartClock)
        EVT_BUTTON(self, XRCID('StopClockButton'), self.OnStopClock)
        EVT_BUTTON(self, XRCID('SeeBillableHoursButton'), self.OnSeeBillableHours)
        EVT_BUTTON(self, XRCID('SeeBillableAmountButton'), self.OnSeeBillableAmount)
        EVT_BUTTON(self, XRCID('ChangeRateButton'), self.OnChangeRate)

        # Event generated by hitting Enter after some text
        EVT_TEXT_ENTER(self, XRCID('ChangeRateText'), self.OnChangeRate)

        # Events generated from the parcel-specific menu items
        EVT_MENU(self, XRCID('SwitchToPoundsMenuItem'), self.OnSwitchToPounds)
        EVT_MENU(self, XRCID('SwitchToMarksMenuItem'), self.OnSwitchToMarks)
        EVT_MENU(self, XRCID('SwitchToPesosMenuItem'), self.OnSwitchToPesos)
        EVT_MENU(self, XRCID('SwitchToFrancsMenuItem'), self.OnSwitchToFrancs)
        EVT_MENU(self, XRCID('SwitchToYenMenuItem'), self.OnSwitchToYen)
        EVT_MENU(self, XRCID('SwitchToEurosMenuItem'), self.OnSwitchToEuros)
        EVT_MENU(self, XRCID('SwitchToBhatMenuItem'), self.OnSwitchToBhat)
        EVT_MENU(self, XRCID('SwitchToRinggitMenuItem'), self.OnSwitchToRinggit)
        EVT_MENU(self, XRCID('SwitchToDollarsMenuItem'), self.OnSwitchToDollars)
        EVT_MENU(self, XRCID('SeeBillableHoursMenu'), self.OnSeeBillableHours)
        EVT_MENU(self, XRCID('SeeBillableAmountMenu'), self.OnSeeBillableAmount)

        # Events generated from the Help menu
        EVT_MENU(self, XRCID('AboutTimeclockMenuItem'), self.OnAboutTimeclock)

        # Events generated from the radio buttons
        EVT_RADIOBOX(self, XRCID('CustomerBox'), self.OnSwitchCustomer)

    # Note that there is a different CurrentCustomer for the View than for the Model:
    # The currentCustomer for the Model is whichever customer was selected
    # when the start button was pressed.
    def CurrentCustomer(self):
        return self.model.customerList[self.radioBox.GetSelection()]

    def OnStartClock(self, event):
        self.model.startTime = time()

        # Even if the customer is changed after Start is pressed, it should
        # count that time towards the customer that was chosen when Start was pressed.
        self.model.currentCustomer = self.CurrentCustomer()


    def OnStopClock(self, event):
        elapsedTime = time() - self.model.startTime
        # Here is a point where the *model's* idea of currentCustomer is used,
        # *not* the View's idea of current customer.
        currentCustomer = self.model.currentCustomer
        if self.model.startTime == 0:
            wxMessageBox(_("I can't tell you how much time has elapsed unless you tell me when to start.  Please press the 'Start Clock' button."))
        else:
            # convert seconds into hours
            currentCustomer.AddBillableHours(elapsedTime/3600)
            wxMessageBox(_("%0.1f" % elapsedTime + _(" seconds billed to ") + currentCustomer.name))
            # clear the clock
            self.model.startTime = 0

    def OnSeeBillableHours(self, event):
        currentCustomer = self.CurrentCustomer()
        billableHours = currentCustomer.GetBillableHours()
        # wxMessageBox(_("%0.1f" % billableHours + " hours billable to " + currentCustomer.name))
        wxMessageBox(_("%0.1f" % (billableHours*3600) + _(" seconds billable to ") + currentCustomer.name))

    def OnSeeBillableAmount(self, event):
        currentCustomer = self.CurrentCustomer()
        billableAmount = currentCustomer.GetBillableHours() * currentCustomer.GetBillingRate()
        wxMessageBox(_("%0.9f" % billableAmount + " " + self.model.currencyName + _(" billable to ") + currentCustomer.name))

    # Switching currency only changes how the billing rates and
    # accumulated amounts are displayed, nothing else.  This
    # little parcel is NOT a currency converter!
    def SwitchToNewCurrency(self, currencyName):
        self.model.currencyName = currencyName
        self.currencyPerHourTextDisplay.SetLabel(currencyName + _(" per hour"))

    # Note that these strings are *not* localized because they
    # *are* a form of localization.  
    def OnSwitchToPesos(self, event):
        self.SwitchToNewCurrency("Pesos")

    def OnSwitchToMarks(self, event):
        self.SwitchToNewCurrency("Marks")

    def OnSwitchToRinggit(self, event):
        self.SwitchToNewCurrency("Ringgit")

    def OnSwitchToBhat(self, event):
        self.SwitchToNewCurrency("Bhat")

    def OnSwitchToYen(self, event):
        self.SwitchToNewCurrency("Yen")

    def OnSwitchToEuros(self, event):
        self.SwitchToNewCurrency("euros")

    def OnSwitchToPounds(self, event):
        self.SwitchToNewCurrency("Pounds")

    def OnSwitchToDollars(self, event):
        self.SwitchToNewCurrency("dollars")

    def OnSwitchToFrancs(self, event):
        self.SwitchToNewCurrency("francs")

    # This routine changes the hourly billing rate for the currently 
    # selected customer.
    def OnChangeRate(self, event):
        box = self.FindWindowById(XRCID('ChangeRateText'))
        text = box.GetLineText(0)
        currentCustomer = self.model.customerList[self.radioBox.GetSelection()]
        try:
            currentCustomer.SetBillingRate(float(text))
        except ValueError:
            wxMessageBox(_("I don't know how to convert what you typed into a number.  Please enter a number."))

    """
    This routine changes the View's current customer but does NOT change
    the model's current customer.  The model's current customer
    should only change when the clock starts.
    """
    def OnSwitchCustomer(self, event):
        currentCustomer = self.CurrentCustomer()
        self.rateTextDisplay.Clear()
        self.rateTextDisplay.AppendText(str(currentCustomer.GetBillingRate()))
        self.rateTextDisplay.SetInsertionPoint(0)

    def OnAboutTimeclock(self, event):
        pageLocation = self.model.path + os.sep + "AboutTimeclock.html"
        infoPage = SplashScreen(self, _("About Timeclock"), pageLocation, false)
        if infoPage.ShowModal():
            infoPage.Destroy()

