"""
AWS Lambda function to provide notifications API for the frontend.

This function allows the frontend to poll for document processing notifications
and real-time updates about the status of uploaded documents.
"""

import json
import logging
import boto3
from typing import Dict, Any, List
import os
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda handler for notifications API.
    
    Supports:
    - GET /notifications/{engagement_id} - Get notifications for an engagement
    - POST /notifications/{engagement_id}/mark-read - Mark notifications as read
    
    Args:
        event: API Gateway event
        context: Lambda context
    
    Returns:
        API Gateway response
    """
    logger.info(f"Received event: {json.dumps(event, indent=2)}")
    
    try:
        # Parse request
        http_method = event.get('httpMethod', 'GET')
        path_parameters = event.get('pathParameters', {})
        engagement_id = path_parameters.get('engagement_id')
        
        if not engagement_id:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'engagement_id is required'})
            }
        
        if http_method == 'GET':
            return get_notifications(engagement_id, event)
        elif http_method == 'POST':
            return mark_notifications_read(engagement_id, event)
        else:
            return {
                'statusCode': 405,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Method not allowed'})
            }
            
    except Exception as e:
        logger.error(f"API handler error: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

def get_notifications(engagement_id: str, event: Dict) -> Dict[str, Any]:
    """
    Get notifications for an engagement.
    
    Query parameters:
    - since: timestamp to get notifications since (optional)
    - limit: max number of notifications (default 50)
    - status: filter by status (optional)
    """
    try:
        query_params = event.get('queryStringParameters') or {}
        since_timestamp = query_params.get('since')
        limit = int(query_params.get('limit', 50))
        status_filter = query_params.get('status')
        
        dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        table = dynamodb.Table(os.getenv('NOTIFICATIONS_TABLE', 'province-chat-notifications'))
        
        # Build query parameters
        query_kwargs = {
            'KeyConditionExpression': boto3.dynamodb.conditions.Key('engagement_id').eq(engagement_id),
            'ScanIndexForward': False,  # Most recent first
            'Limit': limit
        }
        
        # Add timestamp filter if provided
        if since_timestamp:
            query_kwargs['KeyConditionExpression'] = query_kwargs['KeyConditionExpression'] & \
                boto3.dynamodb.conditions.Key('timestamp').gt(int(since_timestamp))
        
        # Add status filter if provided
        if status_filter:
            query_kwargs['FilterExpression'] = boto3.dynamodb.conditions.Attr('status').eq(status_filter)
        
        response = table.query(**query_kwargs)
        
        notifications = []
        for item in response.get('Items', []):
            # Convert Decimal to float for JSON serialization
            notification = convert_decimals(item)
            notifications.append(notification)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'notifications': notifications,
                'count': len(notifications),
                'engagement_id': engagement_id
            })
        }
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

def mark_notifications_read(engagement_id: str, event: Dict) -> Dict[str, Any]:
    """
    Mark notifications as read.
    
    Body should contain:
    - timestamps: list of timestamps to mark as read
    """
    try:
        body = json.loads(event.get('body', '{}'))
        timestamps = body.get('timestamps', [])
        
        if not timestamps:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'timestamps array is required'})
            }
        
        dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        table = dynamodb.Table(os.getenv('NOTIFICATIONS_TABLE', 'province-chat-notifications'))
        
        updated_count = 0
        
        for timestamp in timestamps:
            try:
                table.update_item(
                    Key={
                        'engagement_id': engagement_id,
                        'timestamp': int(timestamp)
                    },
                    UpdateExpression='SET #read = :read, #read_at = :read_at',
                    ExpressionAttributeNames={
                        '#read': 'read',
                        '#read_at': 'read_at'
                    },
                    ExpressionAttributeValues={
                        ':read': True,
                        ':read_at': int(context.aws_request_id.split('-')[0], 16)  # Use request ID as timestamp
                    }
                )
                updated_count += 1
            except Exception as e:
                logger.warning(f"Failed to mark notification {timestamp} as read: {e}")
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': f'Marked {updated_count} notifications as read',
                'updated_count': updated_count
            })
        }
        
    except Exception as e:
        logger.error(f"Error marking notifications as read: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

def convert_decimals(obj):
    """Convert DynamoDB Decimal objects to float for JSON serialization."""
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj

def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers for API responses."""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
    }
