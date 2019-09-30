# -*- coding: utf-8 -*-
from __future__ import print_function
from Products.CMFPlone.interfaces import INavigationSchema
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile, TEST_USER_PASSWORD
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.registry.interfaces import IRegistry
from plone.testing import z2
from zope.component import getUtility
import collective.fieldcollapsing
from plone.testing.z2 import Browser
from six.moves import range


def setup_content(portal, num_folders, num_docs_in_folder):
    for i in range(1, num_folders + 1):
        fid = "testfolder-{:02d}".format(i)
        portal.invokeFactory("Folder",
                             fid,
                             title="Test Folder {:02d}".format(i))
        test_folder = portal[fid]
        for j in range(1, num_docs_in_folder + 1):
            id = "testpage-{:02d}-{:02d}".format(i, j)
            test_folder.invokeFactory(
                "Document",
                id,
                title="Test Page {:02d}-{:02d}".format(i, j))
            test_page = test_folder[id]
            test_page.setSubject(["Lorem", "Folder {}".format(i)])
            test_page.reindexObject()
            portal.portal_workflow.doActionFor(test_page, 'publish')


class CollectiveFieldcollapsingLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=collective.fieldcollapsing)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'collective.fieldcollapsing:default')
        setRoles(portal, TEST_USER_ID, ['Manager'])
        login(portal, TEST_USER_NAME)
        portal.acl_users.userFolderAddUser('admin',
                                           'secret',
                                           ['Manager'],
                                           [])
        portal.portal_workflow.setChainForPortalTypes(
            ('Document',), 'plone_workflow'
        )

        self.portal = portal
        self['num_folders'] = 15
        self['num_docs_in_folder'] = 5
        setup_content(self.portal, 15, 5)

        # Get rid of navigation so it doesn't intefer with browser tests
        registry = getUtility(IRegistry)
        navigation_settings = registry.forInterface(
            INavigationSchema,
            prefix="plone",
            check=False
        )
        navigation_settings.generate_tabs = False


def get_browser(layer):
    # api.user.create(
    #     username='adm', password='secret', email='a@example.org',
    #     roles=('Manager', )
    # )
    # transaction.commit()
    browser = Browser(layer['app'])
    browser.addHeader('Authorization', 'Basic %s:%s' % (TEST_USER_NAME, TEST_USER_PASSWORD))

    browser.handleErrors = False

    def raising(self, info):
        import traceback
        traceback.print_tb(info[2])
        print(info[1])  # noqa: T001

    from Products.SiteErrorLog.SiteErrorLog import SiteErrorLog
    SiteErrorLog.raising = raising

    return browser


COLLECTIVE_FIELDCOLLAPSING_FIXTURE = CollectiveFieldcollapsingLayer()


COLLECTIVE_FIELDCOLLAPSING_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLECTIVE_FIELDCOLLAPSING_FIXTURE,),
    name='CollectiveFieldcollapsingLayer:IntegrationTesting',
)


COLLECTIVE_FIELDCOLLAPSING_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_FIELDCOLLAPSING_FIXTURE,),
    name='CollectiveFieldcollapsingLayer:FunctionalTesting',
)


COLLECTIVE_FIELDCOLLAPSING_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        COLLECTIVE_FIELDCOLLAPSING_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='CollectiveFieldcollapsingLayer:AcceptanceTesting',
)
