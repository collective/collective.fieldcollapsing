# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from collective.fieldcollapsing.testing import COLLECTIVE_FIELDCOLLAPSING_INTEGRATION_TESTING  # noqa
import unittest
try:
    from Products.CMFPlone.utils import get_installer
except Exception:
    # Quick shim for 5.1 api change

    class get_installer(object):
        def __init__(self, portal, request):
            self.installer = api.portal.get_tool('portal_quickinstaller')

        def is_product_installed(self, name):
            return self.installer.isProductInstalled(name)

        def uninstall_product(self, name):
            return self.installer.uninstallProducts([name])


class TestSetup(unittest.TestCase):
    """Test that collective.fieldcollapsing is properly installed."""

    layer = COLLECTIVE_FIELDCOLLAPSING_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = get_installer(self.portal, self.layer['request'])

    def test_product_installed(self):
        """Test if collective.collectionfilter is installed."""
        self.assertTrue(self.installer.is_product_installed(
            'collective.fieldcollapsing'))

    def test_browserlayer(self):
        """Test that ICollectionFilterBrowserLayer is registered."""
        from collective.fieldcollapsing.interfaces import ICollectiveFieldcollapsingLayer
        from plone.browserlayer import utils
        self.assertIn(
            ICollectiveFieldcollapsingLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = COLLECTIVE_FIELDCOLLAPSING_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = get_installer(self.portal, self.layer['request'])
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer.uninstall_product('collective.fieldcollapsing')
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if collective.collectionfilter is cleanly uninstalled."""
        self.assertFalse(self.installer.is_product_installed(
            'collective.fieldcollapsing'))

    def test_browserlayer_removed(self):
        """Test that ICollectionFilterBrowserLayer is removed."""
        from collective.fieldcollapsing.interfaces import \
            ICollectiveFieldcollapsingLayer
        from plone.browserlayer import utils
        self.assertNotIn(
            ICollectiveFieldcollapsingLayer,
            utils.registered_layers())
