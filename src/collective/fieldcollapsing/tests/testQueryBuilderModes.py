import unittest
from collective.fieldcollapsing.testing import COLLECTIVE_FIELDCOLLAPSING_INTEGRATION_TESTING
from zope.publisher.browser import TestRequest
from collective.fieldcollapsing.browser.querybuilder import QueryBuilder


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
        self.querybuilder.max_unfiltered_page_size = 10

    def testQueryBuilderEmptyQueryContentListing(self):
        results = self.querybuilder._makequery(query={})
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
        self.assertEqual(type(results).__name__, 'ContentListing')

    def testQueryBuilderEmptyQueryBatchWithCollapsing(self):
        results = self.querybuilder._makequery(
            query={}, batch=True,
            custom_query={"collapse_on": "Subject"}
        )
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
        self.assertEqual(type(results).__name__, 'LazyFilterLen')

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
