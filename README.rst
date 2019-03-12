.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

==========================
collective.fieldcollapsing
==========================

This add-on provides Field Collapsing feature to Plone through a behaviour provided to the **Collection Content Type** similar to field collapsing in ElasticSearch.

A Collection can have one of more field set to collapse on. This groups or de-deplicates the result list of the collection such that only the first result with a given values of that set of fields is shown. All subsequent matching results won't appear in the list. There is limited support for path based collapsing also such as collapsing on the parent.

For example

- if you have content types for companies and employees
- you wanted to have a custom search page to search for companies that had employees with certain skills
- you could use collective.collectionfilter and collective.fieldcollapsing to provide a search page which let you search details of employees but return only links to companies.
- you would set collapse_on for the collection to be the custom metadata field "company_id" in this example (or if employees are contained within company objects then use the parent path to collapse on).

Features
--------

- Provides Field Collapsing behaviour for the **Collection Content Type**
- Group similar results together based on the selected metadata fields.
- Retrieve the most relevant hits first.
- Retrieve only one result from a whole set of resources is included in the results list


Documentation
-------------

This add-on works similar to Elastic Search field collapsing function as explained here - https://www.rea-group.com/blog/using-elasticsearch-field-collapsing-to-group-related-search-results/


Installation
------------

Install collective.fieldcollapsing by adding it to your buildout::

    [buildout]

    ...

    eggs =
        collective.fieldcollapsing


and then running ``bin/buildout``


Afterwards, install the add-on via Add-on Control panel

Field Collapsing behaviour will automatically be installed on the default Collection Content Type but custom collections can have it added by visiting Dexterity Content Types Control panel.


Contribute
----------

- Issue Tracker: https://github.com/collective/collective.fieldcollapsing/issues
- Source Code: https://github.com/collective/collective.fieldcollapsing


License
-------

The project is licensed under the GPLv2.
