..
    This file is part of m.css.

    Copyright © 2017, 2018 Vladimír Vondruš <mosra@centrum.cz>

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included
    in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
..

Presentation
############

:breadcrumb: {filename}/css.rst CSS
:footer:
    .. note-dim::
        :class: m-text-center

        `« Page layout <{filename}/css/page-layout.rst>`_ | `CSS <{filename}/css.rst>`_ | `Themes » <{filename}/css/themes.rst>`_

The `m-presentation.css <{filename}/css.rst>`_ file allows you to easily reuse
existing m.css features and components like math rendering or code highlighting
to create presentations (slide decks, keynotes, ..., you name it) that match
your website theme.

.. note-success::

    Check out `present.py <{filename}/pelican/theme.rst>`_ --- a standalone
    tool for creating presentations directly from :abbr:`reST <reStructuredText>`
    sources using m.css components.

.. contents::
    :class: m-block m-default

`Features`_
===========

-   Reuse all existing m.css components to create presentations
-   Ability to show a "presenter view" with additional notes
-   CSS-only, with optional minimal JavaScript for key bindings and presenter
    view synchronization
-   Print directly to PDF on supported browsers for maximal compatibility

`Basic markup structure`_
=========================

.. code:: html

    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <title>Presentation title</title>
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <link rel="stylesheet" href="m-dark-presentation.css" />
    </head>
    <body>
    <div class="m-container m-container-inflatable">
      <div class="m-row">
        <div class="m-col-l-12">
          <article>
            <aside>
              <!-- here goes the "boot screen" -->
            </aside>
            <section id="#cover">
              <!-- here goes the cover slide -->
            </section>
            <!-- here goes the rest of the presentation <section>s -->
          </article>
        </div>
      </div>
    </div>
    </body>
    </html>

.. note-info::

    See how a basic presentation `looks <{filename}/css/presentation/example.html>`_.

`Boot screen`_
==============

`Presenter view`_
=================

`JavaScript extras`_
====================

`Printing to a PDF`_
====================
