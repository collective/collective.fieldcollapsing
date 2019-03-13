# -*- coding: utf-8 -*-

from collective.fieldcollapsing.testing import \
    COLLECTIVE_FIELDCOLLAPSING_INTEGRATION_TESTING
from collective.fieldcollapsing.browser.querybuilder import QueryBuilder

from plone.app.querystring.querybuilder import QueryBuilder as BaseQueryBuilder
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest

import unittest


class TestQuerybuilder(unittest.TestCase):

    layer = COLLECTIVE_FIELDCOLLAPSING_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.num_folders = 15
        self.num_docs_in_folder = 5
        self.total_num_docs = self.num_folders * self.num_docs_in_folder
        for i in range(1, self.num_folders + 1):
            self.portal.invokeFactory("Folder",
                                      "testfolder-{}".format(i),
                                      title="Test Folder {}".format(i))
            test_folder = self.portal["testfolder-{}".format(i)]
            for j in range(1, self.num_docs_in_folder + 1):
                test_folder.invokeFactory(
                    "Document",
                    "testpage-{}".format(j),
                    title="Test Page {}".format(j))
                test_page = test_folder["testpage-{}".format(j)]
                test_page.setSubject(["Lorem", "Folder {}".format(i)])
                test_page.reindexObject()
                self.portal.portal_workflow.doActionFor(test_page, 'publish')
        
        self.request = TestRequest()
        self.querybuilder = QueryBuilder(
            self.portal, self.request
        )
        self.query = [{
            'i': 'portal_type',
            'o': 'plone.app.querystring.operation.selection.any',
            'v': ['Document']
        }]

    def testQueryBuilderHTML(self):
        results = self.querybuilder.html_results(self.query)
        self.assertTrue('Test Page 1' in results)

    def testQueryBuilderNumberOfResults(self):
        results = self.querybuilder.number_of_results(self.query)
        numeric = int(results.split(' ')[0])
        self.assertEqual(numeric, 1)

    def testMakeQuery(self):
        results = self.querybuilder._makequery(
            query=self.query,
            sort_on="created"
        )
        self.assertEqual(len(results), self.total_num_docs)
        self.assertEqual(
            results[0].getURL(),
            'http://nohost/plone/testfolder-1/testpage-1')
        self.assertEqual(
            results[1].getURL(),
            'http://nohost/plone/testfolder-1/testpage-2')
        self.assertEqual(
            results[2].getURL(),
            'http://nohost/plone/testfolder-1/testpage-3')

    def testMakeQueryWithBrains(self):
        results = self.querybuilder._makequery(
            query=self.query,
            custom_query={"collapse_on": "__PARENT__"},
            brains=True,
            sort_on="created"
        )
        self.assertEqual(len(results), self.total_num_docs)
        self.assertEqual(
            results[0].getURL(),
            'http://nohost/plone/testfolder-1/testpage-1')
        self.assertEqual(
            results[1].getURL(),
            'http://nohost/plone/testfolder-2/testpage-1')
        self.assertEqual(
            results[2].getURL(),
            'http://nohost/plone/testfolder-3/testpage-1')

    def testMakeQueryWithBrainsMultiCollapse(self):
        results = self.querybuilder._makequery(
            query=self.query,
            custom_query={"collapse_on": ['Subject', "__PARENT__"]},
            brains=True,
            sort_on="created"
        )
        self.assertEqual(len(results), self.total_num_docs)
        self.assertEqual(
            results[0].getURL(),
            'http://nohost/plone/testfolder-1/testpage-1')
        self.assertEqual(
            results[1].getURL(),
            'http://nohost/plone/testfolder-2/testpage-1')
        self.assertEqual(
            results[2].getURL(),
            'http://nohost/plone/testfolder-3/testpage-1')

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
            'http://nohost/plone/testfolder-1/testpage-1')
        self.assertEqual(
            results[1].getURL(),
            'http://nohost/plone/testfolder-1/testpage-2')
        self.assertEqual(
            results[2].getURL(),
            'http://nohost/plone/testfolder-1/testpage-3')

    def testMakeQueryWithBatch(self):
        results = self.querybuilder._makequery(
            query=self.query,
            custom_query={"collapse_on": "__PARENT__"},
            batch=True,
            sort_on="created"
        )
        self.assertEqual(len(results), self.total_num_docs)
        self.assertEqual(
            results[0].getURL(),
            'http://nohost/plone/testfolder-1/testpage-1')
        self.assertEqual(
            results[1].getURL(),
            'http://nohost/plone/testfolder-2/testpage-1')
        self.assertEqual(
            results[2].getURL(),
            'http://nohost/plone/testfolder-3/testpage-1')

    def testMakeQueryWithCollapseOn(self):
        results = self.querybuilder._makequery(
            query=self.query,
            sort_on="created"
        )
        self.assertEqual(len(results), self.total_num_docs)
        self.assertEqual(
            results[0].getURL(),
            'http://nohost/plone/testfolder-1/testpage-1')
        self.assertEqual(
            results[1].getURL(),
            'http://nohost/plone/testfolder-1/testpage-2')

        collasped_results = self.querybuilder._makequery(
            query=self.query,
            custom_query={"collapse_on": "__PARENT__"},
            sort_on="created"
        )
        
        # Test the reported length of the collapsed results
        self.assertEqual(len(collasped_results), self.total_num_docs)
        # Test the reported length of the collapsed results
        # aganist the actual length of the collapsed results
        self.assertNotEqual(
            len(collasped_results[:]),
            self.total_num_docs
        )
        # The actual length of the collapsed results should be 20 because
        # we created 20 folders and retrieve first document from each folder.
        self.assertEqual(
            len(collasped_results[:]),
            self.num_folders
        )
        
        self.assertEqual(
            collasped_results[0].getURL(),
            'http://nohost/plone/testfolder-1/testpage-1')
        self.assertEqual(
            collasped_results[1].getURL(),
            'http://nohost/plone/testfolder-2/testpage-1')
        self.assertEqual(
            collasped_results[2].getURL(),
            'http://nohost/plone/testfolder-3/testpage-1')

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
        self.assertEqual(len(results), self.total_num_docs)
        self.assertEqual(len(results[:]), self.num_folders)
        self.assertEqual(
            results[0].getURL(),
            'http://nohost/plone/testfolder-1/testpage-1')
        self.assertEqual(
            results[1].getURL(),
            'http://nohost/plone/testfolder-2/testpage-1')
        self.assertEqual(
            results[2].getURL(),
            'http://nohost/plone/testfolder-3/testpage-1')

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
        self.assertEqual(len(results), self.total_num_docs)
        self.assertEqual(len(results[:]), self.num_folders)
        self.assertEqual(
            results[0].getURL(),
            'http://nohost/plone/testfolder-1/testpage-1')
        self.assertEqual(
            results[1].getURL(),
            'http://nohost/plone/testfolder-2/testpage-1')
        self.assertEqual(
            results[2].getURL(),
            'http://nohost/plone/testfolder-3/testpage-1')


class TestQuerybuilderResultTypes(unittest.TestCase):

    layer = COLLECTIVE_FIELDCOLLAPSING_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = TestRequest()
        self.querybuilder = QueryBuilder(
            self.portal, self.request
        )
        self.query = [{
            'i': 'Title',
            'o': 'plone.app.querystring.operation.string.is',
            'v': 'Non-existent',
        }]

    def testQueryBuilderEmptyQueryContentListing(self):
        results = self.querybuilder._makequery(query={})
        self.assertEqual(len(results), 0)
        self.assertEqual(type(results).__name__, 'ContentListing')

    def testQueryBuilderEmptyQueryBrains(self):
        results = self.querybuilder._makequery(query={}, brains=True)
        self.assertEqual(len(results), 0)
        self.assertEqual(results, [])

    def testQueryBuilderEmptyQueryBatch(self):
        results = self.querybuilder._makequery(query={}, batch=True)
        self.assertEqual(len(results), 0)
        self.assertEqual(type(results).__name__, 'BaseBatch')

    def testQueryBuilderNonEmptyQueryContentListing(self):
        results = self.querybuilder._makequery(query=self.query)
        self.assertEqual(len(results), 0)
        self.assertEqual(type(results).__name__, 'ContentListing')

    def testQueryBuilderNonEmptyQueryBrains(self):
        results = self.querybuilder._makequery(query=self.query, brains=True)
        self.assertEqual(len(results), 0)
        self.assertEqual(type(results).__name__, 'LazyCat')

    def testQueryBuilderNonEmptyQueryBatch(self):
        results = self.querybuilder._makequery(query=self.query, batch=True)
        self.assertEqual(len(results), 0)
        self.assertEqual(type(results).__name__, 'BaseBatch')

    def testQueryBuilderNonEmptyContentListingCustomQuery(self):
        results = self.querybuilder._makequery(
            query={},
            custom_query={'portal_type': 'NonExistent'}
        )
        self.assertEqual(len(results), 0)
        self.assertEqual(type(results).__name__, 'ContentListing')

    def testQueryBuilderEmptyQueryContentListingWithCollapsing(self):
        results = self.querybuilder._makequery(
            query={},
            custom_query={"collapse_on": "Subject"}
        )
        self.assertEqual(len(results), 0)
        self.assertEqual(type(results).__name__, 'ContentListing')

    def testQueryBuilderEmptyQueryBrainsWithCollapsing(self):
        results = self.querybuilder._makequery(
            query={}, brains=True,
            custom_query={"collapse_on": "Subject"}
        )
        self.assertEqual(len(results), 0)

    def testQueryBuilderEmptyQueryBatchWithCollapsing(self):
        results = self.querybuilder._makequery(
            query={}, batch=True,
            custom_query={"collapse_on": "Subject"}
        )
        self.assertEqual(len(results), 0)
        self.assertEqual(type(results).__name__, 'BaseBatch')

    def testQueryBuilderNonEmptyQueryContentListingWithCollapsing(self):
        results = self.querybuilder._makequery(
            query=self.query,
            custom_query={"collapse_on": "Subject"}
        )
        self.assertEqual(len(results), 0)
        self.assertEqual(type(results).__name__, 'ContentListing')

    def testQueryBuilderNonEmptyQueryBrainsWithCollapsing(self):
        results = self.querybuilder._makequery(
            query=self.query,
            brains=True,
            custom_query={"collapse_on": "Subject"}
        )
        self.assertEqual(len(results), 0)
        self.assertEqual(type(results).__name__, 'LazyCat')

    def testQueryBuilderNonEmptyQueryBatchWithCollapsing(self):
        results = self.querybuilder._makequery(
            query=self.query,
            batch=True,
            custom_query={"collapse_on": "Subject"}
        )
        self.assertEqual(len(results), 0)
        self.assertEqual(type(results).__name__, 'BaseBatch')

    def testQueryBuilderNonEmptyContentListingCustomQueryWithCollapsing(self):
        results = self.querybuilder._makequery(
            query={},
            custom_query={
                'portal_type': 'NonExistent',
                "collapse_on": "Subject"}
        )
        self.assertEqual(len(results), 0)
        self.assertEqual(type(results).__name__, 'ContentListing')
