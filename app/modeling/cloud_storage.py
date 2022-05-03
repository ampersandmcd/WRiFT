from google.cloud import storage
from pathlib import Path
import os


def safe_open(filepath):
    """
    Use the local file if it exists, download from cloud storage if it doesn't
    :param filepath: File to look for
    :return: The open binary of the file
    """
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            return f.read()
    else:
        name = Path(filepath).name
        filepath = "data/" + name
        return download_blob("risksforecastingdatastore", filepath)


def download_blob(bucket_name, source_blob_name):
    """Downloads a blob from the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The ID of your GCS object
    # source_blob_name = "storage-object-name"

    # The path to which the file should be downloaded
    # destination_file_name = "local/path/to/file"

    storage_client = storage.Client.create_anonymous_client()

    bucket = storage_client.bucket(bucket_name)

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.blob(source_blob_name)
    return blob.download_as_bytes()

if __name__ == '__main__':
    download_blob("modeling_data_farsite", "data/", "app/test/")
