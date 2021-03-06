from plone import api
from plone.supermodel import model
from plone.autoform import directives
from plone.app.z3cform.widget import SelectFieldWidget
from plone.autoform.interfaces import IFormFieldProvider
from zope import schema
from zope.interface import provider
from zope.interface import implementer
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary
from Products.CMFPlone.interfaces.syndication import ISyndicatable
from zope.interface import directlyProvides

from collective.fieldcollapsing import _


def collapse_on_vocab(context):
    catalog = api.portal.get_tool('portal_catalog')
    options = [('Path (Parent)', '__PARENT__')]
    options += [(i, i) for i in sorted(catalog._catalog.names)]
    return SimpleVocabulary.fromItems(list(options))
directlyProvides(collapse_on_vocab, IContextSourceBinder)


@provider(IFormFieldProvider, ISyndicatable)
class ICollectionFieldCollapser(model.Schema):
    """Model based Dexterity Type"""

    directives.widget('collapse_on', SelectFieldWidget)
    directives.order_after(collapse_on='ICollection.query')
    collapse_on = schema.Set(
        title=_(u"Collapse on"),
        required=False,
        value_type=schema.Choice(source=collapse_on_vocab),
        description=_(
            u"Select the field, which the results will collapse on and return "
            u"the first of each collapsed set")
    )

    directives.widget('merge_fields', SelectFieldWidget)
    directives.order_after(merge_fields='ICollectionFieldCollapser.collapse_on')
    merge_fields = schema.Set(
        title=_(u"Fields to merge"),
        required=False,
        description=_(
            u"Combine field data into a list/text when items collapse based on associated Index type. This is useful for"
            u"collective.collectionfilter to ensure the right options appear in filters"
        ),
        value_type=schema.Choice(
            source=collapse_on_vocab,
        )
    )

    directives.order_after(max_unfiltered_page_size='ICollectionFieldCollapser.merge_fields')
    max_unfiltered_page_size = schema.Int(
        title=_(u"Max Uncollapsed Page Size"),
        required=False,
        default=1000,
        description=_(
            u"To improve performance the search will only lookahead this number "
            u"of results which will then be collapsed into one page in a batch. "
            u"If this is set to low you may be missing results on the current page."
        )
    )


@implementer(ICollectionFieldCollapser)
class CollectionFieldCollapserFactory(object):

    def __init__(self, context):
        self.context = context

    @property
    def collapse_on(self):
        return getattr(self.context, 'collapse_on', None)

    @collapse_on.setter
    def collapse_on(self, value):
        self.context.collapse_on = value

    @property
    def max_unfiltered_page_size(self):
        return getattr(self.context, 'max_unfiltered_page_size', 1000)

    @max_unfiltered_page_size.setter
    def max_unfiltered_page_size(self, value):
        self.context.max_unfiltered_page_size = value

    @property
    def merge_fields(self):
        return getattr(self.context, 'merge_fields', None)

    @merge_fields.setter
    def merge_fields(self, value):
        self.context.merge_fields = value
