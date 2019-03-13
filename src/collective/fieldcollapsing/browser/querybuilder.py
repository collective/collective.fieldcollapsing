# -*- coding: utf-8 -*-

import json
import logging
import Missing

from operator import itemgetter
from plone import api
from plone.app.contentlisting.interfaces import IContentListing
from plone.app.querystring import queryparser
from plone.app.querystring.interfaces import IParsedQueryIndexModifier
from plone.app.querystring.interfaces import IQueryModifier
from plone.app.querystring.interfaces import IQuerystringRegistryReader
from plone.batching import Batch
from plone.registry.interfaces import IRegistry
from zope.component import getMultiAdapter, getUtility, getUtilitiesFor
from zope.i18n import translate
from zope.i18nmessageid import MessageFactory
from zope.publisher.browser import BrowserView
from AccessControl import getSecurityManager
from AccessControl.unauthorized import Unauthorized
from AccessControl.ZopeGuards import guarded_getitem
from Products.CMFCore.utils import getToolByName
from ZTUtils import LazyFilter
from plone.app.querystring.querybuilder import QueryBuilder as BaseQueryBuilder

from collective.fieldcollapsing import _
from collective.fieldcollapsing import logger


try:
    from ZTUtils.Lazy import LazyCat
    from ZTUtils.Lazy import LazyMap
except ImportError:
    # bbb import for Zope2
    from Products.ZCatalog.Lazy import LazyCat
    from Products.ZCatalog.Lazy import LazyMap


class FieldCollapser(object):
  
    def __init__(self, query={'collapse_on': None}):
        self._base_results = set()
        self.query = query
        self.collapse_on = self.query.get('collapse_on', None)
        self.collapse_on_parent = self.collapse_on == '__PARENT__'
  
    def collapse(self, brain):
        base_brain = brain
        base_path = path_ = brain.getPath()
        path_sep = path_.split("/")

        if self.collapse_on_parent:
            if brain.Type != 'Plone Site':
                field_value = "/".join(path_sep[:-1])
            else:
                return True
        else:
            field_value = getattr(brain, self.collapse_on, None)
            if field_value is None or field_value is Missing.Value:
                return True
            if hasattr(field_value, '__iter__'):
                set_diff = set(field_value) - self._base_results
                if len(set_diff) > 0:
                    self._base_results.update(set_diff)
                    return True
                return False
        if field_value not in self._base_results:
            self._base_results.add(field_value)
            return True
        return False

        if base_path not in self._base_results:
            self._base_results.add(base_path)
            return True
        return False


class QueryBuilder(BaseQueryBuilder):

    def _makequery(self, query=None, batch=False, b_start=0, b_size=30,
                   sort_on=None, sort_order=None, limit=0, brains=False,
                   custom_query=None):
        """Parse the (form)query and return using multi-adapter"""
        query_modifiers = getUtilitiesFor(IQueryModifier)
        for name, modifier in sorted(query_modifiers, key=itemgetter(0)):
            query = modifier(query)

        parsedquery = queryparser.parseFormquery(
            self.context, query, sort_on, sort_order)

        index_modifiers = getUtilitiesFor(IParsedQueryIndexModifier)
        for name, modifier in index_modifiers:
            if name in parsedquery:
                new_name, query = modifier(parsedquery[name])
                parsedquery[name] = query
                # if a new index name has been returned, we need to replace
                # the native ones
                if name != new_name:
                    del parsedquery[name]
                    parsedquery[new_name] = query

        # Check for valid indexes
        catalog = getToolByName(self.context, 'portal_catalog')
        valid_indexes = [index for index in parsedquery
                         if index in catalog.indexes()]

        # We'll ignore any invalid index, but will return an empty set if none
        # of the indexes are valid.
        if not valid_indexes:
            logger.warning(
                "Using empty query because there are no valid indexes used.")
            parsedquery = {}

        empty_query = not parsedquery  # store emptiness
        if batch:
            parsedquery['b_start'] = b_start
            parsedquery['b_size'] = b_size
        elif limit:
            parsedquery['sort_limit'] = limit

        if 'path' not in parsedquery:
            parsedquery['path'] = {'query': ''}

        collapse_on = self.request.get(
            'collapse_on',
            getattr(self.context, 'collapse_on', None)
        )
        if isinstance(custom_query, dict) and custom_query:
            # Update the parsed query with an extra query dictionary. This may
            # override the parsed query. The custom_query is a dictonary of
            # index names and their associated query values.
            if 'collapse_on' in custom_query:
                collapse_on = custom_query.get('collapse_on', collapse_on)
                del custom_query['collapse_on']
            parsedquery.update(custom_query)
            empty_query = False

        # filter bad term and operator in query
        parsedquery =  self.filter_query(parsedquery)
        results = []
        if not empty_query:
            results = catalog(**parsedquery)
            if getattr(results, 'actual_result_count', False) and limit\
                    and results.actual_result_count > limit:
                results.actual_result_count = limit

        if collapse_on is not None:
            fc = FieldCollapser(
                query={'collapse_on': collapse_on}
            )
            if type(results).__name__ == 'LazyCat':
                results = LazyCat(
                    LazyFilter(results, test=fc.collapse),
                    length=results._len,
                    actual_result_count=results.actual_result_count
                )
            else:
                results = LazyMap(
                    lambda x:x,
                    LazyFilter(results, test=fc.collapse),
                    length=results._len,
                    actual_result_count=results.actual_result_count
                )

        if not brains:
            results = IContentListing(results)
        if batch:
            results = Batch(results, b_size, start=b_start)
        return results
