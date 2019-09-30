import unittest
import transaction
try:
    from zope.testbrowser.browser import LinkNotFoundError
except ImportError:
    from mechanize import LinkNotFoundError
from collective.fieldcollapsing.testing import COLLECTIVE_FIELDCOLLAPSING_FUNCTIONAL_TESTING, get_browser


def getLinks(browser, link_text, exact_match=True):
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


def assertNumLinks(browser, link_text, num, exact_match=True):
    links = getLinks(browser, link_text, exact_match)
    if len(links) < num:
        assert False, "Not enough links for '%s' %i<%i" % (link_text, len(links), num)
    elif len(links) > num:
        assert False, "Too many links for '%s' %i>%i" % (link_text, len(links), num)


class TestCollection(unittest.TestCase):
    layer = COLLECTIVE_FIELDCOLLAPSING_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.num_folders = self.layer['num_folders']
        self.num_docs_in_folder = self.layer['num_docs_in_folder']
        self.total_num_docs = self.num_folders * self.num_docs_in_folder

        self.portal.invokeFactory(
            "Collection",
            "collection",
            title="Collection",
            query=[{
                'i': 'portal_type',
                'o': 'plone.app.querystring.operation.selection.any',
                'v': ['Document']
            }],
            collapse_on=['__PARENT__'],
            sort_on="id",
            max_unfiltered_page_size=10,
            item_count=5,

        )

    def testBrowseBatch(self):

        b = get_browser(self.layer)
        transaction.commit()
        b.open(self.portal.collection.absolute_url())
        # make sure there are 5 items on the page
        assertNumLinks(b, 'Test Page', 5, exact_match=False)
        assertNumLinks(b, 'Test Page 01-01', 1)
        assertNumLinks(b, 'Test Page 02-01', 1)
        assertNumLinks(b, 'Test Page 03-01', 1)
        assertNumLinks(b, 'Test Page 04-01', 1)
        assertNumLinks(b, 'Test Page 05-01', 1)
        # Make sure that we have 11 pages (ie we don't know true length yet). Thinks its 55
        assertNumLinks(b, '11', 1)
        assertNumLinks(b, 'Next', 1, exact_match=False)

        getLinks(b, 'Next', exact_match=False)[0].click()
        assertNumLinks(b, '1', 1)
        assertNumLinks(b, '3', 1)
        assertNumLinks(b, 'Next', 1, exact_match=False)
        assertNumLinks(b, 'Test Page', 5, exact_match=False)
        # We've now learnt more about the real length so less pages
        assertNumLinks(b, '8', 0)
        assertNumLinks(b, '7', 1)

        # Jump ahead to the end
        getLinks(b, '7')[0].click()
        # Now we know the real length so we have correct number of pages
        assertNumLinks(b, 'Next', 0, exact_match=False)
        assertNumLinks(b, '4', 0)  # Current page is never a link
        assertNumLinks(b, '2', 1)
        # TODO: This test fails because the batching code thinks it should correct the start to 15 which is past the
        # end. It's not clear why its doing that since the page code indicates its on page 3 so the start should be 10.
        # Not yet clear if its a bug in batching and/if it should be corrected or what the workaround should be
        # assertNumLinks(b, 'Test Page', 5, exact_match=False)

        # Now even if we go back to the start we have the correct number of pages
        getLinks(b, '1')[0].click()
        # Now we know the real length so we have correct number of pages
        assertNumLinks(b, '3', 1)
        # assertNumLinks(b, '4', 0)
        # assertNumLinks(b, 'Test Page 1', 5)
