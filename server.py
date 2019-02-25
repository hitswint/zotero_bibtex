#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""Start a web server listening on port 23119. This server is
compatible with the `zotero connector`. This means that if zotero is
*not* running, you can have items from your web browser added directly
into papis.

"""
import os
import json
import logging
import http.server
import tools

logger = logging.getLogger("zotero:bib:server")
logging.basicConfig(filename="", level=logging.INFO)

connector_api_version = 2
zotero_version = "5.0.25"
zotero_port = 23119
out_file = "~/.bib/EB.bib"

field_translation = {
    'abstractNote': 'abstract',
    'publicationTitle': 'journal',
    'DOI': 'doi',
    'ISSN': 'issn',
    'callNumber': 'lccn',
    'issue': 'number',
    'thesisType': 'type',
}


def zotero_data_to_bibtex(item):
    data = {}

    for key in field_translation.keys():
        if item.get(key):
            data[field_translation[key]] = item.get(key)
            del item[key]

    # Maybe zotero has good tags
    if isinstance(item.get('tags'), list):
        try:
            data['keywords'] = ', '.join([x['tag'] for x in item.get('tags')])
            logger.info("try")
        except:
            logger.info("pass")
            pass
        del item['tags']

    if isinstance(item.get('creators'), list):
        try:
            data['author'] = ' and '.join([
                x['lastName'] + ', ' + x['firstName']
                for x in item.get('creators')
            ])
        except:
            pass
        del item['creators']

    if item.get('itemType'):
        if item.get('itemType') == "journalArticle":
            data['itemType'] = "article"
        elif item.get('itemType') == "thesis":
            data['itemType'] = "phdthesis"
        else:
            data['itemType'] = "misc"

        del item['itemType']

    if item.get('date'):
        if ',' in item.get('date'):
            data['year'] = item.get('date').split(',')[-1].strip()
            # data['month'] = item.get('date').split(',')[0].strip()
        else:
            data['year'] = item.get('date')

        del item['date']

    # still get all information from zotero
    data.update(item)

    return data


class BibtexRequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        global logger
        logger.info(fmt % args)
        return

    def set_zotero_headers(self):
        self.send_header("X-Zotero-Version", zotero_version)
        self.send_header("X-Zotero-Connector-API-Version",
                         connector_api_version)
        self.end_headers()

    def read_input(self):
        length = int(self.headers['content-length'])
        return self.rfile.read(length)

    def pong(self, POST=True):
        global logger
        logger.info("pong!")
        # Pong must respond to ping on both GET and POST
        # It must accepts application/json and text/plain
        if not POST:  # GET
            logger.debug("GET request")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.set_zotero_headers()
            response = '''\
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Zotero Connector Server is Available</title>
                </head>
                <body>
                    Zotero Connector Server is Available
                </body>
            </html>
            '''
        else:  # POST
            logger.debug("POST request")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.set_zotero_headers()
            response = json.dumps({"prefs": {"automaticSnapshots": True}})

        self.wfile.write(bytes(response, "utf8"))

    def collection(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.set_zotero_headers()

        bib_library = 0
        response = json.dumps({
            "libraryID": 1,
            "libraryName": bib_library,
            "libraryEditable": True,
            "editable": True,
            "id": None,
            "name": bib_library
        })
        self.wfile.write(bytes(response, "utf8"))

    def add(self):
        logger.info("Adding paper from zotero connector")
        rawinput = self.read_input()
        data = json.loads(rawinput.decode('utf8'))

        bib_items = [zotero_data_to_bibtex(item) for item in data['items']]

        tools.write(bib_items, os.path.expanduser(out_file), "braces", False)

        self.send_response(201)  # Created
        self.set_zotero_headers()
        # return the JSON data back
        self.wfile.write(rawinput)

    def snapshot(self):
        logger.warning("Snapshot not implemented")
        self.send_response(201)
        self.set_zotero_headers()
        return

    def do_POST(self):
        if self.path == "/connector/ping":
            self.pong()
        elif self.path == '/connector/getSelectedCollection':
            self.collection()
        elif self.path == '/connector/saveSnapshot':
            self.snapshot()
        elif self.path == '/connector/saveItems':
            self.add()
        return

    def do_GET(self):
        if self.path == "/connector/ping":
            self.pong(POST=False)
