.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

==========================
collective.fieldcollapsing
==========================

This add-ons provides Field Collapsing feature to Plone through a behavior provided to the **Collection Content Type**.

The Field Collapsing function allows search results collapsed into a single entry based on field values.
The collapsing is done by selecting only the top sorted document per collapse key.


Features
--------

- Providesz Field Collapsing behavior for the **Collection Content Type**
- Group similar results together based on the selected metadata field.
- Retrive the most relevent hits first.
- Retrive only one result from a whole set of resources is included in the results list


Documentation
-------------

This works similar to Elastic Search field collapsing function as explained here - https://www.rea-group.com/blog/using-elasticsearch-field-collapsing-to-group-related-search-results/


Installation
------------

Install collective.fieldcollapsing by adding it to your buildout::

    [buildout]

    ...

    eggs =
        collective.fieldcollapsing


and then running ``bin/buildout``


Afterwards, install the add-on via Add-on Controlpanel

Enable the Field Collapsing behavior on the Collection Content Type by visitng Dexterity Content Types Controlpanel.


Contribute
----------

- Issue Tracker: https://github.com/collective/collective.fieldcollapsing/issues
- Source Code: https://github.com/collective/collective.fieldcollapsing


License
-------

The project is licensed under the GPLv2.
