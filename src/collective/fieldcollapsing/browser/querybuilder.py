# -*- coding: utf-8 -*-

import json
import logging
from math import floor

import Missing

# from operator import itemgetter
# from plone import api
# from plone.app.contentlisting.interfaces import IContentListing
# from plone.app.querystring import queryparser
# from plone.app.querystring.interfaces import IParsedQueryIndexModifier
# from plone.app.querystring.interfaces import IQueryModifier
# from plone.app.querystring.interfaces import IQuerystringRegistryReader
from plone.app.contentlisting.interfaces import IContentListing
from plone.batching import Batch
# from plone.registry.interfaces import IRegistry
# from zope.component import getMultiAdapter, getUtility, getUtilitiesFor
# from zope.i18n import translate
# from zope.i18nmessageid import MessageFactory
# from zope.publisher.browser import BrowserView
# from AccessControl import getSecurityManager
# from AccessControl.unauthorized import Unauthorized
# from AccessControl.ZopeGuards import guarded_getitem
# from Products.CMFCore.utils import getToolByName
from ZTUtils import LazyFilter, make_query
from plone.app.querystring.querybuilder import QueryBuilder as BaseQueryBuilder
from plone.batching.browser import BatchView

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
  
    def __init__(self, query={}):
        self._base_results = set()
        self.query = query
        self.collapse_on = list(self.query.get('collapse_on', []))
        self.has_collapse_on_parent = '__PARENT__' in self.collapse_on
        
        if self.has_collapse_on_parent:
            self.collapse_on.remove('__PARENT__')
        
        self.has_metadata = len(self.collapse_on) > 0

        # Bit of a hacky way to keep track of how many unfiltered items we are up to
        self.test_count = 0

    def _collapse_on_parent(self, brain, default=False):
        if self.has_collapse_on_parent:
            base_path = path_ = brain.getPath()
            path_sep = path_.split("/")
            if brain.Type != 'Plone Site':
                field_value = "/".join(path_sep[:-1])
                if field_value not in self._base_results:
                    self._base_results.add(field_value)
                    return True
            else:
                return True
        return default

    def collapse(self, brain):
        is_successful = False
        self.test_count += 1
        collapsed_on_parent = self._collapse_on_parent(brain)
        if not self.has_metadata:
            return collapsed_on_parent

        for metafield in self.collapse_on:
            field_value = getattr(brain, metafield, None)
            if field_value is None or field_value is Missing.Value:
                if self.has_collapse_on_parent:
                    return collapsed_on_parent
                return True
            if hasattr(field_value, '__iter__'):
                set_diff = set(field_value) - self._base_results
                if len(set_diff) > 0:
                    self._base_results.update(set_diff)
                    if not is_successful:
                        is_successful = True
        
        if self.has_collapse_on_parent:
            return collapsed_on_parent
        return is_successful


class QueryBuilder(BaseQueryBuilder):

    def _makequery(self, query=None, batch=False, b_start=0, b_size=30,
                   sort_on=None, sort_order=None, limit=0, brains=False,
                   custom_query=None):
        """Parse the (form)query and return using multi-adapter"""


        # Catalog assumes we want to limit the results to b_start+b_size. We would like to limit the
        # search too however we don't for sure what to limit it to since we need an unknown number
        # of returns to fill up an filtered page
        # We will use a combination of hints to guess
        # - data about how much filtered in pages the user has click on before
        # - the final length if the user clicked on the last page
        # - a look ahead param on the collection representing the max number of unfiltered results to make up a filtered page
        #if b_start >=10:
        #    import pdb; pdb.set_trace()

        fc_ends = enumerate([int(i) for i in self.request.get('fc_ends','').split(':') if i])
        fc_ends = [(page, i) for page, i in fc_ends if page*b_size <= b_start+b_size]
        if not fc_ends:
            nearest_page, nearest_end = 0,0
        else:
            nearest_page, nearest_end = max(fc_ends)

        max_unfiltered_pagesize = getattr(self.context, 'max_unfiltered_page_size', 1000)

        additional_pages = int(floor(float(b_start)/b_size - nearest_page))
        safe_start = nearest_end
        safe_limit = additional_pages * max_unfiltered_pagesize

        results = super(QueryBuilder, self)._makequery(
            query,
            batch=False,
            b_start=safe_start,
            b_size=safe_limit,
            sort_on=sort_on,
            sort_order=sort_order,
            limit=limit,
            brains=True,
            custom_query=custom_query
        )

        collapse_on = getattr(self.context, 'collapse_on', set())
        if custom_query is not None and 'collapse_on' in custom_query:
            custom_collapse_on = custom_query.get('collapse_on')
            if hasattr(custom_collapse_on, '__iter__'):
                collapse_on.update(custom_collapse_on)
            elif type(custom_collapse_on) in [str, unicode]:
                collapse_on.add(custom_collapse_on)
            del custom_query['collapse_on']

        if  collapse_on:

            fc = FieldCollapser(query={'collapse_on': collapse_on})

            unfiltered = results
            results = LazyFilterLen(unfiltered, test=fc.collapse)
            fc_len = self.request.get('fc_len', None)
            if fc_len is not None:
                #import pdb; pdb.set_trace()
                results.actual_result_count = results.fc_len = fc_len

            # Work out unfiltered index up until the end of the current page
            unfiltered_ends = []
            index = b_size
            while index < b_start+b_size+1:
                try:
                    results[index]
                except IndexError:
                    self.request.form['fc_len'] = len(results)
                    break
                else:
                    if hasattr(results, '_eindex'):
                        unfiltered_ends.append(results._eindex)
                index += b_size

            if len(unfiltered_ends) > len(fc_ends):
                # Put this into request so it ends up the batch links
                self.request.form['fc_ends'] = ':'.join([str(i) for i in unfiltered_ends])

        if not brains:
            results = IContentListing(results)
        if batch:
            results = Batch(results, b_size, start=b_start)
        return results



# batching seems to call len and that ends up iterating over the whole filter
# Also batching has this weird optimisation that if the actual is not the same as len it assumes the seq is just that page
# and it repeats items
class LazyFilterLen(LazyFilter):
    def __len__(self):
        if hasattr(self, 'fc_len'):
            return self.fc_len
        if hasattr(self, '_eindex'):
            self.actual_result_count = self._seq.actual_result_count -  (self._eindex + 1) + len(self._data)
        else:
            self.actual_result_count = len(self._data)
        return self.actual_result_count

