from typing import Dict, Any

import boto3

def create_comprehend_client(boto_kwargs: Dict[str, Any]):
    return boto3.client("comprehendmedical", **boto_kwargs)

def analyze_text(client, text: str) -> Dict[str, Any]:
    return client.detect_entities_v2(Text=text)