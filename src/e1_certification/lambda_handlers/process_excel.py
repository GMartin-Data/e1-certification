"""
Lambda handler for processing Excel files from S3.
Triggered by S3 events or EventBridge schedules.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import boto3

from e1_certification.db import close_db_connections, init_db
from e1_certification.etl.processor import CollibraETLProcessor
from e1_certification.utils.logging_config import logger


def download_s3_file(bucket: str, key: str, local_path: Path) -> None:
    """Download file from S3 to local path inside the Lambda's environment."""
    s3_client = boto3.client("s3")
    logger.info(f"📥 Downloading s3://{bucket}/{key} to {local_path}")
    s3_client.download_file(bucket, key, str(local_path))


def identify_file_type(filename: str) -> str | None:
    """
    Identify entity type from filename.

    Returns:
        Entity name or None if not recognized.
    """
    filename_lower = filename.lower()

    if "commun" in filename_lower:
        return "communautes"
    elif "domain" in filename_lower or "domaine" in filename_lower:
        return "domaines"
    elif "table" in filename_lower and "column" not in filename_lower:
        return "data_tables"
    elif "col" in filename_lower:
        return "data_colonnes"

    return None


def process_s3_event(event: dict[str, Any]) -> dict[str, Any]:
    """
    Process files from S3 event notification.

    Args:
        event: S3 event from Lambda

    Returns:
        Processing results
    """
    results = {"files_processed": 0, "errors": [], "stats": {}}

    # Extract S3 records from event
    records = event.get("Records", [])
    if not records:
        logger.warning("⚠️ No S3 records in event")
        return results

    # Group files by upload batch (same prefix)
    file_batches = {}

    for record in records:
        # Get S3 info
        s3_info = record.get("s3", {})
        bucket = s3_info.get("bucket", {}).get("name")
        key = s3_info.get("object", {}).get("key")

        if not bucket or not key:
            logger.error(f"❌ Invalid S3 record: {record}")
            continue

        # Extract batch prefix (e.g., "incoming/20240105_120000")
        parts = key.split("/")
        if len(parts) >= 2:
            batch_key = "/".join(parts[:2])
        else:
            batch_key = "unknown"

        if batch_key not in file_batches:
            file_batches[batch_key] = {}

        # Identify file type
        filename = os.path.basename(key)
        file_type = identify_file_type(filename)

        if file_type:
            file_batches[batch_key][file_type] = {
                "bucket": bucket,
                "key": key,
                "filename": filename,
            }
        else:
            logger.warning(f"⚠️ Unknown file type for {filename}")

        # Process each batch
        for batch_key, files in file_batches.items():
            logger.info(f"🔁 Processing batch: {batch_key}")
            batch_stats = process_file_batch(files)
            results["stats"][batch_key] = batch_stats
            results["files_processed"] += len(files)

            # Collect any errors
            if "error" in batch_stats:
                results["errors"].append(
                    {
                        "batch": batch_key,
                        "error": batch_stats["error"],
                        "files_affected": list(files.keys()),
                    }
                )

    return results


def process_file_batch(files: dict[str, dict[str, str]]) -> dict[str, Any]:
    """
    Process a batch of related Excel files.

    Args:
        files: Dict mapping entity type to S3 info

    Returns:
        Processing statistics
    """
    # Use Lambda's /tmp directory for local storage
    with tempfile.TemporaryDirectory(dir="/tmp") as temp_dir:
        temp_path = Path(temp_dir)
        file_paths = {}

        try:
            # Download all files
            for entity_type, s3_info in files.items():
                local_path = temp_path / s3_info["filename"]
                download_s3_file(s3_info["bucket"], s3_info["key"], local_path)
                file_paths[entity_type] = local_path

            # Process with ETL
            processor = CollibraETLProcessor(file_paths)
            stats = processor.process_all()

            logger.info(f"✅ Batch processing complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"❌ Batch processing failed: {e}")
            return {
                "error": str(e),
                "error_type": type(e).__name__,
                "files_affected": list(files.keys()),
            }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Main Lambda handler function.

    Args:
        event: Lambda event (S3 or EventBridge)
        context: Lambda context

    Returns:
        Response with processing results
    """
    logger.info(f"🚀 Lambda handler started: {event.get('source', 'unknown')} event")

    try:
        # Initialize database connection
        init_db()

        # Process based on event source
        if "Records" in event:
            # S3 event
            results = process_s3_event(event)
        else:
            # EventBridge or manual trigger
            # Process all files in incoming folder
            logger.info("🗓️ Scheduled processing not yet implemented")
            results = {"message": "Scheduled processing not yet implemented"}

        # Determine status code based on errors
        status_code = 500 if results.get("errors") else 200

        return {"statusCode": status_code, "body": json.dumps(results)}

    except Exception as e:
        logger.error(f"❌ Lambda handler failed: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e), "type": type(e).__name__}),
        }

    finally:
        # Clean up database connections
        close_db_connections()


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "test-bucket"},
                    "object": {
                        "key": "incoming/20240105_120000/metadata_communities.xlsx"
                    },
                }
            }
        ]
    }

    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
