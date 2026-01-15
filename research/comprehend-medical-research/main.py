# main.py
# This script contains the Python prototype for interacting with AWS Comprehend Medical.
# It uses pydantic-settings for configuration management.

import boto3
import json
from typing import Any, Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    aws_access_key_id: Optional[str] = Field(None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field("us-east-1", alias="AWS_REGION")


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_boto_kwargs(self) -> Dict[str, Any]:
        if self.aws_access_key_id and self.aws_secret_access_key:
            return {
                "aws_access_key_id": self.aws_access_key_id,
                "aws_secret_access_key": self.aws_secret_access_key,
                "region_name": self.aws_region,
            }
        return {"region_name": self.aws_region}

def analyze_text_with_comprehend_medical(client: Any, text: str) -> Optional[Dict[str, Any]]:
    """
    Analyzes a text string with AWS Comprehend Medical to detect medical entities.

    :param client: A configured boto3 client for comprehendmedical.
    :param text: The text to analyze.
    :return: The response dictionary from Comprehend Medical or None on error.
    """
    try:
        print("Calling DetectEntitiesV2...")
        response = client.detect_entities_v2(Text=text)
        print("Successfully received response.")
        return response
    except Exception as e:
        print(f"Error during API call: {e}")
        return None


def main():
    """
    Main function to initialize settings, create a client, and run the analysis.
    """
    print("Initializing settings...")
    settings = Settings()

    # Example text from a hypothetical patient-doctor chat
    sample_text = (
        "For the past three days, I have had a burning pain in the upper part of my stomach. "
        "The pain gets worse after eating and is sometimes accompanied by nausea. "
        "I feel bloated and uncomfortable, especially in the epigastric area. "
        "There is no vomiting or fever."
    )

    print(f"Analyzing text: \n---\n{sample_text}\n---")

    try:
        boto_kwargs = settings.get_boto_kwargs()
        # For this prototype, we ensure keys are present for local execution
        if "aws_access_key_id" not in boto_kwargs:
            print("Error: AWS credentials not found. Please create a .env file with AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
            return

        client = boto3.client("comprehendmedical", **boto_kwargs)
        
        comprehend_response = analyze_text_with_comprehend_medical(client, sample_text)

        if comprehend_response and "Entities" in comprehend_response:
            print("\n--- Analysis Results ---")
            # Pretty-print the JSON response of entities
            print(json.dumps(comprehend_response["Entities"], indent=4, default=str))

            print(f"\nCharacter count: {len(sample_text)}")
            # Note: Pricing is based on characters, which is useful for cost estimation.
        elif comprehend_response:
            print("\n--- Full Response (No Entities Found) ---")
            print(json.dumps(comprehend_response, indent=4, default=str))

    except Exception as e:
        print(f"An unexpected error occurred in main: {e}")


if __name__ == "__main__":
    main()
