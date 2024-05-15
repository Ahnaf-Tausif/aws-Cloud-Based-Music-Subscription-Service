import boto3
import json

json_source = 'a1.json'
table_name = 'music'

with open(json_source, mode='r') as json_file:
    songs_data = json.load(json_file)['songs']

dynamo_resource = boto3.resource('dynamodb')
music_table = dynamo_resource.Table(table_name)

with music_table.batch_writer() as batch_writer:
    for song in songs_data:
        batch_writer.put_item(Item=song)

print("Data successfully uploaded to DynamoDB.")

