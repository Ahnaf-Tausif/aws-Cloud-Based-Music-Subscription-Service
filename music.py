import boto3
table_config = {
    'TableName': 'music',
    'KeySchema': [{'AttributeName': 'title', 'KeyType': 'HASH'},
                  {'AttributeName': 'artist', 'KeyType': 'RANGE'}],
    'AttributeDefinitions': [{'AttributeName': 'title', 'AttributeType': 'S'},
                             {'AttributeName': 'artist', 'AttributeType': 'S'}],
    'ProvisionedThroughput': {'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
}

dynamo_resource = boto3.resource('dynamodb')

music_table = dynamo_resource.create_table(**table_config)

music_table.meta.client.get_waiter('table_exists').wait(TableName='music')

print("Table created successfully.")
