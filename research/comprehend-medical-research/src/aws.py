from typing import Dict, Any

import boto3

# A dispatcher to map short names to the actual boto3 client method names.
# This makes the main script cleaner and decouples it from boto3's specifics.
API_DISPATCHER: Dict[str, str] = {
    "entities": "detect_entities_v2",
    "icd10": "infer_icd10_cm",
    "rxnorm": "infer_rx_norm",
    "snomedct": "infer_snomedct",
}


def create_comprehend_client(boto_kwargs: Dict[str, Any]):
    """Creates and returns a boto3 client for AWS Comprehend Medical."""
    return boto3.client("comprehendmedical", **boto_kwargs)


def call_comprehend_api(client: Any, text: str, api_method: str) -> Dict[str, Any]:
    """
    Calls a specified AWS Comprehend Medical API method using the dispatcher.

    :param client: A configured boto3 client for comprehendmedical.
    :param text: The text to analyze.
    :param api_method: The short name of the API to call (e.g., 'entities', 'icd10').
    :return: The response dictionary from the API.
    :raises ValueError: If the api_method is not supported.
    """
    method_name = API_DISPATCHER.get(api_method)
    if not method_name:
        supported_methods = ", ".join(API_DISPATCHER.keys())
        raise ValueError(
            f"Unsupported API method: '{api_method}'. Supported methods are: [{supported_methods}]"
        )

    # Get the actual function (e.g., client.detect_entities_v2) from the client object
    boto_method = getattr(client, method_name)

    # Call the function with the text
    return boto_method(Text=text)