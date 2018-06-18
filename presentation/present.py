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
import http.server
import inspect
import jinja2
import logging
import multiprocessing
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
import m.components
import m.math

from docutils.parsers import rst
from docutils.parsers.rst import directives
from docutils.parsers.rst.roles import set_classes
from docutils import nodes

class PresenterDirective(rst.Directive):
    has_content = True
    optional_arguments = 0

    def run(self):
        set_classes(self.options)

        text = '\n'.join(self.content)
        topic_node = nodes.topic(text, **self.options)
        topic_node['classes'] += ['m-presenter']

        self.state.nested_parse(self.content, self.content_offset,
                                topic_node)
        return [topic_node]

default_templates = os.path.dirname(os.path.realpath(__file__))
default_config = {
    # TODO: mimic pelican with these?
    'DEFAULT_LANG': 'en',
    'M_HTMLSANITY_SMART_QUOTES': True,
    'M_EXTRA_FILES': [
        '../css/m-grid.css',
        '../css/m-components.css',
        '../css/m-presentation.css',
        '../css/m-theme-dark.css',
        '../css/pygments-dark.css',
        '../css/pygments-console.css'],
    'M_CSS_FILES': [
        'https://fonts.googleapis.com/css?family=Source+Code+Pro:400,400i,600%7CSource+Sans+Pro:400,400i,600,600i',
        '../css/m-dark-presentation.css']
}

class Presenter:
    def __init__(self, templates):
        # TODO: ugh
        m.code.register()
        m.components.register()
        m.math.register()

        rst.directives.register_directive('presenter', PresenterDirective)

        extra_params = {'initial_header_level': '2',
                        'syntax_highlight': 'short',
                        'input_encoding': 'utf-8',
                        'language_code': 'en',
                        # TODO: five only when autoreload, should exit with
                        # failure in batch mode
                        'exit_status_level': 5,
                        'sectsubtitle_xform': True,
                        'embed_stylesheet': False}
        self.pub = docutils.core.Publisher(
            #writer=docutils.writers.html4css1.Writer(),
            writer=m.htmlsanity.SaneHtmlWriter(),
            source_class=docutils.io.StringInput,
            destination_class=docutils.io.StringOutput)
        self.pub.set_components('standalone', 'restructuredtext', 'html')
        #self.pub.writer.translator_class = m.htmlsanity.SaneHtmlTranslator
        self.pub.process_programmatic_settings(None, extra_params, None)

        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates),
            trim_blocks=True, lstrip_blocks=True, enable_async=True)
        def basename_or_url(path):
            if urllib.parse.urlparse(path).netloc: return path
            return '/' + os.path.basename(path) # TODO: fix w/o the /
        self.env.filters['basename_or_url'] = basename_or_url

    def present(self, input, output, config, presenter_view):
        basedir = os.path.dirname(input)

        m.htmlsanity.configure(config)

        logging.debug("reading {}".format(input))
        with open(input, 'r') as f: source = f.read()

        self.pub.set_source(source=source, source_path=input)
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

        print(self.pub.writer.parts.get('subtitle'))

        page = Empty()
        page.title = self.pub.writer.parts.get('title')
        page.subtitle = self.pub.writer.parts.get('subtitle')
        page.content = self.pub.writer.parts.get('body')
        for key, value in metadata.items():
            setattr(page, key, value)

        # Add cover image to the extra files to be copied
        extra_files = []
        if hasattr(page, 'cover'): extra_files += [page.cover]

        # Write normal view
        template = self.env.get_template('template.html')
        rendered = template.render(page=page, PRESENTER_VIEW=False, **config)

        if not os.path.exists(output): os.makedirs(output)
        output_file = os.path.join(output, 'index.html')
        logging.debug("writing {}".format(output_file))
        with open(output_file, 'w') as f: f.write(rendered)

        # Write presenter view, if requested
        if presenter_view:
            rendered = template.render(page=page, PRESENTER_VIEW=True, **config)

            presenter_output = os.path.join(output, presenter_view)
            if not os.path.exists(presenter_output): os.makedirs(presenter_output)
            output_file = os.path.join(presenter_output, 'index.html')
            logging.debug("writing {}".format(output_file))
            with open(output_file, 'w') as f: f.write(rendered)

        # Copy all referenced files
        for i in config['M_EXTRA_FILES'] + config['M_CSS_FILES'] + ['presentation.js'] + extra_files:
            # Skip absolute URLs
            if urllib.parse.urlparse(i).netloc: continue

            # If file is found relative to the input file, use that
            if os.path.exists(os.path.join(basedir, i)):
                i = os.path.join(basedir, i)

            # Otherwise use path relative to script directory
            else:
                i = os.path.join(os.path.dirname(os.path.realpath(__file__)), i)

            logging.debug("copying {} to {}".format(i, output))
            shutil.copy(i, os.path.join(output, os.path.basename(i)))

def file_watcher(path):
    last_mtime = 0
    while True:
        mtime = os.stat(path).st_mtime
        # Avoid reporting the file has changed right after start
        if not last_mtime:
            last_mtime = mtime
        elif mtime > last_mtime:
            last_mtime = mtime
            yield True
        else:
            yield False

def autoreload(presenter, input, output, config, presenter_view):
    for updated in file_watcher(input):
        if updated:
            logging.info("modified {}, updating".format(input))
            presenter.present(input, output, config, presenter_view)
            logging.info("done")
        else:
            time.sleep(1)

def serve(output, port):
    os.chdir(output)
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

if __name__ == '__main__': # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help="input reST file with the presentation")
    parser.add_argument('-o', '--output', help="output directory (relative to input)", default='output/')
    parser.add_argument('--presenter', nargs='?', const='presenter/', default=None, help="generate a presenter view")
    parser.add_argument('--templates', help="template directory", default=default_templates)
    parser.add_argument('-c', '--config', help='config file')
    parser.add_argument('--debug', help="verbose debug output", action='store_true')
    parser.add_argument('--autoreload', help="reload on input file change", action='store_true')
    parser.add_argument('--serve', help="serve the output via a webserver", action='store_true')
    parser.add_argument('-p', '--port', help="", default='8000', type=int)
    args = parser.parse_args()

    #os.chdir(os.path.dirname(args.input))

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

    output = os.path.join(os.path.dirname(args.input), args.output)

    presenter = Presenter(args.templates)
    presenter.present(args.input, output, config, args.presenter)

    if args.autoreload and args.serve:
        logging.info("serving on http://localhost:{} with autoreload ...".format(args.port))
        queue = multiprocessing.Queue()
        reloader = multiprocessing.Process(target=autoreload, args=(presenter, args.input, output, config, args.presenter))
        server = multiprocessing.Process(target=serve, args=(output, args.port))
        reloader.start()
        server.start()
        e = queue.get()
        reloader.terminate()
        server.terminate()
        logging.critical(e)
    elif args.autoreload:
        logging.info("started autoreload...")
        autoreload(presenter, args.input, output, config, args.presenter)
    elif args.serve:
        logging.info("serving on http://localhost:{} ...".format(args.port))
        serve(output, args.port)
