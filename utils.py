import os
import weaviate

# Weaviate connection
WEAVIATE_HOST = os.getenv('WEAVIATE_HOST', 'weaviate')
WEAVIATE_PORT = os.getenv('WEAVIATE_PORT', 8080)

WEAVIATE_CLOUD_URL = os.getenv('WEAVIATE_CLOUD_URL')
WEAVIATE_CLOUD_API_KEY = os.getenv('WEAVIATE_CLOUD_API_KEY')

def get_local_weaviate_client():
    """Get Weaviate client connection"""
    if not WEAVIATE_HOST or not WEAVIATE_PORT:
        raise RuntimeError(
            "WEAVIATE_HOST and WEAVIATE_PORT must be set to use the local client"
        )
    
    return weaviate.connect_to_local(host=WEAVIATE_HOST, port=WEAVIATE_PORT)

def get_cloud_weaviate_client():
    """Get Weaviate client connection"""
    if not WEAVIATE_CLOUD_URL or not WEAVIATE_CLOUD_API_KEY:
        raise RuntimeError(
            "WEAVIATE_CLOUD_URL and WEAVIATE_CLOUD_API_KEY must be set to use the cloud client"
        )
    
    return weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_CLOUD_URL, 
        auth_credentials=WEAVIATE_CLOUD_API_KEY,
    )