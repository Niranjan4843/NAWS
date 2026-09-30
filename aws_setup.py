"""
AWS Infrastructure Setup & Cloud Provisioning Helper for Movie Magic.
Creates required DynamoDB Tables (Users, Movies, Bookings) and SNS Notification Topic.
"""

import os
import sys

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("boto3 is not installed. Please install boto3 with `pip install boto3`")
    sys.exit(1)

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

def create_dynamodb_tables():
    dynamodb = boto3.client('dynamodb', region_name=AWS_REGION)
    existing_tables = dynamodb.list_tables()['TableNames']
    
    # 1. Users Table (Partition Key: user_id)
    if 'Users' not in existing_tables:
        print("[AWS Setup] Creating DynamoDB Table 'Users'...")
        dynamodb.create_table(
            TableName='Users',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        print(" -> Table 'Users' creation initiated.")
    else:
        print(" -> Table 'Users' already exists.")

    # 2. Movies Table (Partition Key: movie_id)
    if 'Movies' not in existing_tables:
        print("[AWS Setup] Creating DynamoDB Table 'Movies'...")
        dynamodb.create_table(
            TableName='Movies',
            KeySchema=[{'AttributeName': 'movie_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'movie_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        print(" -> Table 'Movies' creation initiated.")
    else:
        print(" -> Table 'Movies' already exists.")

    # 3. Bookings Table (Partition Key: booking_id)
    if 'Bookings' not in existing_tables:
        print("[AWS Setup] Creating DynamoDB Table 'Bookings'...")
        dynamodb.create_table(
            TableName='Bookings',
            KeySchema=[{'AttributeName': 'booking_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'booking_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        print(" -> Table 'Bookings' creation initiated.")
    else:
        print(" -> Table 'Bookings' already exists.")

def setup_sns_topic():
    sns = boto3.client('sns', region_name=AWS_REGION)
    print("[AWS Setup] Creating SNS Topic 'MovieMagic-BookingNotifications'...")
    response = sns.create_topic(Name='MovieMagic-BookingNotifications')
    topic_arn = response['TopicArn']
    print(f" -> SNS Topic created with ARN: {topic_arn}")
    return topic_arn

if __name__ == "__main__":
    print("=== Movie Magic Cloud Infrastructure Initializer ===")
    try:
        create_dynamodb_tables()
        arn = setup_sns_topic()
        print("\n[SUCCESS] AWS Infrastructure provisioned successfully!")
        print(f"Set environment variables:\nexport USE_AWS_DYNAMODB=true\nexport SNS_TOPIC_ARN={arn}")
    except Exception as e:
        print(f"\n[ERROR] AWS Setup failed: {e}")
