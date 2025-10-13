import json, os, base64, uuid, requests
from io import BytesIO

# NVIDIA VILA VLM Configuration
VILA_INVOKE_URL = "https://ai.api.nvidia.com/v1/vlm/nvidia/vila"
NVCF_ASSET_URL = "https://api.nvcf.nvidia.com/v2/nvcf/assets"
API_KEY = os.environ.get("NIM_API_KEY")


def _upload_asset(image_data: bytes, mime_type: str, description: str = "Document image for parsing") -> str:
    """Upload image asset to NVCF and return asset_id."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "accept": "application/json",
    }
    
    # Request upload URL
    authorize = requests.post(
        NVCF_ASSET_URL,
        headers=headers,
        json={"contentType": mime_type, "description": description},
        timeout=30,
    )
    authorize.raise_for_status()
    authorize_res = authorize.json()
    
    # Upload the actual image data
    response = requests.put(
        authorize_res["uploadUrl"],
        data=image_data,
        headers={
            "x-amz-meta-nvcf-asset-description": description,
            "content-type": mime_type,
        },
        timeout=300,
    )
    response.raise_for_status()
    
    asset_id = authorize_res["assetId"]
    print(f"[VILA] Uploaded asset {asset_id}")
    return asset_id


def _delete_asset(asset_id: str):
    """Delete asset from NVCF."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }
    response = requests.delete(
        f"{NVCF_ASSET_URL}/{asset_id}",
        headers=headers,
        timeout=30
    )
    response.raise_for_status()
    print(f"[VILA] Deleted asset {asset_id}")


def parse_page_markdown_bbox(image_b64: str):
    """
    Parse document image using NVIDIA VILA VLM.
    Handles asset upload/deletion workflow required by VILA.
    """
    asset_id = None
    try:
        # Extract image data from base64 string
        if image_b64.startswith('data:image/'):
            # Remove data URL prefix
            header, encoded = image_b64.split(',', 1)
            image_data = base64.b64decode(encoded)
            # Determine mime type from header
            if 'png' in header:
                mime_type = "image/png"
            elif 'jpeg' in header or 'jpg' in header:
                mime_type = "image/jpeg"
            else:
                mime_type = "image/png"  # default
        else:
            # Assume it's raw base64
            image_data = base64.b64decode(image_b64)
            mime_type = "image/png"
        
        # Upload asset to NVCF
        asset_id = _upload_asset(image_data, mime_type)
        
        # Build message with asset reference
        media_content = f'<img src="data:{mime_type};asset_id,{asset_id}" />'
        messages = [
            {
                "role": "user",
                "content": f"Extract all text from this document image. Return the text blocks in order, preserving the layout and structure. {media_content}",
            }
        ]
        
        # Call VILA API
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "NVCF-INPUT-ASSET-REFERENCES": asset_id,
            "NVCF-FUNCTION-ASSET-IDS": asset_id,
            "Accept": "application/json",
        }
        
        payload = {
            "max_tokens": 4096,
            "temperature": 0.2,
            "top_p": 0.7,
            "messages": messages,
            "stream": False,
            "model": "nvidia/vila",
        }
        
        response = requests.post(VILA_INVOKE_URL, headers=headers, json=payload, stream=False)
        response.raise_for_status()
        result = response.json()
        
        # Extract text from response
        text_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Return in structured format
        return {
            "blocks": [{
                "text": text_content,
                "type": "text",
                "bbox": None
            }]
        }
        
    except Exception as e:
        # Fallback: return error info but don't crash
        print(f"[VILA WARNING] Parse failed: {e}")
        return {
            "blocks": [{
                "text": "",
                "type": "text",
                "bbox": None,
                "error": str(e)
            }]
        }
    finally:
        # Always clean up the asset
        if asset_id:
            try:
                _delete_asset(asset_id)
            except Exception as cleanup_error:
                print(f"[VILA WARNING] Failed to delete asset {asset_id}: {cleanup_error}")
