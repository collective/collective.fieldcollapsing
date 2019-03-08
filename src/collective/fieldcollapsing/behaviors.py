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
    options.add('getParent')
    return SimpleVocabulary.fromValues(list(options))
directlyProvides(collapse_on_vocab, IContextSourceBinder)


@provider(IFormFieldProvider, ISyndicatable)
class ICollectionFieldCollapser(model.Schema):
    """Model based Dexterity Type"""

    collapse_on = schema.Choice(
        title=_(u"Collapse on"),
        source=collapse_on_vocab,
        required=False,
        description=_(
            u"Select the field, which the results will collapse on and return "
            u"the first of each collapsed set")
    )
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