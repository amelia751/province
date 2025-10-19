#!/usr/bin/env python3
"""
Quick test script for the automated document processing pipeline.
Run this to verify all components are working correctly.
"""

import asyncio
import json
import requests
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
TEST_ENGAGEMENT_ID = "test-engagement-final"

def test_backend_health():
    """Test backend health endpoint."""
    print("🏥 Testing backend health...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/health/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend healthy: {data.get('status')} - {data.get('environment')}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_notifications_api():
    """Test document notifications API."""
    print("🔔 Testing notifications API...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/documents/notifications/{TEST_ENGAGEMENT_ID}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Notifications API working: {data.get('count')} notifications")
            return True
        else:
            print(f"❌ Notifications API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Notifications API error: {e}")
        return False

def test_simulation_api():
    """Test document processing simulation."""
    print("🔄 Testing processing simulation...")
    try:
        # This endpoint doesn't expect a JSON body, just the engagement_id in the path
        response = requests.post(
            f"{BACKEND_URL}/api/v1/documents/notifications/{TEST_ENGAGEMENT_ID}/simulate-processing"
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('processing_result', {})
            print(f"✅ Simulation working: {result.get('document_type')} - ${result.get('total_wages', 0):,.2f}")
            return True
        else:
            print(f"❌ Simulation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Simulation error: {e}")
        return False

def test_agent_stats():
    """Test agent stats endpoint."""
    print("🤖 Testing agent stats...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/agents/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Agent stats working: {len(data.get('agents', []))} agents available")
            return True
        else:
            print(f"❌ Agent stats failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Agent stats error: {e}")
        return False

def test_tax_engagements():
    """Test tax engagements API."""
    print("📋 Testing tax engagements...")
    try:
        # Test GET
        response = requests.get(f"{BACKEND_URL}/api/v1/tax-engagements?user_id=test-user&tax_year=2024")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Tax engagements GET working: {len(data.get('engagements', []))} engagements")
            return True
        else:
            print(f"❌ Tax engagements failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Tax engagements error: {e}")
        return False

def run_all_tests():
    """Run all backend tests."""
    print("🧪 Starting Backend Pipeline Tests")
    print("=" * 50)
    
    tests = [
        ("Backend Health", test_backend_health),
        ("Notifications API", test_notifications_api),
        ("Processing Simulation", test_simulation_api),
        ("Agent Stats", test_agent_stats),
        ("Tax Engagements", test_tax_engagements),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📝 Running: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Backend pipeline is ready.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
