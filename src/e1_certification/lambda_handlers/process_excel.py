"""
Lambda handler for processing Excel files from S3.
Triggered by EventBridge schedules to process all files in incoming/ folder.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import boto3

from e1_certification.config import settings
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


def process_file_batch(files: dict[str, dict[str, str]]) -> dict[str, Any]:
    """
    Process a batch of related Excel files.

    Args:
        files: Dict mapping entity type to S3 info

    Example input:
        {
            "communautes": {
                "bucket": "e1-certification-excel-dev-123456",
                "key": "incoming/20240105_120000/metadata_communities_v2.xlsx",
                "filename": "metadata_communities_v2.xlsx"
            },
            "domaines": {
                "bucket": "e1-certification-excel-dev-123456",
                "key": "incoming/20240105_120000/metadata_domaines_v2.xlsx",
                "filename": "metadata_domaines_v2.xlsx"
            },
            "data_tables": {...},
            "data_colonnes": {...}
        }

    Returns:
        Processing statistics

    Example output (success):
        {
            "communautes": {"read": 20, "loaded": 20},
            "domaines": {"read": 145, "loaded": 145},
            "data_tables": {"read": 1356, "loaded": 1356},
            "data_colonnes": {"read": 61113, "loaded": 61113},
            "errors": []
        }

    Example output (error):
        {
            "error": "Cannot connect to database",
            "error_type": "ConnectionError",
            "files_affected": ["communautes", "domaines", "data_tables", "data_colonnes"]
        }
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


def process_batch() -> dict[str, Any]:
    """
    Process all Excel files in incoming/ folder.
    Groups files by timestamp prefix and processes each batch.

    Returns:
        Processing results

    Example output (success):
        {
            "files_processed": 4,
            "errors": [],
            "stats": {
                "incoming/20240105_120000": {
                    "communautes": {"read": 20, "loaded": 20},
                    "domaines": {"read": 145, "loaded": 145},
                    "data_tables": {"read": 1356, "loaded": 1356},
                    "data_colonnes": {"read": 61113, "loaded": 61113},
                    "errors": []
                }
            }
        }

    Example output (partial failure):
        {
            "files_processed": 8,
            "errors": [
                {
                    "batch": "incoming/20240105_140000",
                    "error": "Foreign key constraint failed",
                    "files_affected": ["domaines", "data_tables"]
                }
            ],
            "stats": {
                "incoming/20240105_120000": {
                    "communautes": {"read": 20, "loaded": 20},
                    "domaines": {"read": 145, "loaded": 145},
                    "data_tables": {"read": 1356, "loaded": 1356},
                    "data_colonnes": {"read": 61113, "loaded": 61113},
                    "errors": []
                },
                "incoming/20240105_140000": {
                    "error": "Foreign key constraint failed",
                    "error_type": "IntegrityError",
                    "files_affected": ["domaines", "data_tables"]
                }
            }
        }

    Example output (no files):
        {
            "message": "No files to process",
            "files_processed": 0,
            "errors": []
        }
    """
    s3_client = boto3.client("s3")
    bucket_name = settings.s3_bucket_name

    # List all objects in incoming/
    response = s3_client.list_objects_v2(
        Bucket=bucket_name, Prefix="incoming/", Delimiter="/"
    )

    if "Contents" not in response:
        logger.info("📭 No files to process in incoming/")
        return {"message": "No files to process", "files_processed": 0, "errors": []}

    # Get all Excel files (excluding temp files starting with ~$)
    excel_files = []
    for obj in response["Contents"]:
        key = obj["Key"]
        if key.endswith(".xlsx") and not os.path.basename(key).startswith("~$"):
            excel_files.append(key)

    if not excel_files:
        logger.info("📭 No Excel files found in incoming/")
        return {"message": "No Excel files found", "files_processed": 0, "errors": []}

    # Group files by batch (same timestamp prefix)
    file_batches = {}
    for key in excel_files:
        # Extract batch key (e.g., "incoming/20240105_120000")
        parts = key.split("/")
        if len(parts) >= 2:
            # Extract timestamp prefix from filename
            filename = parts[-1]  # "20250707_04_metadata_columns_v2.xlsx"
            timestamp = "_".join(filename.split("_")[:2])  # "20250707_04"
            batch_key = f"{parts[0]}/{timestamp}"  # "incoming/20250707_04"
        else:
            batch_key = "incoming/manual"

        if batch_key not in file_batches:
            file_batches[batch_key] = {}

        # Identify file type
        filename = os.path.basename(key)
        file_type = identify_file_type(filename)

        if file_type:
            file_batches[batch_key][file_type] = {
                "bucket": bucket_name,
                "key": key,
                "filename": filename,
            }

    # Process each batch
    results = {"files_processed": 0, "errors": [], "stats": {}}

    for batch_key, files in sorted(file_batches.items()):
        logger.info(f"🔁 Processing batch: {batch_key}")
        batch_stats = process_file_batch(files)
        logger.info(f"📊 Batch stats keys: {batch_stats.keys()}")
        logger.info(
            f"🔍 Move condition check: 'error' in batch_stats = {'error' in batch_stats}"
        )
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

        # Move processed files to processed/ folder if successful
        if "error" not in batch_stats:
            logger.info(f"✅ No errors found, moving {len(files)} files...")
            for file_info in files.values():
                try:
                    old_key = file_info["key"]
                    new_key = old_key.replace("incoming/", "processed/", 1)
                    logger.info(f"🚚 Moving {old_key} -> {new_key}")

                    # Copy to processed/
                    s3_client.copy_object(
                        CopySource={"Bucket": bucket_name, "Key": old_key},
                        Bucket=bucket_name,
                        Key=new_key,
                    )

                    # Delete from incoming/
                    s3_client.delete_object(Bucket=bucket_name, Key=old_key)

                    logger.info(f"✅ Moved {old_key} to {new_key}")

                except Exception as e:
                    logger.error(f"❌ Failed to move {old_key}: {e}")

    logger.info("🏁 All batches processed, flushing logs...")
    import sys

    sys.stdout.flush()
    sys.stderr.flush()

    return results


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Main Lambda handler function.

    Args:
        event: Eventbridge event (or manual invocation)
        context: Lambda context

    Returns:
        Response with processing results
    """
    # Clear caches to ensure fresh settings in Lambda
    from e1_certification.config import get_settings

    get_settings.cache_clear()

    # Also clear the database engine cache
    close_db_connections()

    # Log event source
    event_source = "EventBridge" if event.get("source") == "aws.events" else "manual"
    logger.info(f"🚀 Lambda handler started: {event_source} trigger")

    try:
        # Initialize database connection
        init_db()

        # Process all files in incoming/ folder
        results = process_batch()

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
    # Test EventBridge event
    test_event = {
        "source": "aws.events",
        "detail-type": "Scheduled Event",
        "resources": [
            "arn:aws:events:eu-west-3:123456789012:rule/BatchProcessingSchedule"
        ],
    }

    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
