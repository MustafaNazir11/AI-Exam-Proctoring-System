#!/usr/bin/env python3
"""
Azure Face API Setup Script
Run this to configure your Azure Face API credentials
"""

import os

def setup_azure_credentials():
    print("🔧 Azure Face API Setup")
    print("=" * 40)
    
    # Get API key
    api_key = input("Enter your Azure Face API Key: ").strip()
    if not api_key:
        print("❌ API key is required!")
        return False
    
    # Get endpoint
    print("\nEnter your Azure Face API Endpoint")
    print("Example: https://your-region.api.cognitive.microsoft.com/")
    endpoint = input("Endpoint: ").strip()
    if not endpoint:
        endpoint = "https://your-region.api.cognitive.microsoft.com/"
    
    # Create .env file
    env_content = f"""# Azure Face API Configuration
AZURE_FACE_API_KEY={api_key}
AZURE_FACE_ENDPOINT={endpoint}

# Cloudinary Configuration (update these too)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("\n✅ Configuration saved to .env file")
    
    # Test the connection
    print("\n🧪 Testing Azure Face API connection...")
    try:
        from utils.azure_face_api import init_azure_face_detector
        detector = init_azure_face_detector(api_key, endpoint)
        if detector:
            print("✅ Azure Face API connection successful!")
            return True
        else:
            print("❌ Failed to connect to Azure Face API")
            return False
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False

if __name__ == "__main__":
    success = setup_azure_credentials()
    if success:
        print("\n🚀 Setup complete! You can now run the application with Azure Face API support.")
    else:
        print("\n⚠️ Setup incomplete. Please check your credentials and try again.")