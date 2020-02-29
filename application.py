import os
import tempfile
import time
from datetime import datetime
from flask import Flask, request, abort, jsonify


app = Flask(__name__)


def version():
    stat = os.stat(__file__)
    return datetime.utcfromtimestamp(stat.st_mtime).strftime('%Y%m%d.%H%M')


def storage_connection_string():
    try:
        return os.environ['AZURE_STORAGE_CONNECTION_STRING']
    except KeyError as _deprecated:
        return 'NOT SET'


def get_blob_client():
    from azure.storage.blob import BlobServiceClient

    return BlobServiceClient.from_connection_string(storage_connection_string())


@app.route('/')
def hello():
    return jsonify({
        'version': version(),
        'azure_storage_connect_string': storage_connection_string()[:30],
        'message': 'Hello from Alex!',
    })


@app.route('/post_image', methods=['POST'])
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


@app.route('/create_blobs_on_container', methods=['GET'])
def create_blobs_on_container():
    """
    @:param container: container name
    @:type container: str
    @:param counter: how many blobs to create
    @:type counter: integer
    @:param interval: interval between blob creation
    @:type interval: integer
    @:param wait: how many seconds to wait on each interval
    @:type wait: float
    :return:
    """

    if request.method == 'GET':
        try:
            client = get_blob_client()
        except Exception as e:
            return e.args[0]

        container = request.args.get('container', None)
        counter = request.args.get('counter', None)
        interval = request.args.get('interval', None)
        wait = request.args.get('wait', None)

        if not container or not counter:
            return 'container and counter must be specified'

        try:
            counter = int(counter)
        except TypeError as _deprecated:
            return 'counter must be integer'

        if interval:
            try:
                interval = int(interval)
            except TypeError as _deprecated:
                return 'interval must be integer'

            if interval == 0:
                return 'interval can not be 0'

        if wait:
            try:
                wait = float(wait)
            except TypeError as _deprecated:
                return 'wait must be float'

        # create container for this operation
        try:
            container_client = client.create_container(name=container)
        except Exception as e:
            return "something wrong with get container client: {}".format(e)

        # create temp file for upload
        tmpfile = tempfile.NamedTemporaryFile()
        tmpname = tmpfile.name.split('/').pop(-1)

        # upload files with counter times
        for index in range(counter):
            # wait few seconds on each interval
            if interval is not None and counter % interval == 0:
                if wait:
                    time.sleep(wait)

            blob_client = client.get_blob_client(container=container, blob="{}_{}".format(tmpname, index))
            blob_client.upload_blob(tmpfile)

        return jsonify({
            'container': container,
            'blob_list': sorted([x.name for x in container_client.list_blobs()]),
        })


if __name__ == '__main__':
    app.debug = True
    app.run()

