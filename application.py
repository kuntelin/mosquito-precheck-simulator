import os
from datetime import datetime
from flask import Flask, request, abort, jsonify


app = Flask(__name__)


def version():
    stat = os.stat(__file__)
    return datetime.utcfromtimestamp(stat.st_mtime).strftime('%Y%m%d.%H%M')


def blob_connection_string():
    try:
        return os.environ['BLOB_CONNECTION_STRING']
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
BLOB_CONNECTION_STRING: {}
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


@app.route('/container', methods=['GET'])
def container():
    if request.method == 'GET':
        'list container'
        try:
            client = get_blob_client()
        except Exception as e:
            return e.args[0]

        return jsonify(client.list_containers())


if __name__ == '__main__':
    app.debug = True
    app.run()

