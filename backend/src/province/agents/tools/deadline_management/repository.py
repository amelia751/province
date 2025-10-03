"""
Deadline Repository

This module provides DynamoDB operations for deadline management including
CRUD operations, queries, and batch operations.
"""

import boto3
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from .models import Deadline, DeadlineStatus, DeadlineType, Priority

logger = logging.getLogger(__name__)


class DeadlineRepository:
    """Repository for deadline DynamoDB operations"""
    
    def __init__(self, table_name: str = "province-deadlines", region_name: str = "us-east-1"):
        self.table_name = table_name
        self.region_name = region_name
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.table = self.dynamodb.Table(table_name)
    
    def create_deadline(self, deadline: Deadline) -> bool:
        """
        Create a new deadline in DynamoDB
        
        Args:
            deadline: Deadline object to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update timestamps
            deadline.created_at = datetime.utcnow()
            deadline.updated_at = datetime.utcnow()
            deadline.update_status()
            
            # Convert to DynamoDB item
            item = deadline.to_dict()
            
            # Add GSI keys for efficient querying
            item['matter_id_status'] = f"{deadline.matter_id}#{deadline.status.value}"
            item['due_date_sort'] = deadline.due_date.isoformat()
            item['status_due_date'] = f"{deadline.status.value}#{deadline.due_date.isoformat()}"
            
            # Put item with condition to prevent overwrites
            self.table.put_item(
                Item=item,
                ConditionExpression=Attr('deadline_id').not_exists()
            )
            
            logger.info(f"Created deadline: {deadline.deadline_id}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.error(f"Deadline already exists: {deadline.deadline_id}")
            else:
                logger.error(f"Error creating deadline: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating deadline: {str(e)}")
            return False
    
    def get_deadline(self, deadline_id: str) -> Optional[Deadline]:
        """
        Get a deadline by ID
        
        Args:
            deadline_id: ID of the deadline to retrieve
            
        Returns:
            Deadline object if found, None otherwise
        """
        try:
            response = self.table.get_item(
                Key={'deadline_id': deadline_id}
            )
            
            if 'Item' in response:
                return Deadline.from_dict(response['Item'])
            else:
                logger.warning(f"Deadline not found: {deadline_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting deadline {deadline_id}: {str(e)}")
            return None
    
    def update_deadline(self, deadline: Deadline) -> bool:
        """
        Update an existing deadline
        
        Args:
            deadline: Updated deadline object
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update timestamp and status
            deadline.updated_at = datetime.utcnow()
            deadline.update_status()
            
            # Convert to DynamoDB item
            item = deadline.to_dict()
            
            # Update GSI keys
            item['matter_id_status'] = f"{deadline.matter_id}#{deadline.status.value}"
            item['due_date_sort'] = deadline.due_date.isoformat()
            item['status_due_date'] = f"{deadline.status.value}#{deadline.due_date.isoformat()}"
            
            # Update item with condition to ensure it exists
            self.table.put_item(
                Item=item,
                ConditionExpression=Attr('deadline_id').exists()
            )
            
            logger.info(f"Updated deadline: {deadline.deadline_id}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.error(f"Deadline does not exist: {deadline.deadline_id}")
            else:
                logger.error(f"Error updating deadline: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating deadline: {str(e)}")
            return False
    
    def delete_deadline(self, deadline_id: str) -> bool:
        """
        Delete a deadline
        
        Args:
            deadline_id: ID of the deadline to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.table.delete_item(
                Key={'deadline_id': deadline_id},
                ConditionExpression=Attr('deadline_id').exists()
            )
            
            logger.info(f"Deleted deadline: {deadline_id}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.error(f"Deadline does not exist: {deadline_id}")
            else:
                logger.error(f"Error deleting deadline: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting deadline: {str(e)}")
            return False
    
    def get_deadlines_by_matter(self, matter_id: str, status: Optional[DeadlineStatus] = None) -> List[Deadline]:
        """
        Get all deadlines for a matter
        
        Args:
            matter_id: ID of the matter
            status: Optional status filter
            
        Returns:
            List of deadline objects
        """
        try:
            if status:
                # Query by matter_id and status using GSI
                response = self.table.query(
                    IndexName='matter-status-index',
                    KeyConditionExpression=Key('matter_id_status').eq(f"{matter_id}#{status.value}")
                )
            else:
                # Query by matter_id using GSI
                response = self.table.query(
                    IndexName='matter-index',
                    KeyConditionExpression=Key('matter_id').eq(matter_id)
                )
            
            deadlines = []
            for item in response['Items']:
                deadlines.append(Deadline.from_dict(item))
            
            # Sort by due date
            deadlines.sort(key=lambda d: d.due_date)
            
            logger.info(f"Retrieved {len(deadlines)} deadlines for matter {matter_id}")
            return deadlines
            
        except Exception as e:
            logger.error(f"Error getting deadlines for matter {matter_id}: {str(e)}")
            return []
    
    def get_upcoming_deadlines(self, days_ahead: int = 30) -> List[Deadline]:
        """
        Get deadlines due within the specified number of days
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of upcoming deadlines
        """
        try:
            end_date = datetime.utcnow() + timedelta(days=days_ahead)
            
            # Query active deadlines using GSI
            response = self.table.query(
                IndexName='status-due-date-index',
                KeyConditionExpression=Key('status_due_date').begins_with('active#'),
                FilterExpression=Attr('due_date').lte(end_date.isoformat())
            )
            
            deadlines = []
            for item in response['Items']:
                deadline = Deadline.from_dict(item)
                if deadline.due_date <= end_date:
                    deadlines.append(deadline)
            
            # Sort by due date
            deadlines.sort(key=lambda d: d.due_date)
            
            logger.info(f"Retrieved {len(deadlines)} upcoming deadlines")
            return deadlines
            
        except Exception as e:
            logger.error(f"Error getting upcoming deadlines: {str(e)}")
            return []
    
    def get_overdue_deadlines(self) -> List[Deadline]:
        """
        Get all overdue deadlines
        
        Returns:
            List of overdue deadlines
        """
        try:
            current_time = datetime.utcnow()
            
            # Query active deadlines that are past due
            response = self.table.query(
                IndexName='status-due-date-index',
                KeyConditionExpression=Key('status_due_date').begins_with('active#'),
                FilterExpression=Attr('due_date').lt(current_time.isoformat())
            )
            
            deadlines = []
            for item in response['Items']:
                deadline = Deadline.from_dict(item)
                if deadline.due_date < current_time:
                    # Update status to overdue
                    deadline.status = DeadlineStatus.OVERDUE
                    self.update_deadline(deadline)
                    deadlines.append(deadline)
            
            logger.info(f"Retrieved {len(deadlines)} overdue deadlines")
            return deadlines
            
        except Exception as e:
            logger.error(f"Error getting overdue deadlines: {str(e)}")
            return []
    
    def get_deadlines_needing_reminders(self) -> List[Deadline]:
        """
        Get deadlines that need reminders sent
        
        Returns:
            List of deadlines needing reminders
        """
        try:
            deadlines_needing_reminders = []
            
            # Get active deadlines
            response = self.table.query(
                IndexName='status-due-date-index',
                KeyConditionExpression=Key('status_due_date').begins_with('active#')
            )
            
            current_time = datetime.utcnow()
            
            for item in response['Items']:
                deadline = Deadline.from_dict(item)
                
                # Check if any reminder dates have passed without sending
                for days_before in deadline.reminder_settings.days_before:
                    reminder_date = deadline.due_date - timedelta(days=days_before)
                    
                    # If reminder date has passed and no reminder sent for this interval
                    if reminder_date <= current_time:
                        # Check if reminder already sent for this interval
                        reminder_sent = any(
                            r.get('days_before') == days_before 
                            for r in deadline.reminders_sent
                        )
                        
                        if not reminder_sent:
                            deadlines_needing_reminders.append(deadline)
                            break  # Only add once per deadline
            
            logger.info(f"Found {len(deadlines_needing_reminders)} deadlines needing reminders")
            return deadlines_needing_reminders
            
        except Exception as e:
            logger.error(f"Error getting deadlines needing reminders: {str(e)}")
            return []
    
    def search_deadlines(self, 
                        title_contains: Optional[str] = None,
                        deadline_type: Optional[DeadlineType] = None,
                        priority: Optional[Priority] = None,
                        status: Optional[DeadlineStatus] = None,
                        court_name: Optional[str] = None,
                        limit: int = 50) -> List[Deadline]:
        """
        Search deadlines with various filters
        
        Args:
            title_contains: Search in title
            deadline_type: Filter by deadline type
            priority: Filter by priority
            status: Filter by status
            court_name: Filter by court name
            limit: Maximum number of results
            
        Returns:
            List of matching deadlines
        """
        try:
            # Build filter expression
            filter_expressions = []
            
            if title_contains:
                filter_expressions.append(Attr('title').contains(title_contains))
            
            if deadline_type:
                filter_expressions.append(Attr('deadline_type').eq(deadline_type.value))
            
            if priority:
                filter_expressions.append(Attr('priority').eq(priority.value))
            
            if status:
                filter_expressions.append(Attr('status').eq(status.value))
            
            if court_name:
                filter_expressions.append(Attr('court_name').contains(court_name))
            
            # Combine filter expressions
            filter_expression = None
            if filter_expressions:
                filter_expression = filter_expressions[0]
                for expr in filter_expressions[1:]:
                    filter_expression = filter_expression & expr
            
            # Scan with filters (for complex searches)
            scan_kwargs = {'Limit': limit}
            if filter_expression:
                scan_kwargs['FilterExpression'] = filter_expression
            
            response = self.table.scan(**scan_kwargs)
            
            deadlines = []
            for item in response['Items']:
                deadlines.append(Deadline.from_dict(item))
            
            # Sort by due date
            deadlines.sort(key=lambda d: d.due_date)
            
            logger.info(f"Search returned {len(deadlines)} deadlines")
            return deadlines
            
        except Exception as e:
            logger.error(f"Error searching deadlines: {str(e)}")
            return []
    
    def batch_update_status(self, deadline_ids: List[str], new_status: DeadlineStatus) -> int:
        """
        Batch update status for multiple deadlines
        
        Args:
            deadline_ids: List of deadline IDs to update
            new_status: New status to set
            
        Returns:
            Number of successfully updated deadlines
        """
        updated_count = 0
        
        try:
            for deadline_id in deadline_ids:
                deadline = self.get_deadline(deadline_id)
                if deadline:
                    deadline.status = new_status
                    deadline.updated_at = datetime.utcnow()
                    
                    if self.update_deadline(deadline):
                        updated_count += 1
            
            logger.info(f"Batch updated {updated_count}/{len(deadline_ids)} deadlines to {new_status.value}")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error in batch status update: {str(e)}")
            return updated_count
    
    def get_deadline_statistics(self, matter_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about deadlines
        
        Args:
            matter_id: Optional matter ID to filter by
            
        Returns:
            Dictionary with deadline statistics
        """
        try:
            # Get deadlines
            if matter_id:
                deadlines = self.get_deadlines_by_matter(matter_id)
            else:
                # Get all deadlines (limited scan for performance)
                response = self.table.scan(Limit=1000)
                deadlines = [Deadline.from_dict(item) for item in response['Items']]
            
            # Calculate statistics
            total = len(deadlines)
            by_status = {}
            by_type = {}
            by_priority = {}
            
            overdue_count = 0
            approaching_count = 0
            
            for deadline in deadlines:
                # Status counts
                status = deadline.status.value
                by_status[status] = by_status.get(status, 0) + 1
                
                # Type counts
                dtype = deadline.deadline_type.value
                by_type[dtype] = by_type.get(dtype, 0) + 1
                
                # Priority counts
                priority = deadline.priority.value
                by_priority[priority] = by_priority.get(priority, 0) + 1
                
                # Special conditions
                if deadline.is_overdue:
                    overdue_count += 1
                elif deadline.is_approaching:
                    approaching_count += 1
            
            return {
                'total_deadlines': total,
                'by_status': by_status,
                'by_type': by_type,
                'by_priority': by_priority,
                'overdue_count': overdue_count,
                'approaching_count': approaching_count,
                'matter_id': matter_id
            }
            
        except Exception as e:
            logger.error(f"Error getting deadline statistics: {str(e)}")
            return {}