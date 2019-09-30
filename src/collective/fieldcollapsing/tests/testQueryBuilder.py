# -*- coding: utf-8 -*-
from collective.fieldcollapsing.testing import \
    COLLECTIVE_FIELDCOLLAPSING_INTEGRATION_TESTING
from collective.fieldcollapsing.browser.querybuilder import QueryBuilder
from plone.app.querystring.querybuilder import QueryBuilder as BaseQueryBuilder
from zope.publisher.browser import TestRequest
import unittest


class TestQuerybuilder(unittest.TestCase):

    layer = COLLECTIVE_FIELDCOLLAPSING_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.num_folders = self.layer['num_folders']
        self.num_docs_in_folder = self.layer['num_docs_in_folder']
        self.total_num_docs = self.num_folders * self.num_docs_in_folder

        self.request = TestRequest()
        self.querybuilder = QueryBuilder(
            self.portal, self.request,

        )
        self.query = [{
            'i': 'portal_type',
            'o': 'plone.app.querystring.operation.selection.any',
            'v': ['Document']
        }]

    def testQueryBuilderHTML(self):
        self.request.form['sort_on'] = 'id'
        results = self.querybuilder.html_results(self.query)
        self.assertIn('Test Page 01-01', results)
        del self.request.form['sort_on']

    def testQueryBuilderNumberOfResults(self):
        results = self.querybuilder.number_of_results(self.query)
        numeric = int(results.split(' ')[0])
        self.assertEqual(numeric, 1)

    def testMakeQuery(self):
        results = self.querybuilder._makequery(
            query=self.query,
            sort_on="id"
        )
        self.assertEqual(len(results), self.total_num_docs)
        self.assertEqual(
            results[0].getURL(),
            'http://nohost/plone/testfolder-01/testpage-01-01')
        self.assertEqual(
            results[1].getURL(),
            'http://nohost/plone/testfolder-01/testpage-01-02')
        self.assertEqual(
            results[2].getURL(),
            'http://nohost/plone/testfolder-01/testpage-01-03')

    def testMakeQueryWithBrains(self):
        results = self.querybuilder._makequery(
            query=self.query,
            custom_query={"collapse_on": "__PARENT__"},
            brains=True,
            sort_on="created"
        )
        self.assertEqual(len(results), self.num_folders)
        self.assertEqual(
            results[0].getURL(),
            'http://nohost/plone/testfolder-01/testpage-01-01')
        self.assertEqual(
            results[1].getURL(),
            'http://nohost/plone/testfolder-02/testpage-02-01')
        self.assertEqual(
            results[2].getURL(),
            'http://nohost/plone/testfolder-03/testpage-03-01')
        self.assertEqual(
            results[14].getURL(),
            'http://nohost/plone/testfolder-15/testpage-15-01')

    def testMakeQueryWithBrainsMultiCollapse(self):
        results = self.querybuilder._makequery(
            query=self.query,
            custom_query={"collapse_on": ['Subject', "__PARENT__"]},
            brains=True,
            sort_on="created",
            b_size=5,
            batch=True,
        )
        self.assertEqual(len(results), 55)  # lazyfilter gueses the len
        self.assertEqual(
            results[0].getURL(),
            'http://nohost/plone/testfolder-01/testpage-01-01')
        self.assertEqual(
            results[1].getURL(),
            'http://nohost/plone/testfolder-02/testpage-02-01')
        self.assertEqual(
            results[2].getURL(),
            'http://nohost/plone/testfolder-03/testpage-03-01')

    def testBaseMakeQueryWithBrains(self):
        querybuilder = BaseQueryBuilder(self.portal, self.request)
        results = querybuilder._makequery(
            query=self.query,
            brains=True,
            sort_on="created"
        )
        self.assertEqual(len(results), self.total_num_docs)
        self.assertEqual(
            results[0].getURL(),
            'http://nohost/plone/testfolder-01/testpage-01-01')
        self.assertEqual(
            results[1].getURL(),
            'http://nohost/plone/testfolder-01/testpage-01-02')
        self.assertEqual(
            results[2].getURL(),
            'http://nohost/plone/testfolder-01/testpage-01-03')

    def testMakeQueryWithBatch(self):
        results = self.querybuilder._makequery(
            query=self.query,
            custom_query={"collapse_on": "__PARENT__"},
            batch=True,
            sort_on="created",
            b_size=5,
        )
        self.assertEqual(len(results), 55)  # lazyfilter guesses the len
        self.assertEqual(
            results[0].getURL(),
            'http://nohost/plone/testfolder-01/testpage-01-01')
        self.assertEqual(
            results[1].getURL(),
            'http://nohost/plone/testfolder-02/testpage-02-01')
        self.assertEqual(
            results[2].getURL(),
            'http://nohost/plone/testfolder-03/testpage-03-01')

    def testMakeQueryWithCollapseOn(self):
        results = self.querybuilder._makequery(
            query=self.query,
            sort_on="created"
        )
        self.assertEqual(len(results), self.total_num_docs)
        self.assertEqual(
            results[0].getURL(),
            'http://nohost/plone/testfolder-01/testpage-01-01')
        self.assertEqual(
            results[1].getURL(),
            'http://nohost/plone/testfolder-01/testpage-01-02')

        collasped_results = self.querybuilder._makequery(
            query=self.query,
            custom_query={"collapse_on": "__PARENT__"},
            sort_on="created",
            b_size=5,
            batch=True,
        )

        # Test the reported length of the collapsed results
        self.assertEqual(len(collasped_results), 55)  # lazyfilter guesses the len
        # Test the reported length of the collapsed results
        # aganist the actual length of the collapsed results
        self.assertNotEqual(
            len(list(collasped_results._sequence)),
            self.total_num_docs
        )
        # The actual length of the collapsed results should be 20 because
        # we created 20 folders and retrieve first document from each folder.
        self.assertEqual(
            len(list(collasped_results._sequence)),
            self.num_folders
        )

        self.assertEqual(
            collasped_results[0].getURL(),
            'http://nohost/plone/testfolder-01/testpage-01-01')
        self.assertEqual(
            collasped_results[1].getURL(),
            'http://nohost/plone/testfolder-02/testpage-02-01')
        self.assertEqual(
            collasped_results[2].getURL(),
            'http://nohost/plone/testfolder-03/testpage-03-01')

        # Test the 4th result item aganist the 4th collapsed result item.
        self.assertNotEqual(
            results[3].getURL(),
            collasped_results[3].getURL())

    def testMakeQueryWithCollapseOnSubject(self):
        query = [{
            'i': 'Subject',
            'o': 'plone.app.querystring.operation.selection.any',
            'v': 'Lorem',
        }]
        results = self.querybuilder._makequery(
            query=query,
            custom_query={"collapse_on": "Subject"},
            sort_on="created"
        )
        self.assertEqual(len(results[:]), self.num_folders)
        self.assertEqual(
            results[0].getURL(),
            'http://nohost/plone/testfolder-01/testpage-01-01')
        self.assertEqual(
            results[1].getURL(),
            'http://nohost/plone/testfolder-02/testpage-02-01')
        self.assertEqual(
            results[2].getURL(),
            'http://nohost/plone/testfolder-03/testpage-03-01')

    def testMakeQueryWithCollapseOnMultipleSubject(self):
        query = [{
            'i': 'Subject',
            'o': 'plone.app.querystring.operation.selection.any',
            'v': ['Lorem', 'Ipsum'],
        }]
        results = self.querybuilder._makequery(
            query=query,
            custom_query={"collapse_on": "Subject"},
            sort_on="created"
        )
        self.assertEqual(len(results[:]), self.num_folders)
        self.assertEqual(
            results[0].getURL(),
            'http://nohost/plone/testfolder-01/testpage-01-01')
        self.assertEqual(
            results[1].getURL(),
            'http://nohost/plone/testfolder-02/testpage-02-01')
        self.assertEqual(
            results[2].getURL(),
            'http://nohost/plone/testfolder-03/testpage-03-01')

    def testMergeKeywordIndex(self):
        """Example of keyword indexed stored as tuples which gets merge into more tupples"""

        # First lets show the data in there
        results = self.querybuilder._makequery(
            query=self.query,
            sort_on="created"
        )
        self.assertEqual(
            results[0].Subject(), ('Lorem', 'Folder 1'))

        for i, page in enumerate(results):
            if i % 2 == 1:
                page.getObject().setSubject(set())
            else:
                page.getObject().setSubject(('page {}'.format(i + 1),))
            page.getObject().reindexObject()

        collasped_results = self.querybuilder._makequery(
            query=self.query,
            custom_query={"collapse_on": "__PARENT__", "merge_fields": ["Subject"]},
            sort_on="created",
            b_size=5
        )

        # now when we look at subject to see if its merged
        self.assertEqual(
            collasped_results[0].Subject(), ('page 1', 'page 3', 'page 5'))
        self.assertEqual(
            collasped_results[1].Subject(), ('page 7', 'page 9'))

    def testMergeZCIndex(self):
        """ Example of textindex which gets merged by joining strings"""

        # First lets show the data in there
        results = self.querybuilder._makequery(
            query=self.query,
            sort_on="created"
        )
        self.assertEqual(
            results[0].Title(), 'Test Page 01-01')

        collasped_results = self.querybuilder._makequery(
            query=self.query,
            custom_query={"collapse_on": "__PARENT__", "merge_fields": ["Title"]},
            sort_on="created",
            b_size=5
        )

        # now when we look at subject to see if its merged
        self.assertEqual(
            collasped_results[0].Title(),
            'Test Page 01-01 Test Page 01-02 Test Page 01-03 Test Page 01-04 Test Page 01-05')

    def testMergeFieldIndex(self):
        """ Type is an example of field index which will get merged into a tuple """

        # Lets add in a some other types of content
        # test_folder = self.portal['testfolder-01']

        # id = test_folder.invokeFactory("Folder", 'testfolder-01-01', title="Test Folder 1")
        # news = test_folder[id]
        # self.portal.portal_workflow.doActionFor(news, 'publish')

        # First lets show the data in there
        results = self.querybuilder._makequery(
            query=self.query,
            sort_on="created",
            brains=True,
        )
        self.assertEqual(
            results[0].getId, 'testpage-01-01')

        collasped_results = self.querybuilder._makequery(
            query=self.query,
            custom_query={"collapse_on": "__PARENT__", "merge_fields": ["getId"]},
            sort_on="created",
            b_size=5,
            brains=True,
        )

        # now when we look at getid to see if its merged
        self.assertEqual(collasped_results[0].getId, ('testpage-01-01', 'testpage-01-02', 'testpage-01-03',
                                                      'testpage-01-04', 'testpage-01-05'))
        self.assertEqual(collasped_results[1].getId, ('testpage-02-01', 'testpage-02-02', 'testpage-02-03',
                                                      'testpage-02-04', 'testpage-02-05'))

    def testMergeIteration(self):
        """ Ensure we still merge if we iterate instead of use getitem """

        collasped_results = self.querybuilder._makequery(
            query=self.query,
            custom_query={"collapse_on": "__PARENT__", "merge_fields": ["getId"]},
            sort_on="created",
            b_size=5,
            batch=False,
            brains=True,
        )

        merged = [len(b.getId) for b in collasped_results]
        self.assertEqual(merged, [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5])

        # However if we do the same query with batch on then won't do the merge after the first batch
        collasped_results = self.querybuilder._makequery(
            query=self.query,
            custom_query={"collapse_on": "__PARENT__", "merge_fields": ["getId"]},
            sort_on="created",
            b_size=5,
            batch=True,
            brains=True,
        )

        # because we get the merged value before we reach the end the merge hasn't been completed
        merged = [len(b.getId) for b in collasped_results._sequence]
        self.assertEqual(merged, [5, 5, 5, 5, 5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])

    def testLengthHintWrong(self):
        query = [{
            'i': 'Subject',
            'o': 'plone.app.querystring.operation.selection.any',
            'v': ['Lorem', 'Ipsum'],
        }]
        results = self.querybuilder._makequery(
            query=query,
            custom_query={"collapse_on": "Subject", "fc_len": 1},
            sort_on="created"
        )
        self.assertEqual(len(results), 15)

    def testLengthHintQueryChanged(self):
        query = [
            {
                'i': 'Subject',
                'o': 'plone.app.querystring.operation.selection.any',
                'v': ['Lorem', 'Ipsum'],
            },
            {
                'i': 'path',
                'o': 'plone.app.querystring.operation.string.path',
                'v': '/'}
        ]
        results = self.querybuilder._makequery(
            query=query,
            custom_query={"collapse_on": "Subject", "fc_len": 15},
            sort_on="created",
            b_size=5,
            batch=True,
        )
        self.assertEqual(len(results), 55)  # It's made a guess at the total length
        self.assertEquals(self.request.form['fc_ends'], "25")  # We don't know the end yet but we know the end of the
        # first batch

        # if we use the checksum with the same query but set the length hint wrong then we will get the wrong len

        checksum = self.request.form['fc_check']
        results = self.querybuilder._makequery(
            query=query,
            custom_query={"collapse_on": "Subject", "fc_len": 30, "fc_check": checksum},
            sort_on="created",
            b_size=5,
            batch=True,
        )
        self.assertEqual(len(results), 30)

        # But if we change the query then fc_len will be ignored

        checksum = self.request.form['fc_check']
        results = self.querybuilder._makequery(
            query=query,
            custom_query={"collapse_on": "portal_type", "fc_len": 30, "fc_check": checksum},
            sort_on="created",
            b_size=5,
        )
        self.assertEqual(len(results), 1)
