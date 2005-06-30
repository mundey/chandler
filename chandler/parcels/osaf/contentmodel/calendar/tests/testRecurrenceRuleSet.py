"""
Unit tests for recurrence
"""

__revision__  = "$Revision: 5742 $"
__date__      = "$Date: 2005-06-23 09:21:54 -0700 (Thu, 23 Jun 2005) $"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os
from datetime import datetime, timedelta

import dateutil.rrule
from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU, WEEKLY
from osaf.contentmodel.calendar.Recurrence import \
     FrequencyEnum, RecurrenceRuleSet, RecurrenceRule, toDateUtil
import osaf.contentmodel.tests.TestContentModel as TestContentModel

class RecurrenceRuleTest(TestContentModel.ContentModelTestCase):
    """ Test Recurrence Content Model """

    def setUp(self):
        super(RecurrenceRuleTest,self).setUp()
        self.start = datetime(2005, 7, 4, 13) #1PM, July 4, 2005

        self.weekly = {'end'   : datetime(2005, 11, 14, 13),
                       'start' : self.start,
                       'count' : 20}
        
        self.monthly = {'end'   : datetime(2005, 11, 4, 13),
                       'start' : self.start,
                       'count' : 5}
        
    def _testRRule(self, freq, rrule):
        """Create a simple rrule, make sure it behaves as we expect."""
        self.assertEqual(rrule[0], getattr(self, freq)['start'])
        self.assertEqual(rrule[-1], getattr(self, freq)['end'])
        self.assertEqual(rrule.count(), getattr(self, freq)['count'])

    def _createBasicItem(self, freq):
        ruleItem = RecurrenceRule(None, view=self.rep.view)
        ruleItem.until = getattr(self, freq)['end']
        if freq == 'weekly':
            self.assertEqual(ruleItem.freq, 'weekly', 
                             "freq should default to weekly")
        else:
            ruleItem.freq = freq
        return ruleItem
    
    def _createBasicDateUtil(self, freq):
        return dateutil.rrule.rrule(toDateUtil(freq),
                                    count   = getattr(self, freq)['count'],
                                    dtstart = getattr(self, freq)['start'])

    def testDateUtilRRules(self):
        for freq in 'weekly', 'monthly':
            self._testRRule(freq, self._createBasicDateUtil(freq))
        
    def testFrequencyEnum(self):
        freqItem = FrequencyEnum()
        self.assert_('yearly' in freqItem.values)
        self.failIf('bicentenially' in freqItem.values)
    
    def testRuleItem(self):
        """Test that transformations of RecurrenceRules work."""
        ruleItem = self._createBasicItem('weekly')
        rrule = ruleItem.createDateUtilFromRule(self.weekly['start'])
        self._testRRule('weekly', rrule)
        self.rep.check()
        
        # Every other week on Tuesday and Thursday, for 4 occurrences.
        complexRule = dateutil.rrule.rrule(WEEKLY, interval=2, count=4, wkst=SU,
                                           byweekday=(TU,TH),dtstart=self.start)
        lastDate = datetime(2005, 7, 21, 13)

        # Note that dtstart is a Monday and is NOT included, which is not RFC
        # compliant.  VObject works around this for now, someday dateutil will
        # provide an RFC compliant mode, hopefully.
        self.assertNotEqual(complexRule[0], self.start)
        self.assertEqual(complexRule[-1], lastDate)
        
        ruleItem.setRuleFromDateUtil(complexRule)
        
        # make sure isCount was stored and until was set properly
        self.assert_(ruleItem.isCount)
        self.assertEqual(ruleItem.until, lastDate)

        # make sure setRuleFromDateUtil(rrule).createDateUtilFromRule(dtstart)
        # represents the same dates as rrule
        identityTransformedRule = ruleItem.createDateUtilFromRule(self.start)
        
        # make sure the transform sets count, not until, since isCount==True
        self.assertEqual(identityTransformedRule._until, None)
        self.assertEqual(identityTransformedRule._count, 4)

        # compare datetimes for original rule and identityTransformedRule
        self.assertEqual(list(identityTransformedRule),
                         list(complexRule))
                         
    def testInfiniteRuleItem(self):
        """Test that infinite RecurrenceRules work."""
        ruleItem = RecurrenceRule(None, view=self.rep.view)
        #default frequency is weekly
        rule = ruleItem.createDateUtilFromRule(self.start)
        self.assertEqual(rule[149], datetime(2008, 5, 12, 13))
        
    def testTwoRuleSet(self):
        """Test two RecurrenceRules composed into a RuleSet."""
        ruleSetItem = RecurrenceRuleSet(None, view=self.rep.view)
        ruleItem = self._createBasicItem('weekly')
        ruleSetItem.addRule(ruleItem)
        ruleSet = ruleSetItem.createDateUtilFromRule(self.weekly['start'])
        
        #rrulesets support the rrule interface
        self._testRRule('weekly', ruleSet)
        
        ruleItem = self._createBasicItem('monthly')
        ruleSetItem.addRule(ruleItem)
        ruleSet = ruleSetItem.createDateUtilFromRule(self.monthly['start'])
        
        #not 25, or count1 + count2, because the two rules share self.start
        self.assertEqual(ruleSet.count(), 24)
        self.assertEqual(ruleSet[-1], self.weekly['end'])

    def testRuleSetFromDateUtil(self):
        ruleSet = dateutil.rrule.rruleset()
        for freq in 'weekly', 'monthly':
            ruleSet.rrule(self._createBasicDateUtil(freq))
        ruleSetItem = RecurrenceRuleSet(None, view=self.rep.view)
        ruleSetItem.setRuleFromDateUtil(ruleSet)

    def testExRule(self):
        pass
    
    def testRDate(self):
        pass


#tests to write:
"""

factor out testCombined
createDateUtil inverse for ruleset

Check behavior when bad enums are set

test multiple RRULEs in one rruleset

setRuleFromDateUtil(rruleset)
"""