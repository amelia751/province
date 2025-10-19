#!/usr/bin/env python3
"""
Test to see if ingest_documents is making multiple Bedrock calls,
which could be causing the throttling when called by the agent.
"""

import asyncio
import sys
import time
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, '/Users/anhlam/province/backend/src')

class BedrockCallMonitor:
    def __init__(self):
        self.call_count = 0
        self.call_times = []
        
    def log_call(self, service, operation):
        self.call_count += 1
        self.call_times.append({
            'timestamp': datetime.now(),
            'service': service,
            'operation': operation
        })
        print(f"🔍 Bedrock call #{self.call_count}: {service}.{operation} at {datetime.now()}")

async def test_ingest_documents_bedrock_usage():
    """Test how many Bedrock calls ingest_documents makes"""
    print("🔍 TESTING INGEST_DOCUMENTS BEDROCK USAGE")
    print("=" * 60)
    
    monitor = BedrockCallMonitor()
    
    # Monkey patch boto3 to monitor Bedrock calls
    import boto3
    original_client = boto3.client
    
    def monitored_client(service_name, **kwargs):
        client = original_client(service_name, **kwargs)
        
        if 'bedrock' in service_name:
            # Wrap the client's methods to monitor calls
            original_make_api_call = client._make_api_call
            
            def monitored_make_api_call(operation_name, api_params):
                monitor.log_call(service_name, operation_name)
                return original_make_api_call(operation_name, api_params)
            
            client._make_api_call = monitored_make_api_call
        
        return client
    
    # Apply the monkey patch
    boto3.client = monitored_client
    
    try:
        print("📝 Starting ingest_documents test...")
        start_time = time.time()
        
        from province.agents.tax.tools.ingest_documents import ingest_documents
        
        # Test with the uploaded W-2
        result = await ingest_documents(
            s3_key="tax-engagements/ea3b3a4f-c877-4d29-bd66-2cff2aa77476/chat-uploads/W2_XL_input_clean_1000.pdf",
            taxpayer_name="April Hensley",
            tax_year=2024,
            document_type="W-2"
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n📊 INGEST_DOCUMENTS ANALYSIS:")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Total Bedrock calls: {monitor.call_count}")
        print(f"   Success: {result.get('success', False)}")
        
        if monitor.call_count > 0:
            print(f"\n🔍 BEDROCK CALL BREAKDOWN:")
            for i, call in enumerate(monitor.call_times, 1):
                print(f"   {i}. {call['service']}.{call['operation']} at {call['timestamp']}")
            
            # Check call frequency
            if len(monitor.call_times) > 1:
                intervals = []
                for i in range(1, len(monitor.call_times)):
                    interval = (monitor.call_times[i]['timestamp'] - monitor.call_times[i-1]['timestamp']).total_seconds()
                    intervals.append(interval)
                
                avg_interval = sum(intervals) / len(intervals)
                min_interval = min(intervals)
                
                print(f"\n⏱️  CALL TIMING ANALYSIS:")
                print(f"   Average interval: {avg_interval:.2f} seconds")
                print(f"   Minimum interval: {min_interval:.2f} seconds")
                
                if min_interval < 1.0:
                    print(f"   ⚠️  POTENTIAL THROTTLING RISK: Calls less than 1 second apart!")
                if monitor.call_count > 5:
                    print(f"   ⚠️  HIGH CALL VOLUME: {monitor.call_count} calls in {duration:.2f} seconds")
        
        return monitor.call_count
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return -1
    
    finally:
        # Restore original boto3.client
        boto3.client = original_client

async def test_calc_1040_bedrock_usage():
    """Test how many Bedrock calls calc_1040 makes"""
    print("\n🔍 TESTING CALC_1040 BEDROCK USAGE")
    print("=" * 60)
    
    monitor = BedrockCallMonitor()
    
    # Same monitoring setup
    import boto3
    original_client = boto3.client
    
    def monitored_client(service_name, **kwargs):
        client = original_client(service_name, **kwargs)
        
        if 'bedrock' in service_name:
            original_make_api_call = client._make_api_call
            
            def monitored_make_api_call(operation_name, api_params):
                monitor.log_call(service_name, operation_name)
                return original_make_api_call(operation_name, api_params)
            
            client._make_api_call = monitored_make_api_call
        
        return client
    
    boto3.client = monitored_client
    
    try:
        print("📝 Starting calc_1040 test...")
        start_time = time.time()
        
        from province.agents.tax.tools.calc_1040 import calc_1040
        
        result = await calc_1040(
            engagement_id="ea3b3a4f-c877-4d29-bd66-2cff2aa77476",
            filing_status="S",
            dependents_count=0
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n📊 CALC_1040 ANALYSIS:")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Total Bedrock calls: {monitor.call_count}")
        print(f"   Success: {result.get('success', False)}")
        
        if monitor.call_count > 0:
            print(f"\n🔍 BEDROCK CALL BREAKDOWN:")
            for i, call in enumerate(monitor.call_times, 1):
                print(f"   {i}. {call['service']}.{call['operation']} at {call['timestamp']}")
        
        return monitor.call_count
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return -1
    
    finally:
        boto3.client = original_client

async def main():
    """Main test runner"""
    print("🎯 GOAL: Identify which tools are making Bedrock calls")
    print("   Hypothesis: ingest_documents makes multiple Bedrock Data Automation calls")
    print("   This could cause throttling when the agent calls it")
    print()
    
    # Test ingest_documents
    ingest_calls = await test_ingest_documents_bedrock_usage()
    
    # Test calc_1040
    calc_calls = await test_calc_1040_bedrock_usage()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print(f"   ingest_documents Bedrock calls: {ingest_calls}")
    print(f"   calc_1040 Bedrock calls: {calc_calls}")
    
    total_calls = (ingest_calls if ingest_calls > 0 else 0) + (calc_calls if calc_calls > 0 else 0)
    
    if total_calls > 10:
        print(f"\n⚠️  HIGH BEDROCK USAGE DETECTED!")
        print(f"   Total calls: {total_calls}")
        print(f"   When the agent calls these tools, it adds to the Bedrock quota")
        print(f"   Agent call + Tool calls = Throttling risk")
    elif total_calls > 5:
        print(f"\n⚠️  MODERATE BEDROCK USAGE")
        print(f"   Total calls: {total_calls}")
        print(f"   Could contribute to throttling under load")
    else:
        print(f"\n✅ LOW BEDROCK USAGE")
        print(f"   Total calls: {total_calls}")
        print(f"   Tools are not the primary cause of throttling")

if __name__ == "__main__":
    asyncio.run(main())
