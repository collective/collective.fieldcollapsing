from plone import api
from plone.supermodel import model
from plone.autoform import directives
from plone.app.contenttypes.interfaces import ICollection
from plone.app.z3cform.widget import AjaxSelectFieldWidget
from plone.app.z3cform.widget import SelectFieldWidget
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from zope import schema
from zope.component import adapter
from zope.interface import alsoProvides
from zope.interface import provider
from zope.interface import implementer

from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.syndication import ISyndicatable
from zope.interface import directlyProvides

from collective.fieldcollapsing import _


def collapse_on_vocab(context):
    catalog = api.portal.get_tool('portal_catalog')
    options = set(catalog._catalog.names)
    options.add('__PARENT__')
    return SimpleVocabulary.fromValues(list(options))
directlyProvides(collapse_on_vocab, IContextSourceBinder)


@provider(IFormFieldProvider, ISyndicatable)
class ICollectionFieldCollapser(model.Schema):
    """Model based Dexterity Type"""

    collapse_on = schema.Set(
        title=_(u"Collapse on"),
        required=False,
        value_type=schema.Choice(source=collapse_on_vocab),
        description=_(
            u"Select the field, which the results will collapse on and return "
            u"the first of each collapsed set")
    )
    directives.widget(
        'collapse_on',
        SelectFieldWidget
    )

    collapse_batch_multiplier = schema.Int(
        title=_(u"Collapse Batch"),
        required=False,
        default=3,
        description=_(
            u"Collapse the total number of pages by the given integer to "
            u"ensure that the number of items on each page is close to the "
            u"given item count. For instance, if each page suppose to show 30 "
            u"items and there are 18 pages, which have up to 8 items, then "
            u"fill up the page from other pages based on the given number of "
            u"collapsed pages. As a result, if the given number of collapsed "
            u"pages is 2, then there will be a total of 9 pages instead of 18 "
            u"pages with 30 items if applicable."
        )
    )
    directives.order_after(collapse_batch_multiplier='ICollection.query')
    directives.order_after(collapse_on='ICollection.query')


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
    def collapse_batch_multiplier(self):
        return getattr(self.context, 'collapse_batch_multiplier', 3)

    @collapse_batch_multiplier.setter
    def collapse_batch_multiplier(self, value):
        self.context.collapse_batch_multiplier = value