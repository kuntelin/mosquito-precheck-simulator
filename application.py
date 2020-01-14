import os
import tempfile
from datetime import datetime
from flask import Flask, request, abort, jsonify


app = Flask(__name__)


def version():
    stat = os.stat(__file__)
    return datetime.utcfromtimestamp(stat.st_mtime).strftime('%Y%m%d.%H%M')


def blob_connection_string():
    try:
        return os.environ['AZURE_STORAGE_CONNECTION_STRING']
    except KeyError as _deprecated:
        return 'NOT SET'


def get_blob_client():
    from azure.storage.blob import BlobServiceClient

    return BlobServiceClient.from_connection_string(blob_connection_string())


@app.route('/')
def hello():
    hello_message = """
Hello from Alex!

VER: {}
CONNECTION_STRING: {}
"""

    return hello_message.format(version(), blob_connection_string()[:30])


@app.route('/post_check', methods=['POST'])
def post_check():
    # return jsonify(request.form.to_dict(flat=False))

    if 'image' not in request.files:
        abort(400, 'no image')

    image = request.files['image']

    if image.filename == '':
        abort(400, 'no image in uploaded files')

    return jsonify({
        'version': version(),
        'name': image.name,
        'filename': image.filename,
        'size': len(image.read()),
    })


@app.route('/trigger_blob_create_event', methods=['GET'])
def trigger_blob_create_event():
    if request.method == 'GET':
        try:
            client = get_blob_client()
        except Exception as e:
            return e.args[0]

        container = request.args.get('container', None)
        counter = request.args.get('counter', None)

        if not container or not counter:
            return 'container and counter must be specified'

        try:
            counter = int(counter)
        except TypeError as _deprecated:
            return 'counter mus be integer'

        # create container for this operation
        try:
            container_client = client.create_container(name=container)
        except Exception as e:
            return "something wrong with create container: {}".format(e)

        # create temp file for upload
        tmpfile = tempfile.NamedTemporaryFile()
        tmpname = tmpfile.name.split('/').pop(-1)

        # upload files with counter times
        for index in range(counter):
            blob_client = client.get_blob_client(container=container, blob="{}_{}".format(tmpname, index))
            blob_client.upload_blob(tmpfile)

        return jsonify({
            'container': container,
            'blob_list': sorted([x.name for x in container_client.list_blobs()]),
        })


if __name__ == '__main__':
    app.debug = True
    app.run()

