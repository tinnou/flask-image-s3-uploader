__author__ = 'antoine.boyer'

from urllib.parse import quote_plus
import os, hashlib, tempfile
from flask import request, jsonify, make_response, Response
from werkzeug.utils import secure_filename
from mimetypes import MimeTypes
import urllib.request
from utils import make_json_app, hashfile, id_generator
from image_uploader.exceptions.Exceptions import UploadToS3Exception, FileNotAllowedException, \
    S3ObjectNotFoundException
from boto.s3.connection import *

UPLOAD_FOLDER = '/Users/antoine.boyer/Desktop/images/'
AWS_ACCESS_KEY = 'AKIAICBNCWN5UXPOVFFA'
AWS_SECRET_KEY = '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'
S3_BUCKET = 'tradesy-image-code-project'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = make_json_app(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['AWS_ACCESS_KEY'] = AWS_ACCESS_KEY
app.config['AWS_SECRET_KEY'] = AWS_SECRET_KEY
app.config['S3_BUCKET'] = S3_BUCKET


# Retrieve (or create) S3 bucket
conn = S3Connection(app.config['AWS_ACCESS_KEY'], app.config['AWS_SECRET_KEY'])
bucket = conn.create_bucket(app.config['S3_BUCKET'])


def generate_unique_filename(user_filename, md5):
    # TODO : generate hash  + filename + timestamp - random string
    # time in milliseconds
    now = time.time()
    # random string
    random_str = id_generator(10)
    # hopefully unique filename
    return str(time.now) + random_str + user_filename


def upload_file_to_s3(file, unique_filename, md5):
    global bucket
    k = Key(bucket, unique_filename)
    # detect content type
    url = urllib.request.pathname2url(file.filename)
    mime = MimeTypes()
    mime_type = mime.guess_type(url, False)
    app.logger.info("Mime type detected %s" % (mime_type,))
    # set content-type for s3
    k.set_metadata("Content-Type", mime_type[0])
    # send file to S3 if not exist already
    bytes_written = k.set_contents_from_file(file, None, False, None, 10, None, None, False, None, False, None, True)
    # key already exists
    if bytes_written is None:
        return False
    # if bytes_written <= 0:
    #     return False
    k.close()
    return True


def retrieve_file_from_s3(filename):
    global bucket
    k = Key(bucket, filename)
    # creates a temporary file on the filesystem
    file = tempfile.NamedTemporaryFile('w+b', -1, None, None, "", "/tmp/tradesy-", None, False)
    # get file from S3 and write to temp file
    k.get_contents_to_file(file)
    if file is None:
        return False
    return file


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/image', methods=['POST'])
def upload_file():
    # init the resp object
    response = {"success": False, "imageId": None}

    # get file from request
    file = request.files['file']

    # validate
    if not file or not allowed_file(file.filename):
        raise FileNotAllowedException("File not allowed to be uploaded | transfer error", 400, response)
    filename = secure_filename(file.filename)

    # create md5 from file
    md5 = hashfile(file, hashlib.sha256())
    app.logger.info("MD5 of file %s is %s", filename, md5)
    success = False
    failure_counter = 0

    #retry 3x if fails
    while not success and failure_counter <= 3:
        # create unique key
        candidate = generate_unique_filename(filename, md5)
        app.logger.info("Unique filename proposed %s", candidate)
        # attempt upload to s3
        success = upload_file_to_s3(file, candidate, md5)
        failure_counter += 1

    if failure_counter > 3:
        # logically this exception should never be thrown, the entropy level should be good enough
        # (if it's not sufficient we can still use object versioning to serve as a the ID collision mitigator like in a hash table)
        raise UploadToS3Exception("Couldn't find a unique filename after 3 tries, upload failed", 500, response)

    response["imageId"] = candidate
    app.logger.info("imageIdUrlEncoded %s", quote_plus(candidate))
    response["imageIdUrlEncoded"] = quote_plus(candidate)
    response["success"] = success
    return jsonify(response)


@app.route('/image/<filename>', methods=['GET'])
def download_file(filename):
    # fetch file from S3
    try:
        file = retrieve_file_from_s3(filename)
    except S3ResponseError:
        raise S3ObjectNotFoundException("This image doesnt exist", 404)

    app.logger.info("file name %s", file.name)
    # open file locally to read
    with open(file.name, 'rb') as f:
        body = f.read()

    response = make_response(body)
    # This is the key: Set the right header for the response
    # to be downloaded, instead of just printed on the browser
    response.headers["Content-Disposition"] = "attachment; filename="+filename
    response.headers["Content-Type"] = MimeTypes().guess_type(urllib.request.pathname2url(filename))[0]
    response.headers['Content-Length'] = os.path.getsize(file.name)
    return response


# Error handlers


@app.errorhandler(FileNotAllowedException)
def file_not_allowed(error):
    return jsonify(error.to_dict()), error.status_code


@app.errorhandler(UploadToS3Exception)
def upload_to_s3_failed(error):
    return jsonify(error.to_dict()), error.status_code


@app.errorhandler(S3ObjectNotFoundException)
def image_not_found(error):
    return jsonify(error.to_dict()), error.status_code