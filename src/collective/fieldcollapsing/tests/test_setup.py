# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from collective.fieldcollapsing.testing import COLLECTIVE_FIELDCOLLAPSING_INTEGRATION_TESTING  # noqa

import unittest


class TestSetup(unittest.TestCase):
    """Test that collective.fieldcollapsing is properly installed."""

    layer = COLLECTIVE_FIELDCOLLAPSING_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if collective.fieldcollapsing is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'collective.fieldcollapsing'))

    def test_browserlayer(self):
        """Test that ICollectiveFieldcollapsingLayer is registered."""
        from collective.fieldcollapsing.interfaces import (
            ICollectiveFieldcollapsingLayer)
        from plone.browserlayer import utils
        self.assertIn(
            ICollectiveFieldcollapsingLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = COLLECTIVE_FIELDCOLLAPSING_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer.uninstallProducts(['collective.fieldcollapsing'])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if collective.fieldcollapsing is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'collective.fieldcollapsing'))

    def test_browserlayer_removed(self):
        """Test that ICollectiveFieldcollapsingLayer is removed."""
        from collective.fieldcollapsing.interfaces import \
            ICollectiveFieldcollapsingLayer
        from plone.browserlayer import utils
        self.assertNotIn(
            ICollectiveFieldcollapsingLayer,
            utils.registered_layers())
