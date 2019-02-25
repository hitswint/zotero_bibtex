import click
import logging
import http.server
import server


@click.group()
@click.help_option('-h', '--help')
def main():
    logger = logging.getLogger("bibtex:zotero")
    logger.info("library '{0}'".format(0))


@main.command('serve')
@click.help_option('-h', '--help')
@click.option(
    "--port", help="Port to listen to", default=server.zotero_port, type=int)
@click.option("--address", help="Address to bind", default="localhost")
def serve(address, port):
    """Start a zotero-connector server"""
    global logger
    server_address = (address, port)
    httpd = http.server.HTTPServer(server_address, server.BibtexRequestHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
