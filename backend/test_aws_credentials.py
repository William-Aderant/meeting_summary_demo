#!/usr/bin/env python3
"""Test script to verify AWS credentials from .env file work correctly."""
import json
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, BotoCoreError

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings


def test_credentials_loaded():
    """Test that credentials are loaded from .env file."""
    print("=" * 60)
    print("Testing AWS Credentials Loading")
    print("=" * 60)
    
    if not settings.aws_access_key_id:
        print("❌ AWS_ACCESS_KEY_ID not found in .env file")
        return False
    else:
        print(f"✅ AWS_ACCESS_KEY_ID loaded: {settings.aws_access_key_id[:10]}...")
    
    if not settings.aws_secret_access_key:
        print("❌ AWS_SECRET_ACCESS_KEY not found in .env file")
        return False
    else:
        print(f"✅ AWS_SECRET_ACCESS_KEY loaded: {settings.aws_secret_access_key[:10]}...")
    
    if settings.aws_session_token:
        print(f"✅ AWS_SESSION_TOKEN loaded: {settings.aws_session_token[:10]}... (temporary credentials)")
    else:
        print("ℹ️  AWS_SESSION_TOKEN not set (using permanent credentials)")
    
    print(f"✅ AWS_REGION: {settings.aws_region}")
    
    if settings.s3_bucket_name:
        print(f"✅ S3_BUCKET_NAME: {settings.s3_bucket_name}")
    else:
        print("⚠️  S3_BUCKET_NAME not set (optional)")
    
    return True


def test_rekognition():
    """Test AWS Rekognition credentials."""
    print("\n" + "=" * 60)
    print("Testing AWS Rekognition")
    print("=" * 60)
    
    try:
        client_kwargs = {
            'aws_access_key_id': settings.aws_access_key_id,
            'aws_secret_access_key': settings.aws_secret_access_key,
            'region_name': settings.aws_region
        }
        if settings.aws_session_token:
            client_kwargs['aws_session_token'] = settings.aws_session_token
        client = boto3.client('rekognition', **client_kwargs)
        
        # Try to list collections (a simple API call that requires valid credentials)
        try:
            response = client.list_collections(MaxResults=1)
            print("✅ Rekognition credentials are valid")
            print(f"   Found {len(response.get('CollectionIds', []))} collections")
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ['InvalidClientTokenId', 'UnrecognizedClientException']:
                print(f"❌ Rekognition credentials are invalid: {error_code}")
                print(f"   Error: {e}")
                return False
            else:
                # Other errors (like AccessDenied) mean credentials work but permissions might be limited
                print(f"⚠️  Rekognition API call failed (credentials may be valid but permissions limited): {error_code}")
                print(f"   Error: {e}")
                return True  # Credentials are valid, just permissions issue
                
    except Exception as e:
        print(f"❌ Failed to initialize Rekognition client: {e}")
        return False


def test_bedrock():
    """Test AWS Bedrock credentials."""
    print("\n" + "=" * 60)
    print("Testing AWS Bedrock")
    print("=" * 60)
    
    try:
        client_kwargs = {
            'aws_access_key_id': settings.aws_access_key_id,
            'aws_secret_access_key': settings.aws_secret_access_key,
            'region_name': settings.aws_region
        }
        if settings.aws_session_token:
            client_kwargs['aws_session_token'] = settings.aws_session_token
        
        client = boto3.client('bedrock-runtime', **client_kwargs)
        
        # Try to list foundation models (requires valid credentials)
        bedrock_client = boto3.client('bedrock', **client_kwargs)
        
        try:
            response = bedrock_client.list_foundation_models()
            print("✅ Bedrock credentials are valid")
            print(f"   Model ID configured: {settings.bedrock_model_id}")
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ['InvalidClientTokenId', 'UnrecognizedClientException']:
                print(f"❌ Bedrock credentials are invalid: {error_code}")
                print(f"   Error: {e}")
                return False
            else:
                print(f"⚠️  Bedrock API call failed (credentials may be valid but permissions limited): {error_code}")
                print(f"   Error: {e}")
                return True  # Credentials are valid, just permissions issue
                
    except Exception as e:
        print(f"❌ Failed to initialize Bedrock client: {e}")
        return False


def test_s3():
    """Test AWS S3 credentials (if bucket is configured)."""
    if not settings.s3_bucket_name:
        print("\n" + "=" * 60)
        print("Testing AWS S3")
        print("=" * 60)
        print("⚠️  S3_BUCKET_NAME not set, skipping S3 test")
        return None
    
    print("\n" + "=" * 60)
    print("Testing AWS S3")
    print("=" * 60)
    
    try:
        client_kwargs = {
            'aws_access_key_id': settings.aws_access_key_id,
            'aws_secret_access_key': settings.aws_secret_access_key,
            'region_name': settings.aws_region
        }
        if settings.aws_session_token:
            client_kwargs['aws_session_token'] = settings.aws_session_token
        client = boto3.client('s3', **client_kwargs)
        
        # Try to head the bucket (requires valid credentials and bucket access)
        try:
            client.head_bucket(Bucket=settings.s3_bucket_name)
            print(f"✅ S3 credentials are valid and can access bucket: {settings.s3_bucket_name}")
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ['InvalidClientTokenId', 'UnrecognizedClientException']:
                print(f"❌ S3 credentials are invalid: {error_code}")
                print(f"   Error: {e}")
                return False
            elif error_code == '404':
                print(f"❌ S3 bucket not found: {settings.s3_bucket_name}")
                return False
            elif error_code == '403':
                print(f"⚠️  S3 credentials are valid but access denied to bucket: {settings.s3_bucket_name}")
                return True  # Credentials work, just permissions issue
            else:
                print(f"⚠️  S3 API call failed: {error_code}")
                print(f"   Error: {e}")
                return True  # Credentials are valid, just permissions issue
                
    except Exception as e:
        print(f"❌ Failed to initialize S3 client: {e}")
        return False


def main():
    """Run all AWS credential tests."""
    print("\n🔍 AWS Credentials Test Script")
    print("=" * 60)
    print(f"Loading from .env file in: {Path(__file__).parent}")
    print("=" * 60)
    
    # Test 1: Credentials loaded
    if not test_credentials_loaded():
        print("\n❌ FAILED: Credentials not loaded from .env file")
        print("   Please check that .env file exists in the backend directory")
        print("   and contains AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        sys.exit(1)
    
    # Test 2: Rekognition
    rekognition_ok = test_rekognition()
    
    # Test 3: Bedrock
    bedrock_ok = test_bedrock()
    
    # Test 4: S3 (optional)
    s3_ok = test_s3()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Credentials Loaded: {'✅' if True else '❌'}")
    print(f"Rekognition: {'✅' if rekognition_ok else '❌'}")
    print(f"Bedrock: {'✅' if bedrock_ok else '❌'}")
    print(f"S3: {'✅' if s3_ok else '⚠️  (not configured)' if s3_ok is None else '❌'}")
    
    if rekognition_ok and bedrock_ok:
        print("\n✅ All critical AWS services are working!")
        sys.exit(0)
    else:
        print("\n❌ Some AWS services failed. Please check your credentials.")
        sys.exit(1)


if __name__ == "__main__":
    main()

