# -*- coding: utf-8 -*-
import transaction
from mechanize import LinkNotFoundError
from zope.testbrowser.browser import Browser

from collective.fieldcollapsing.testing import \
    COLLECTIVE_FIELDCOLLAPSING_INTEGRATION_TESTING, get_browser, COLLECTIVE_FIELDCOLLAPSING_FUNCTIONAL_TESTING
from collective.fieldcollapsing.browser.querybuilder import QueryBuilder

from plone.app.querystring.querybuilder import QueryBuilder as BaseQueryBuilder
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest

import unittest

def setup_content(portal, num_folders, num_docs_in_folder):
    for i in range(1, num_folders + 1):
        fid = "testfolder-{:02d}".format(i)
        portal.invokeFactory("Folder",
                                  fid,
                                  title="Test Folder {:02d}".format(i))
        test_folder = portal[fid]
        for j in range(1, num_docs_in_folder + 1):
            id = "testpage-{:02d}-{:02d}".format(i,j)
            test_folder.invokeFactory(
                "Document",
                id,
                title="Test Page {:02d}-{:02d}".format(i,j))
            test_page = test_folder[id]
            test_page.setSubject(["Lorem", "Folder {}".format(i)])
            test_page.reindexObject()
            portal.portal_workflow.doActionFor(test_page, 'publish')


class TestQuerybuilder(unittest.TestCase):

    layer = COLLECTIVE_FIELDCOLLAPSING_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.num_folders = 15
        self.num_docs_in_folder = 5
        self.total_num_docs = self.num_folders * self.num_docs_in_folder
        setup_content(self.portal, self.num_folders, self.num_docs_in_folder)

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
        self.assertIn('Test Page 01-01',results)
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

    def testMakeQueryWithBrainsMultiCollapse(self):
        results = self.querybuilder._makequery(
            query=self.query,
            custom_query={"collapse_on": ['Subject', "__PARENT__"]},
            brains=True,
            sort_on="created",
            b_size=5,
        )
        self.assertEqual(len(results), 55) # lazyfilter gueses the len
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
        self.assertEqual(len(results), 55) # lazyfilter guesses the len
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
            b_size=5
        )
        
        # Test the reported length of the collapsed results
        self.assertEqual(len(collasped_results), 55) # lazyfilter guesses the len
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


    def testMergeSubject(self):

        # First lets show the data in there
        results = self.querybuilder._makequery(
            query=self.query,
            sort_on="created"
        )
        self.assertEqual(
            results[0].Subject(), ('Lorem', 'Folder 1'))

        for i, page in enumerate(results):
            tags = page.Subject()
            if i % 2 == 1:
                page.getObject().setSubject(set())
            else:
                page.getObject().setSubject(('page {}'.format(i+1),))
            page.getObject().reindexObject()

        collasped_results = self.querybuilder._makequery(
            query=self.query,
            custom_query={"collapse_on": "__PARENT__", "merge_fields":["Subject"]},
            sort_on="created",
            b_size=5
        )

        # now when we look at subject to see if its merged
        self.assertEqual(
            collasped_results[0].Subject(), ('page 1', 'page 3', 'page 5'))
        self.assertEqual(
            collasped_results[1].Subject(), ('page 7', 'page 9'))

    def testMergeTitle(self):

        # First lets show the data in there
        results = self.querybuilder._makequery(
            query=self.query,
            sort_on="created"
        )
        self.assertEqual(
            results[0].Title(), 'Test Page 01-01')

        collasped_results = self.querybuilder._makequery(
            query=self.query,
            custom_query={"collapse_on": "__PARENT__", "merge_fields":["Title"]},
            sort_on="created",
            b_size=5
        )

        # now when we look at subject to see if its merged
        self.assertEqual(
            collasped_results[0].Title(), 'Test Page 01-01 Test Page 01-02 Test Page 01-03 Test Page 01-04 Test Page 01-05')


    def testMergeType(self):

        # First lets show the data in there
        results = self.querybuilder._makequery(
            query=self.query,
            sort_on="created"
        )
        self.assertEqual(
            results[0].Type(), 'Page')

        collasped_results = self.querybuilder._makequery(
            query=self.query,
            custom_query={"collapse_on": "__PARENT__", "merge_fields":["Type"]},
            sort_on="created",
            b_size=5
        )

        # now when we look at subject to see if its merged
        self.assertEqual(collasped_results[0].Type(), ('Page',) )


    def testLengthHintWrong(self):
        query = [{
            'i': 'Subject',
            'o': 'plone.app.querystring.operation.selection.any',
            'v': ['Lorem', 'Ipsum'],
        }]
        results = self.querybuilder._makequery(
            query=query,
            custom_query={"collapse_on": "Subject", "fc_len":1},
            sort_on="created"
        )
        self.assertEqual(len(results), 15)

    def testLengthHintQueryChanged(self):
        query = [{
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
            custom_query={"collapse_on": "Subject", "fc_len":15},
            sort_on="created",
            b_size=5,
        )
        self.assertEqual(len(results), 55) # It's made a guess at the total length
        self.assertEquals(self.request.form['fc_ends'], "25") # We don't know the end yet but we know the end of the first batch

        # if we use the checksum with the same query but set the length hint wrong then we will get the wrong len

        checksum = self.request.form['fc_check']
        results = self.querybuilder._makequery(
            query=query,
            custom_query={"collapse_on": "Subject", "fc_len":30, "fc_check":checksum},
            sort_on="created",
            b_size = 5,
        )
        self.assertEqual(len(results), 30)


        # But if we change the query then fc_len will be ignored

        checksum = self.request.form['fc_check']
        results = self.querybuilder._makequery(
            query=query,
            custom_query={"collapse_on": "portal_type", "fc_len":30, "fc_check":checksum},
            sort_on="created",
            b_size = 5,
        )
        self.assertEqual(len(results), 1)


class TestCollection(unittest.TestCase):
    layer = COLLECTIVE_FIELDCOLLAPSING_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.num_folders = 15
        self.num_docs_in_folder = 5
        self.total_num_docs = self.num_folders * self.num_docs_in_folder
        setup_content(self.portal, self.num_folders, self.num_docs_in_folder)

        self.portal.invokeFactory(
            "Collection",
            "collection",
            title="Collection",
            query = [{
                'i': 'portal_type',
                'o': 'plone.app.querystring.operation.selection.any',
                'v': ['Document']
            }],
            collapse_on=['__PARENT__'],
            sort_on="id",
            max_unfiltered_page_size=10,
            item_count=5,

        )

    def getLinks(self, browser, link_text, exact_match=True):
        links = []
        index = 0
        while True:
            try:
                link = browser.getLink(link_text, index=index)
            except LinkNotFoundError:
                break
            if not exact_match or link.text == link_text:
                links.append(link)
            index += 1
        return links

    def assertNumLinks(self, browser, link_text, num, exact_match=True):
        links = self.getLinks(browser,link_text,exact_match)
        if len(links) < num:
            print browser.contents
            assert False, "Not enough links for '%s' %i<%i" % (link_text, len(links), num)
        elif len(links) > num:
            print browser.contents
            assert False, "Too many links for '%s' %i>%i" % (link_text, len(links), num)

    def testBrowseBatch(self):

        b = get_browser(self.layer)
        transaction.commit()
        b.open(self.portal.collection.absolute_url())
        # make sure there are 5 items on the page
        self.assertNumLinks(b, 'Test Page', 5, exact_match=False)
        self.assertNumLinks(b, 'Test Page 01-01', 1)
        self.assertNumLinks(b, 'Test Page 02-01', 1)
        self.assertNumLinks(b, 'Test Page 03-01', 1)
        self.assertNumLinks(b, 'Test Page 04-01', 1)
        self.assertNumLinks(b, 'Test Page 05-01', 1)
        # Make sure that we have 11 pages (ie we don't know true length yet). Thinks its 55
        self.assertNumLinks(b, '11', 1)
        self.assertNumLinks(b, 'Next 5 items »', 1)

        b.follow('Next 5 items »')
        self.assertNumLinks(b, '1', 1)
        self.assertNumLinks(b, '3', 1)
        self.assertNumLinks(b, 'Next 5 items »', 1)
        self.assertNumLinks(b, 'Test Page', 5, exact_match=False)
        # We've now learnt more about the real length so less pages
        self.assertNumLinks(b, '8', 0)
        self.assertNumLinks(b, '7', 1)

        # Jump ahead to the end
        self.getLinks(b, '7')[0].click()
        # Now we know the real length so we have correct number of pages
        self.assertNumLinks(b, 'Next', 0, exact_match=False)
        self.assertNumLinks(b, '4', 0) #Current page is never a link
        self.assertNumLinks(b, '2', 1)
        # TODO: This test fails because the batching code thinks it should correct the start to 15 which is past the
        # end. It's not clear why its doing that since the page code indicates its on page 3 so the start should be 10.
        # Not yet clear if its a bug in batching and/if it should be corrected or what the workaround should be
        self.assertNumLinks(b, 'Test Page', 5, exact_match=False)

        # Now even if we go back to the start we have the correct number of pages
        self.getLinks(b, '1')[0].click()
        # Now we know the real length so we have correct number of pages
        self.assertNumLinks(b, '3', 1)
        self.assertNumLinks(b, '4', 0)
        self.assertNumLinks(b, 'Test Page 1', 5)




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
