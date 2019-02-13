#
# Copyright (C) 2019 Red Hat, Inc
# see the LICENSE file for license
#
import logging
import os
from tempfile import NamedTemporaryFile, TemporaryDirectory
import zipfile

from flask import Blueprint, jsonify, current_app, request

from .constants import (
    ALLOWED_EXTENSIONS,
    DEFAULT_ZIPFILE_MAX_UNCOMPRESSED_SIZE,
)
from .errors import OMPSUploadedFileError, OMPSExpectedFileError

logger = logging.getLogger(__name__)
BLUEPRINT = Blueprint('push', __name__)


def validate_allowed_extension(filename):
    """Check file extension"""
    if '.' in filename:
        extension = filename.rsplit('.', 1)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise OMPSUploadedFileError(
                'Uploaded file extension "{}" is not allowed'.format(extension)
            )


def extract_zip_file(req, target_dir,
                     max_uncompressed_size=DEFAULT_ZIPFILE_MAX_UNCOMPRESSED_SIZE):
    """Function store uploaded file in target_directory

    :param req: Flask request object
    :param target_dir: directory where file will be stored
    :param max_uncompressed_size: size in Bytes how big data can be accepted
        after uncompressing
    """
    assert req.method == 'POST'
    if 'file' not in req.files:
        raise OMPSExpectedFileError('No "file" in upload')
    file = req.files['file']
    if not file.filename:
        raise OMPSExpectedFileError('No selected "file" in upload')

    validate_allowed_extension(file.filename)

    with NamedTemporaryFile('w', suffix='.zip', dir=target_dir) as tmpf:
        file.save(tmpf.name)
        archive = zipfile.ZipFile(tmpf.name)
        if logger.isEnabledFor(logging.DEBUG):
            # log content of zipfile
            logger.debug(
                'Content of uploaded zip archive "%s":\n%s',
                file.filename, '\n'.join(
                    "name={zi.filename}, compress_size={zi.compress_size}, "
                    "file_size={zi.file_size}".format(zi=zipinfo)
                    for zipinfo in archive.filelist
                )
            )

        uncompressed_size = sum(zi.file_size for zi in archive.filelist)
        if uncompressed_size > max_uncompressed_size:
            raise OMPSUploadedFileError(
                "Uncompressed archive may reach max size limit "
                "({}B>{}B)".format(
                    uncompressed_size, max_uncompressed_size
                ))

        bad_file = archive.testzip()
        if bad_file is not None:
            raise OMPSUploadedFileError(
                "CRC check failed for file {} in archive".format(bad_file)
            )
        archive.extractall(target_dir)
        archive.close()


@BLUEPRINT.route("/<organization>/<repo>/zipfile", methods=('POST',))
def push_zipfile(organization, repo):
    """
    Push operator manifest to registry from uploaded zipfile

    :param organization: quay.io organization
    :param repo: target repository
    """
    data = {
        'organization': organization,
        'repo': repo,
        'msg': 'Not Implemented. Testing only'
    }

    with TemporaryDirectory() as tmpdir:
        max_size = current_app.config.get(
            'ZIPFILE_MAX_UNCOMPRESSED_SIZE',
            DEFAULT_ZIPFILE_MAX_UNCOMPRESSED_SIZE
        )
        extract_zip_file(request, tmpdir,
                         max_uncompressed_size=max_size)
        data['extracted_files'] = os.listdir(tmpdir)
    resp = jsonify(data)
    resp.status_code = 200
    return resp


@BLUEPRINT.route("/<organization>/<repo>/koji/<nvr>", methods=('POST',))
def push_koji_nvr(organization, repo, nvr):
    """
    Get operator manifest from koji by specified NVR and upload operator
    manifest to registry
    :param organization: quay.io organization
    :param repo: target repository
    :param nvr: image NVR from koji
    """
    data = {
        'organization': organization,
        'repo': repo,
        'nvr': nvr,
        'msg': 'Not Implemented. Testing only'
    }
    resp = jsonify(data)
    resp.status_code = 200
    return resp
