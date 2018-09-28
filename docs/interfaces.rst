Interfaces
##########

Note that these descriptions are not necessarily exhaustive, but do include all columns that will be used by ``ensemble``.

ecoinvent DataFrames
====================

``products``
------------

The ``products`` DataFrame lists the products present in the rows of **A**, the technosphere matrix. It is unordered, and indexed by the ``productId`` column.

Columns
*******

* ``productId``: string. Ecoinvent UUID of the product.
* ``productName``: string. Name of product.
* ``unitId``: string. Ecoinvent UUID of the unit
* ``unitName``: string. Ecoinvent name of unit, e.g. "kg".

``activities``
--------------

The ``activities`` DataFrame lists the industrial activities in the columns of **A**, the technosphere matrix, and **B**, the biosphere matrix. It is unordered, and indexed by the ``activityId`` column,

Remember that there can be multiple activities in different locations with the same ``activityId``.

Activity types
**************

* 0: ordinary transforming activity
* 1: market activity
* 2: IO activity
* 3: Residual activity
* 4: production mix
* 5: import activity
* 6: supply mix
* 7: export activity
* 8: re-export activity
* 9: correction activity
* 10: market group

Columns
*******

* ``activityId``: string. Ecoinvent UUID of the activity.
* ``productId``: string. Ecoinvent UUID of the **reference product** for this instance of the activity.
* ``activityName``: string. Name of activity.
* ``ISIC``: string. Activity classification, e.g. "8292:Packaging activities"
* ``geography``: string. Location of activity.
* ``technologyLevel``: string. For example, "Current"
* ``activityType``: int. See above.
* ``startDate``: string, YYYY-MM-DD. For example, "1996-01-01".
* ``endDate``: string, YYYY-MM-DD. For example, "1996-01-01".


Environmental stressors (elementary exchanges)
----------------------------------------------
File: STR.csv
Data frame containing all basic information about the different environmental stressors. 

Columns
*******

* ``id``: string. Ecoinvent UUID of the elementary exchange.
* ``name``: string. Name of stressor.
* ``unit``: string. Name of Unit (e.g. kg.)
* ``cas``: string. Cas classification e.g. "000110-63-4"
* ``comp``: string. Compartment of stressor.
* ``subcomp``: string. Subcompartment of stressor.



G_act
-----
Pandas DataFrame listing all environmental exchanges (rows) per activity (columns):

Index
*****

* ``id``: string. Ecoinevent UUID of elementary exchange

Colunms
*******

* ``Activities``: float. Cumulative elementry exchange per activity per elementary exchange



EXIOBASE SUT DataFrames
====================

