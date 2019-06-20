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
from plone import api
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

INDEX2MERGE_TYPE = dict(
    KeywordIndex=tuple,
    FieldIndex=tuple,
    TopicIndex=tuple,
    ZCTextIndex=unicode
)

class FieldCollapser(object):
  
    def __init__(self, collapse_on=[], merge_fields=[]):
        self.seen_before = dict()  #TODO: should be (field_value,field_value,..) -> brain
        self.collapse_on = collapse_on
        self.merge_fields = merge_fields

        self.merge_type = merge_type = {}
        catalog = api.portal.get_tool('portal_catalog')
        indexes = dict(zip(catalog.indexes(), catalog.getIndexObjects()))
        for field in merge_fields:
            index = indexes.get(field, None)
            if index is None:
                merge_type[field] = None
                continue
            merge_type[field] = INDEX2MERGE_TYPE.get(index.meta_type, None)


    def collapse(self, brain):
        key = ()
        for metafield in self.collapse_on:
            if metafield == '__PARENT__':
                base_path = path_ = brain.getPath()
                path_sep = path_.split("/")
                if brain.Type != 'Plone Site':
                    key += ("/".join(path_sep[:-1]), )
            else:
                field_value = getattr(brain, metafield, None)
                #if field_value is Missing.Value:
                #    return True
                key += (field_value,)

        def conv(value, _type):
            if not value:
                return _type()
            elif type(value) == _type:
                return value

            if _type in [list,tuple] and type(value) not in [list,tuple]:
                return _type([value])
            else:
                return _type(value)

        if key not in self.seen_before:
            self.seen_before[key] = brain
            first = object() # so first is None
            keep = True
        else:
            first = self.seen_before[key]
            keep = False

        # in this case we need to merge some fields from this result into our first one
        for metafield in self.merge_fields:
            _type = self.merge_type[metafield]
            merged = conv(getattr(first, metafield, None), _type)
            value = conv(getattr(brain, metafield, None), _type)
            if not value:
                continue

            if _type == None:
                continue
            elif _type in (tuple, list):
                merged += tuple(i for i in tuple(value) if i not in merged)
            elif _type == unicode:
                # TODO: actually makes more sense to do this based on index type
                merged = u" ".join([merged, unicode(value)]).strip()
            elif _type == dict:
                merged.update(dict(value))
            elif _type in [int,float]:
                merged += value
            else:
                #TODO: how to merge dates?
                continue

            setattr(self.seen_before[key], metafield, merged)
        return keep


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
        merge_fields = getattr(self.context, 'merge_fields', None)
        if merge_fields is None and custom_query is not None:
            merge_fields = custom_query.get('merge_fields',set())
        elif merge_fields is None:
            merge_fields = set()


        if collapse_on:

            fc = FieldCollapser(collapse_on=collapse_on, merge_fields=merge_fields)

            unfiltered = results
            results = LazyFilterLen(unfiltered, test=fc.collapse)
            fc_len = self.request.get('fc_len', None)
            if fc_len is not None:
                #import pdb; pdb.set_trace()
                results.actual_result_count = results.fc_len = int(fc_len)

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

