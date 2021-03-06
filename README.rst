.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

==========================
collective.fieldcollapsing
==========================

This add-on provides Field Collapsing feature to Plone through a behaviour provided to the **Collection Content Type**
similar to field collapsing in ElasticSearch.

A Collection can have one of more field set to collapse on. This groups or de-deplicates the result list of the
collection such that only the first result with a given values of that set of fields is shown. All subsequent matching
results won't appear in the list. There is limited support for path based collapsing also such as collapsing on the parent.

For example

- if you have content types for companies and employees
- you wanted to have a custom search page to search for companies that had employees with certain skills
- you could use collective.collectionfilter and collective.fieldcollapsing to provide a search page which let you
  search details of employees but return only links to companies.
- you would set collapse_on for the collection to be the custom metadata field "company_id" in this example (or
  if employees are contained within company objects then use the parent path to collapse on).
- In order for this search page to return the Comany object you could use collective.listingviews to customise the
  results layout to link to related company as the default results will still list the top employee hit per company.

This add-on works similar to Elastic Search field collapsing function as explained here
- https://www.rea-group.com/blog/using-elasticsearch-field-collapsing-to-group-related-search-results/

Features
--------

- Provides Field Collapsing behaviour for the **Collection Content Type**
- Group similar results together based on the selected metadata fields.
- Retrieve the most relevant hits first.
- Retrieve only one result from a whole set of resources is included in the results list
- Merge certain metadata fields into a single list per collapsed item so collective.collectionfilter works correctly
  or to make display views more informative


Future Enhancements
-------------------

- Ability to collapse on other parts of the path other than parent
- Advanced setting to collapse on a TAL expression
- Store hidden results in special value in brain if required
- Option to automatically return parent result instead of first child (avoid having to use listingviews to do this)
  or at least adjust theh url to be that of the parent
- Integrate with ElasticSearch if installed to use its field collapsing for increased performance
- Integrate more directly with the query widget so Tiles etc can make use of field collapsing


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



TODOs
----------
- Add support for Live Preview of the field collapsing feature


Contribute
----------

- Issue Tracker: https://github.com/collective/collective.fieldcollapsing/issues
- Source Code: https://github.com/collective/collective.fieldcollapsing


License
-------

The project is licensed under the GPLv2.

Thanks
------

Special thanks to Multicultural Health Communication Service of NSW for sponsoring the inital work on this plugin 
