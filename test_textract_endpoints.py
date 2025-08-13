#!/usr/bin/env python3
"""
Test script for AWS Textract endpoints
Tests both ID document analysis and general document analysis
"""

import requests
import json
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_DOCUMENTS = [
    {
        "name": "20250812_143022_a1b2c3d4_cedula.jpg",
        "type": "id_document",
        "description": "Identity document (cédula)"
    },
    {
        "name": "20250812_143022_b1c2d3e4_contrato_page_1.jpg", 
        "type": "general_document",
        "description": "General document (contract page)"
    }
]

def test_textract_id_endpoint():
    """Test the /textract-id/ endpoint"""
    print("🆔 Testing Textract ID Analysis Endpoint")
    print("=" * 50)
    
    for doc in TEST_DOCUMENTS:
        print(f"\n📄 Testing document: {doc['name']}")
        print(f"   Description: {doc['description']}")
        
        # Prepare request
        payload = {
            "document_name": doc["name"],
            "analysis_type": "id_document"
        }
        
        try:
            # Make request
            print("   🔄 Sending request...")
            response = requests.post(
                f"{BASE_URL}/textract-id/",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"   📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Success: {result.get('success', False)}")
                
                if result.get('success'):
                    extracted_fields = result.get('extracted_fields', [])
                    print(f"   📋 Extracted Fields: {len(extracted_fields)}")
                    
                    # Show first few fields
                    for i, field in enumerate(extracted_fields[:3]):
                        print(f"      {i+1}. {field['field_type']}: {field['field_value']} (confidence: {field['field_confidence']:.1f}%)")
                    
                    if len(extracted_fields) > 3:
                        print(f"      ... and {len(extracted_fields) - 3} more fields")
                else:
                    print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP Error: {response.text}")
                
        except requests.RequestException as e:
            print(f"   ❌ Request Error: {str(e)}")
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON Error: {str(e)}")

def test_textract_general_endpoint():
    """Test the /textract-general/ endpoint"""
    print("\n\n📄 Testing Textract General Analysis Endpoint")
    print("=" * 50)
    
    for doc in TEST_DOCUMENTS:
        print(f"\n📄 Testing document: {doc['name']}")
        print(f"   Description: {doc['description']}")
        
        # Prepare request
        payload = {
            "document_name": doc["name"],
            "analysis_type": "general_document"
        }
        
        try:
            # Make request
            print("   🔄 Sending request...")
            response = requests.post(
                f"{BASE_URL}/textract-general/",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"   📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Success: {result.get('success', False)}")
                
                if result.get('success'):
                    summary = result.get('analysis_summary', {})
                    print(f"   📈 Statistics:")
                    print(f"      - Text blocks: {summary.get('total_text_blocks', 0)}")
                    print(f"      - Lines: {summary.get('total_lines', 0)}")
                    print(f"      - Words: {summary.get('total_words', 0)}")
                    print(f"      - Text length: {summary.get('full_text_length', 0)} characters")
                    
                    # Show first few lines
                    lines = result.get('lines', [])
                    if lines:
                        print(f"   📝 First few lines:")
                        for i, line in enumerate(lines[:3]):
                            print(f"      {i+1}. {line[:60]}{'...' if len(line) > 60 else ''}")
                        
                        if len(lines) > 3:
                            print(f"      ... and {len(lines) - 3} more lines")
                else:
                    print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP Error: {response.text}")
                
        except requests.RequestException as e:
            print(f"   ❌ Request Error: {str(e)}")
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON Error: {str(e)}")

def test_endpoint_validation():
    """Test endpoint validation with invalid data"""
    print("\n\n🧪 Testing Endpoint Validation")
    print("=" * 50)
    
    invalid_requests = [
        {
            "name": "Empty document name",
            "payload": {"document_name": ""},
            "endpoint": "textract-id"
        },
        {
            "name": "Invalid file extension",
            "payload": {"document_name": "test.txt"},
            "endpoint": "textract-id"
        },
        {
            "name": "Missing document name",
            "payload": {"analysis_type": "id_document"},
            "endpoint": "textract-general"
        }
    ]
    
    for test_case in invalid_requests:
        print(f"\n🔍 Testing: {test_case['name']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/{test_case['endpoint']}/",
                json=test_case['payload'],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"   📊 Status Code: {response.status_code}")
            
            if response.status_code == 400:
                result = response.json()
                print(f"   ✅ Validation working: {result.get('error', 'Validation error')}")
            else:
                print(f"   ⚠️  Unexpected status: {response.status_code}")
                
        except requests.RequestException as e:
            print(f"   ❌ Request Error: {str(e)}")

def check_service_health():
    """Check if the service is running"""
    print("🏥 Checking Service Health")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/health/", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Service is running: {result.get('message', 'OK')}")
            print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
            return True
        else:
            print(f"❌ Service health check failed: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Service is not accessible: {str(e)}")
        print(f"   Make sure Django server is running on {BASE_URL}")
        return False

def main():
    """Run all tests"""
    print("🚀 AWS Textract Endpoints Test Suite")
    print("=" * 60)
    
    # Check service health first
    if not check_service_health():
        print("\n❌ Service is not available. Please start Django server first:")
        print("   python manage.py runserver")
        return
    
    print(f"\n🔗 Testing endpoints on: {BASE_URL}")
    print(f"📄 Test documents: {len(TEST_DOCUMENTS)} files")
    
    # Run tests
    test_textract_id_endpoint()
    test_textract_general_endpoint()
    test_endpoint_validation()
    
    print("\n\n🎉 Test Suite Completed!")
    print("=" * 60)
    print("💡 Tips:")
    print("   - Make sure test documents exist in your S3 bucket")
    print("   - Check AWS credentials are configured correctly")
    print("   - Verify bucket permissions allow Textract access")
    print("   - Use /upload/ endpoint to upload test documents first")

if __name__ == "__main__":
    main()
