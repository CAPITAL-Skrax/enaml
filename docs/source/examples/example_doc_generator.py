#------------------------------------------------------------------------------
# Copyright (c) 2013-2018, Nucleic Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#------------------------------------------------------------------------------
""" Generate the Example Documentation for the Enaml Examples

Run as part of the documentation build script. Requires PyQt4.
Look for example enaml files with the line:

<< autodoc-me >>

Generate an rst file, then open the app and take a snapshot.

Note: Many examples have dependencies outside of the normal Enaml dependencies.
These will need to be installed for the snapshots to be generated.

"""
from __future__ import print_function
import argparse
import os
import re
import shutil
import sys
from textwrap import dedent

from atom.api import Atom, Unicode, Value
import enaml
from enaml.qt.qt_application import QtApplication
from enaml.qt.QtWidgets import QApplication
from enaml.qt.QtTest import QTest


class SnapShot(Atom):
    """ Generate a snapshot of an enaml view.

    """

    #: The snapshot save path.
    path = Unicode()

    #: The enaml view object.
    view = Value()

    def _observe_view(self, change):
        """ Move window and allow it to draw before taking the snapshot.

        """
        if change['type'] == 'create':
            self.view.initial_position = (10, 10)
            self.view.always_on_top = True

    def snapshot(self):
        """ Take a snapshot of the window and close it.

        """
        widget = self.view.proxy.widget
        framesize = widget.window().frameSize()
        screen = QApplication.primaryScreen()
        screen.grabWindow(
            QApplication.desktop().winId(),
            widget.x(), widget.y(),
            framesize.width(), framesize.height()
            ).save(self.path)
        self.view.close()


def save_snapshot_of_module(mod, image_path):
    view = mod.Main()
    snapshot = SnapShot(path=image_path, view=view)
    view.show()
    QTest.qWaitForWindowExposed(view.proxy.widget)
    QTest.qWait(500)
    snapshot.snapshot()
    QTest.qWait(100)


def extract_docstring(script_text):
    """ Extract the docstring from an example Enaml script. """

    # The docstring is found between the first two '"""' strings.
    return script_text.split('"""')[1]


def clean_docstring(docstring):
    """ Convert a docstring into ReStructuredText format. """

    docstring = docstring.replace('<< autodoc-me >>\n', '').strip()
    # Find backquoted identifiers, and double the backquotes to match RST.
    docstring = re.sub(
        pattern=r"`(?P<identifier>[A-Za-z_]+)`",  # Backquoted identifiers
        repl=r"``\g<identifier>``",  # Double backquoted identifiers
        string=docstring)

    return docstring


SCREENSHOT_RST_TEMPLATE = dedent("""
    Screenshot
    -------------------------------------------------------------------------------

    .. image:: images/{name}
    """)

EXAMPLE_DOC_RST_TEMPLATE = dedent("""
    ..
      NOTE: This RST file was generated by `make examples`.
      Do not edit it directly.
      See docs/source/examples/example_doc_generator.py

    {title} Example
    ===============================================================================

    {docstring_rst}

    .. TIP:: To see this example in action, download it from
     :download:`{name} <../../../{path}>`
     and run::

       $ enaml-run {name}.enaml

    {screenshot_rst}
    Example Enaml Code
    -------------------------------------------------------------------------------
    .. literalinclude:: ../../../{path}
        :language: enaml
    """)


def generate_example_doc(docs_path, script_path):
    """ Generate an RST and a PNG for an example file.

    Parameters
    ----------
    docs_path : str
         Full path to enaml/docs/source/examples
    script_path : str
         Full path to the example enaml file
    """
    script_name = os.path.basename(script_path)
    script_name = script_name[:script_name.find('.')]
    print('generating doc for %s' % script_name)

    script_title = script_name.replace('_', ' ').title()
    script_image_name = 'ex_' + script_name + '.png'
    image_path = os.path.join(docs_path, 'images', script_image_name)
    rst_path = os.path.join(
        docs_path, 'ex_' + script_name + '.rst')
    relative_script_path = script_path[
        script_path.find('examples'):].replace('\\', '/')

    # Add the script to the Python Path
    old_python_path = sys.path
    sys.path = sys.path + [os.path.dirname(script_path)]

    snapshot_success = False
    with enaml.imports():
        try:
            mod = __import__(script_name)
            save_snapshot_of_module(mod, image_path)
            snapshot_success = True
        except Exception as err:
            print('Could not snapshot: %s' % script_name)
            print('    %s' % err)
        finally:
            # The import leaves behind a cache. Clean it up.
            enaml_cache_dir = os.path.join(
                os.path.dirname(script_path), '__enamlcache__')
            shutil.rmtree(enaml_cache_dir)

    # Restore Python path.
    sys.path = old_python_path

    with open(os.path.join(script_path)) as fid:
        script_text = fid.read()

    docstring = clean_docstring(extract_docstring(script_text))

    screenshot_rst = '' if not snapshot_success else (
            SCREENSHOT_RST_TEMPLATE.format(name=script_image_name))

    example_doc_rst = EXAMPLE_DOC_RST_TEMPLATE.format(
        title=script_title,
        name=script_name,
        path=relative_script_path,
        docstring_rst=docstring,
        screenshot_rst=screenshot_rst)

    with open(rst_path, 'wb') as rst_output_file:
        rst_output_file.write(example_doc_rst.lstrip().encode())


def main(white_list):
    """ Generate documentation for all enaml examples requesting autodoc.

    Looks in enaml/examples for all enaml files, then looks for the line:
    << auto-doc >>

    If the line appears in the script, generate an RST and PNG for the example.
    """
    app = QtApplication()
    docs_path = os.path.dirname(__file__)
    base_path = '../../../examples'
    base_path = os.path.realpath(os.path.join(docs_path, base_path))

    # Find all the files in the examples directory with a .enaml extension
    # that contain the pragma '<< autodoc-me >>', and generate .rst files for
    # them.
    for dirname, dirnames, filenames in os.walk(base_path):
        files = [os.path.join(dirname, f)
                 for f in filenames if f.endswith('.enaml')]
        if white_list:
            files = [f for f in files
                     if any([f.endswith(w) for w in white_list])]
        for fname in files:
            with open(fname, 'rb') as fid:
                data = fid.read()
            if b'<< autodoc-me >>' in data.splitlines():
                    generate_example_doc(docs_path, fname)


if __name__ == '__main__':

    doc = ("Enaml example documentation generator.\n\n"
           "By default all examples with the << auto-doc >> directive are "
           "processed.")
    parser = argparse.ArgumentParser(description=doc)
    parser.add_argument('-f', '--filenames',
                        help='Files for which to generate the docs',
                        action='store', nargs='+')

    args = parser.parse_args()

    main(args.filenames)
