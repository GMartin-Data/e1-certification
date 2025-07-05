"""
Upload Excel files from local directory to S3 bucket.
Validate files before upload and moves processed files.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

import boto3  # noqa: E402
from botocore.exceptions import ClientError  # noqa: E402
from e1_certification.config import settings  # noqa: E402
from e1_certification.utils.logging_config import logger  # noqa: E402


class ExcelUploader:
    """Handle Excel file uploads to S3."""

    VALID_EXTENSIONS = {".xlsx", ".xls"}
    MAX_FILE_SIZE_MB = 50

    def __init__(self, bucket_name: str | None = None):
        """
        Initialize uploader with S3 bucket.

        Args:
            bucket_name: S3 bucket name (uses settings if not provided).
        """
        self.bucket_name = bucket_name or settings.s3_bucket_name
        if not self.bucket_name:
            raise ValueError(
                "❌ S3 bucket not configured! "
                "Please set S3_BUCKET_NAME in .env or deploy SAM stack"
            )

        self.s3_client = boto3.client("s3", region_name=settings.aws_region)
        self.pending_dir = Path("data/excel/pending")
        self.processed_dir = Path("data/excel/processed")

    def validate_file(self, file_path: Path) -> bool:
        """
        Validate Excel file before upload, checking extension and size.

        Args:
            file_path: Path to the Excel file.

        Returns:
            True if valid, False otherwise.
        """
        # Check extension
        if file_path.suffix.lower() not in self.VALID_EXTENSIONS:
            logger.warning(f"⚠️  Skipping {file_path.name}: Invalid extension")
            return False

        # Check file size
        size_mb = file_path.stat().st_size / (1_024 * 1_024)
        if size_mb > self.MAX_FILE_SIZE_MB:
            logger.warning(
                f"⚠️  Skipping {file_path.name}: "
                f"File too large ({size_mb:.1f}MB > {self.MAX_FILE_SIZE_MB}MB)"
            )
            return False

        # Check if file is readable
        try:
            with open(file_path, "rb") as f:
                f.read(1)  # Try to read one byte
        except Exception as e:
            logger.error(f"❌ Cannot read {file_path.name}: {e}")
            return False

        logger.info(f"✅ Validated {file_path.name} ({size_mb:.1f}MB)")
        return True

    def upload_file(self, file_path: Path) -> bool:
        """
        Upload single file to S3.

        Args:
            file_path: Path to file

        Returns:
            True if successful, False otherwise.
        """
        # Create S3 key with timestamp prefix
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        s3_key = f"incoming/{timestamp}_{file_path.name}"

        try:
            logger.info(
                f"📤 Uploading {file_path.name} to s3://{self.bucket_name}/{s3_key}"
            )

            # Upload with metadata
            self.s3_client.upload_file(
                str(file_path),
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    "Metadata": {
                        "upload-time": timestamp,
                        "original-name": file_path.name,
                        "file-size": str(file_path.stat().st_size),
                    }
                },
            )

            logger.info(f"✅ Successfully uploaded {file_path.name}")
            return True

        except ClientError as e:
            logger.error(f"❌ Failed to upload {file_path.name}: {e}")
            return False

    def move_to_processed(self, file_path: Path) -> None:
        """Move file to processed directory after successful upload."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        new_name = f"{timestamp}_{file_path.name}"
        destination = self.processed_dir / new_name

        file_path.rename(destination)
        logger.info(f"📁 Moved {file_path.name} to processed folder")

    def upload_batch(self) -> dict[str, int]:
        """
        Upload all Excel files from pending directory.

        Returns:
            Dictionary with upload statistics
        """
        stats = {"total": 0, "uploaded": 0, "failed": 0, "skipped": 0}

        # Get all Excel files
        excel_files = list(self.pending_dir.glob("*.xlsx")) + list(
            self.pending_dir.glob("*.xls")
        )

        if not excel_files:
            logger.warning("📭 No Excel files found in pending directory")
            return stats

        logger.info(f"📋 Found {len(excel_files)} files to process")
        stats["total"] = len(excel_files)

        # Process each file
        for file_path in excel_files:
            # Validate
            if not self.validate_file(file_path):
                stats["skipped"] += 1
                continue

            # Upload
            if self.upload_file(file_path):
                stats["uploaded"] += 1
                self.move_to_processed(file_path)
            else:
                stats["failed"] += 1

        # Summary
        logger.info(
            f"\n📊 Upload Summary:\n"
            f"   Total files: {stats['total']}\n"
            f"   ✅ Uploaded: {stats['uploaded']}\n"
            f"   ❌ Failed: {stats['failed']}\n"
            f"   ⚠️  Skipped: {stats['skipped']}"
        )

        return stats


def main():
    """Main entry point for script execution."""

    try:
        uploader = ExcelUploader()

        # Test S3 access
        logger.info(f"☑️ Checking S3 bucket: {uploader.bucket_name}")
        uploader.s3_client.head_bucket(Bucket=uploader.bucket_name)
        logger.info("✅ S3 bucket accessible")

        # Upload files
        logger.info("\n🚀 Starting Excel file upload...")
        stats = uploader.upload_batch()

        # Exit code based on results
        if stats["failed"] > 0:
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Upload failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
