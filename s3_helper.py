import boto3
import requests
import os
from botocore.exceptions import ClientError

# Your S3 bucket name — change this to your actual bucket name
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "unievents-images-bucket")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# boto3 automatically uses the EC2 IAM role — no keys needed!
s3_client = boto3.client("s3", region_name=AWS_REGION)

def upload_image_to_s3(image_url: str, event_id: str) -> str:
    """
    Downloads an image from a URL and uploads it to S3.
    Returns the public S3 URL, or empty string on failure.
    """
    try:
        # Download the image
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        # Determine file extension
        content_type = response.headers.get("Content-Type", "image/jpeg")
        ext = "jpg" if "jpeg" in content_type else "png"

        # S3 object key
        s3_key = f"events/{event_id}.{ext}"

        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=response.content,
            ContentType=content_type
        )

        # Return the S3 URL
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        print(f"Uploaded image for event {event_id} to S3.")
        return s3_url

    except (requests.exceptions.RequestException, ClientError) as e:
        print(f"Failed to upload image for event {event_id}: {e}")
        return ""
