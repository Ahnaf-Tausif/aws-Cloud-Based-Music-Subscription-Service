import boto3
import requests
import os
import json
from botocore.exceptions import NoCredentialsError

s3_client = boto3.client('s3')
bucket = 'artistimagesbucket'

with open('a1.json', mode='r') as data_file:
    track_data = json.load(data_file)['songs']

def process_images(tracks):
    for track in tracks:
        image_url = track['img_url']
        local_filename = image_url.split('/')[-1]

        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            with open(local_filename, 'wb') as image_file:
                image_file.write(image_response.content)

            try:
                s3_client.upload_file(local_filename, bucket, local_filename)
                print(f"Uploaded {local_filename} to S3 bucket {bucket}")
            except NoCredentialsError:
                print("No valid credentials available.")
            except Exception as error:
                print(f"Failed to upload {local_filename}: {error}")
            finally:
                os.remove(local_filename)
        else:
            print(f"Could not download image from {image_url}")

process_images(track_data)
