..
  NOTE: This RST file was generated by `make examples`.
  Do not edit it directly.
  See docs/source/examples/example_doc_generator.py

Override Layout Constraints Example
===============================================================================

An example which demonstrates overriding ``layout_constraints``.

This example shows how one can override ``layout_constraints`` method from
enaml syntax to generate custom constraints using procedural code. This
can be useful for complex layout scenarios where generating constraints
from a single expression would be difficult or impossible.

.. TIP:: To see this example in action, download it from
 :download:`override_layout_constraints <../../../examples/layout/advanced/override_layout_constraints.enaml>`
 and run::

   $ enaml-run override_layout_constraints.enaml


Screenshot
-------------------------------------------------------------------------------

.. image:: images/ex_override_layout_constraints.png

Example Enaml Code
-------------------------------------------------------------------------------
.. literalinclude:: ../../../examples/layout/advanced/override_layout_constraints.enaml
    :language: enaml
