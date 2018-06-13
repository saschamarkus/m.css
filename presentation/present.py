#!/usr/bin/env python3

#
#   This file is part of m.css.
#
#   Copyright © 2017, 2018 Vladimír Vondruš <mosra@centrum.cz>
#
#   Permission is hereby granted, free of charge, to any person obtaining a
#   copy of this software and associated documentation files (the "Software"),
#   to deal in the Software without restriction, including without limitation
#   the rights to use, copy, modify, merge, publish, distribute, sublicense,
#   and/or sell copies of the Software, and to permit persons to whom the
#   Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included
#   in all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#   THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#   FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#   DEALINGS IN THE SOFTWARE.
#

import argparse
import copy
import docutils
import inspect
import jinja2
import logging
import os
import shutil
import sys
import time
import urllib

from importlib.machinery import SourceFileLoader
from types import SimpleNamespace as Empty

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../pelican-plugins'))
import m.htmlsanity
import m.code
import m.math

default_templates = os.path.dirname(os.path.realpath(__file__))
default_config = {
    'M_EXTRA_FILES': [
        '../css/m-grid.css',
        '../css/m-components.css',
        '../css/pygments-dark.css',
        '../css/pygments-console.css'],
    'M_CSS_FILES': [
        '../css/m-dark.css',
        '../css/m-presentation.css']
}

class Presenter:
    def __init__(self, templates):
        m.code.register()
        m.math.register()

        extra_params = {'initial_header_level': '2',
                        'syntax_highlight': 'short',
                        'input_encoding': 'utf-8',
                        'language_code': 'en',
                        'exit_status_level': 5,
                        'embed_stylesheet': False}
        self.pub = docutils.core.Publisher(
            writer=m.htmlsanity.SaneHtmlWriter(),
            source_class=docutils.io.StringInput,
            destination_class=docutils.io.StringOutput)
        self.pub.set_components('standalone', 'restructuredtext', 'html')
        self.pub.writer.translator_class = m.htmlsanity.SaneHtmlTranslator
        self.pub.process_programmatic_settings(None, extra_params, None)

        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates),
            trim_blocks=True, lstrip_blocks=True, enable_async=True)
        def basename_or_url(path):
            if urllib.parse.urlparse(path).netloc: return path
            return os.path.basename(path)
        self.env.filters['basename_or_url'] = basename_or_url

    def present(self, input, output, config):
        basedir = os.path.dirname(input)

        m.htmlsanity.configure(config)

        logging.debug("reading {}".format(input))
        with open(input, 'r') as f: source = f.read()

        self.pub.set_source(source=source)
        self.pub.publish(enable_exit_status=True)

        metadata = {}
        for docinfo in self.pub.document.traverse(docutils.nodes.docinfo):
            for element in docinfo.children:
                # Custom named field
                if element.tagname == 'field':
                    name_elem, body_elem = element.children
                    name = name_elem.astext()
                    #if name in formatted_fields:
                        #value = render_node_to_html(
                            #document, body_elem,
                            #self.field_body_translator_class)
                    #else:
                    value = body_elem.astext()
                # Author list
                elif element.tagname == 'authors':
                    name = element.tagname
                    value = [element.astext() for element in element.children]
                # Standard field
                else:
                    name = element.tagname
                    value = element.astext()
                name = name.lower()

                metadata[name] = value

        page = Empty()
        page.title = 'hey'
        page.content = self.pub.writer.parts.get('body')

        template = self.env.get_template('presentation.html')
        rendered = template.render(page=page, **config)

        output_file = os.path.join(output, 'index.html')
        logging.debug("writing {}".format(output_file))
        if not os.path.exists(output): os.makedirs(output)
        with open(output_file, 'w') as f: f.write(rendered)

        # Copy all referenced files
        for i in config['M_EXTRA_FILES'] + config['M_CSS_FILES'] + ['presentation.js']:
            # Skip absolute URLs
            if urllib.parse.urlparse(i).netloc: continue

            # If file is found relative to the input file, use that
            if os.path.exists(os.path.join(basedir, i)):
                i = os.path.join(basedir, i)

            # Otherwise use path relative to script directory
            else:
                i = os.path.join(os.path.dirname(os.path.realpath(__file__)), i)

            logging.debug("copying {} to {}".format(i, basedir))
            shutil.copy(i, os.path.join(output, os.path.basename(i)))

def file_watcher(path):
    last_mtime = 0
    while True:
        if path:
            mtime = os.stat(path).st_mtime
            if not last_mtime: last_mtime = mtime

            if mtime > last_mtime:
                last_mtime = mtime
                yield True
            else:
                yield False
        else:
            yield None

if __name__ == '__main__': # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help="input reST file with the presentation")
    parser.add_argument('output', help="output directory")
    parser.add_argument('--templates', help="template directory", default=default_templates)
    parser.add_argument('-c', '--config', help='config file')
    parser.add_argument('--debug', help="verbose debug output", action='store_true')
    parser.add_argument('--autoreload', help="", action='store_true')
    args = parser.parse_args()

    # Load configuration from a file or use the default
    if args.config:
        name, _ = os.path.splitext(os.path.basename(args.config))
        module = SourceFileLoader(name, args.config).load_module()
        config = copy.deepcopy(default_config)
        if module is not None:
            # hum? TODO what is this
            config.update((k, v) for k, v in inspect.getmembers(module) if k.isupper())
    else:
        config = copy.deepcopy(default_config)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    presenter = Presenter(args.templates)
    presenter.present(args.input, args.output, config)

    if args.autoreload:
        for updated in file_watcher(args.input):
            if updated:
                logging.info("modified {}, updating...".format(args.input))
                presenter.present(args.input, args.output, config)
            else:
                time.sleep(1)
