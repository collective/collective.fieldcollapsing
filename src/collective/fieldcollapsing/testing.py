# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.testing import z2

import collective.fieldcollapsing


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
