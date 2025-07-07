# ETL Workflow Architecture

## Overview

The E1 Certification ETL (Extract, Transform, Load) workflow is a serverless pipeline that automatically refreshes a MySQL database with data from Excel files. The system runs weekly and ensures data consistency through a complete refresh strategy.

## High-Level Architecture

```mermaid
graph TB
    subgraph "Local Environment"
        A[Excel Files<br/>data/excel/pending/] -->|Cron: Sunday 1:00 AM| B[upload_to_s3.py]
    end

    subgraph "AWS Cloud"
        B -->|Upload| C[S3 Bucket<br/>incoming/]
        D[EventBridge<br/>Sunday 1:30 AM] -->|Trigger| E[Lambda Function<br/>process_excel]
        C -->|Read Files| E
        E -->|1. Truncate All Tables| F[(RDS MySQL<br/>Database)]
        E -->|2. Load Fresh Data| F
        E -->|3. Move Files| G[S3 Bucket<br/>processed/]
    end

    style A fill:#2196F3,stroke:#1565C0,color:#fff
    style C fill:#FF9800,stroke:#E65100,color:#fff
    style G fill:#4CAF50,stroke:#2E7D32,color:#fff
    style F fill:#9C27B0,stroke:#6A1B9A,color:#fff
    style E fill:#FFC107,stroke:#F57C00,color:#000
    style D fill:#F44336,stroke:#C62828,color:#fff
```

## Detailed Workflow

### 1. File Upload Process

```mermaid
sequenceDiagram
    participant Cron
    participant Script as upload_to_s3.py
    participant S3

    Note over Cron: Every Sunday 1:00 AM
    Cron->>Script: Trigger upload
    Script->>Script: Scan data/excel/pending/

    loop For each Excel file
        Script->>Script: Generate hourly timestamp<br/>(YYYYMMDD_HH)
        Script->>S3: Upload to incoming/<br/>20250107_01_filename.xlsx
        Script->>Script: Move to processed/
    end

    Script->>Cron: Log results
```

### 2. ETL Processing Flow

```mermaid
flowchart LR
    subgraph "Lambda Execution"
        A[EventBridge Trigger] --> B{Any files in<br/>incoming/?}
        B -->|No| C[End: No files]
        B -->|Yes| D[Group by timestamp]

        D --> E[Process Batch]

        subgraph "Batch Processing"
            E --> F[Truncate ALL tables]
            F --> G[Load Communities]
            G --> H[Load Domains]
            H --> I[Load Tables]
            I --> J[Load Columns]
        end

        J --> K{Success?}
        K -->|Yes| L[Move to processed/]
        K -->|No| M[Keep in incoming/]

        L --> N[End: Success]
        M --> O[End: Will retry]
    end

    style A fill:#F44336,stroke:#C62828,color:#fff
    style N fill:#4CAF50,stroke:#2E7D32,color:#fff
    style O fill:#FF5722,stroke:#D84315,color:#fff
    style F fill:#2196F3,stroke:#1565C0,color:#fff
    style G fill:#9C27B0,stroke:#6A1B9A,color:#fff
    style H fill:#FF9800,stroke:#E65100,color:#fff
    style I fill:#795548,stroke:#4E342E,color:#fff
    style J fill:#607D8B,stroke:#37474F,color:#fff
```

### 3. Database Refresh Strategy

```mermaid
graph TD
    A[Start Transaction] --> B[SET FOREIGN_KEY_CHECKS = 0]
    B --> C[Discover all tables<br/>from information_schema]

    C --> D[TRUNCATE communautes]
    C --> E[TRUNCATE domaines]
    C --> F[TRUNCATE data_tables]
    C --> G[TRUNCATE data_colonnes]
    C --> H[TRUNCATE future_tables...]

    D --> I[SET FOREIGN_KEY_CHECKS = 1]
    E --> I
    F --> I
    G --> I
    H --> I

    I --> J[Load new data<br/>in dependency order]

    style A fill:#FF9800,stroke:#E65100,color:#fff
    style B fill:#F44336,stroke:#C62828,color:#fff
    style C fill:#2196F3,stroke:#1565C0,color:#fff
    style J fill:#4CAF50,stroke:#2E7D32,color:#fff
    style D fill:#9C27B0,stroke:#6A1B9A,color:#fff
    style E fill:#3F51B5,stroke:#283593,color:#fff
    style F fill:#00BCD4,stroke:#00838F,color:#fff
    style G fill:#009688,stroke:#00695C,color:#fff
    style H fill:#607D8B,stroke:#37474F,color:#fff
    style I fill:#F44336,stroke:#C62828,color:#fff
```

## File Processing Details

### File Naming Convention

Files must follow this pattern for proper batch grouping:

```
{timestamp}_{description}.xlsx

Where:
- timestamp: YYYYMMDD_HH (year, month, day, hour)
- description: metadata_communities_v2, metadata_domaines_v2, etc.

Example: 20250107_14_metadata_communities_v2.xlsx
```

### Processing Order

Files are processed in a specific order to respect foreign key constraints:

1. **Communities** (communautes) - No dependencies
2. **Domains** (domaines) - Depends on communities
3. **Tables** (data_tables) - Depends on domains
4. **Columns** (data_colonnes) - Depends on tables

### Batch Grouping Logic

```mermaid
graph LR
    A[File 1<br/>20250107_14_communities.xlsx] --> D[Batch: 20250107_14]
    B[File 2<br/>20250107_14_domains.xlsx] --> D
    C[File 3<br/>20250107_14_tables.xlsx] --> D
    E[File 4<br/>20250107_15_columns.xlsx] --> F[Batch: 20250107_15]

    style D fill:#4CAF50,stroke:#2E7D32,color:#fff
    style F fill:#F44336,stroke:#C62828,color:#fff
    style A fill:#2196F3,stroke:#1565C0,color:#fff
    style B fill:#9C27B0,stroke:#6A1B9A,color:#fff
    style C fill:#FF9800,stroke:#E65100,color:#fff
    style E fill:#795548,stroke:#4E342E,color:#fff
```

Files with the same timestamp prefix are processed together as one batch.

## Schedule Configuration

### Production Schedule

| Component   | Schedule     | Time (UTC) | Purpose                  |
| ----------- | ------------ | ---------- | ------------------------ |
| Local Cron  | Every Sunday | 1:00 AM    | Upload Excel files to S3 |
| EventBridge | Every Sunday | 1:30 AM    | Process uploaded files   |

### Manual Execution

For testing or on-demand processing:

```bash
# Upload files manually
python scripts/upload_to_s3.py

# Trigger Lambda manually
aws lambda invoke \
    --function-name e1-certification-dev-process-excel \
    --cli-binary-format raw-in-base64-out \
    --payload '{"source": "aws.events"}' \
    response.json
```

## Error Handling

### Retry Strategy

```mermaid
stateDiagram-v2
    [*] --> FileInIncoming
    FileInIncoming --> Processing: EventBridge Trigger
    Processing --> Success: No Errors
    Processing --> Failed: Error Occurred
    Success --> FileInProcessed: Move File
    Failed --> FileInIncoming: Keep for Retry
    FileInProcessed --> [*]

    note right of Failed
        File stays in incoming/
        Will retry next schedule
    end note
```

### Common Issues

1. **Foreign Key Errors**: Should not occur with full refresh strategy
2. **Timeout**: Lambda has 15-minute timeout for large datasets
3. **Permission Errors**: Lambda needs S3CrudPolicy for file operations

## Monitoring

### CloudWatch Logs

Monitor execution through CloudWatch:

```bash
# Tail Lambda logs
make logs

# Search for errors
aws logs filter-log-events \
    --log-group-name /aws/lambda/e1-certification-dev-process-excel \
    --filter-pattern "ERROR"
```

### Key Metrics to Monitor

- **Processing Time**: ~50-60 seconds for full dataset
- **Records Loaded**:
  - Communities: ~20
  - Domains: ~145
  - Tables: ~1,356
  - Columns: ~61,113
- **Files Processed**: 4 per batch

## Best Practices

1. **Always upload complete sets** - All 4 files should be uploaded together
2. **Use consistent timestamps** - Upload files within the same hour
3. **Monitor first run** - Check logs after schedule changes
4. **Keep processed files** - Archive in S3 for audit trail
5. **Test locally first** - Use `make etl-local` before uploading

## Troubleshooting

### Files Not Processing

```mermaid
graph TD
    A[Files not processing?] --> B{Check S3 incoming/}
    B -->|Files present| C{Check EventBridge}
    B -->|No files| D[Check upload logs]
    C -->|Not triggered| E[Verify schedule]
    C -->|Triggered| F{Check Lambda logs}
    F -->|Errors| G[Fix errors]
    F -->|No logs| H[Check permissions]

    style A fill:#F44336,stroke:#C62828,color:#fff
    style B fill:#2196F3,stroke:#1565C0,color:#fff
    style C fill:#FF9800,stroke:#E65100,color:#fff
    style D fill:#FFC107,stroke:#F57C00,color:#000
    style E fill:#FFC107,stroke:#F57C00,color:#000
    style F fill:#9C27B0,stroke:#6A1B9A,color:#fff
    style G fill:#FFC107,stroke:#F57C00,color:#000
    style H fill:#FFC107,stroke:#F57C00,color:#000
```

### Database Not Updating

1. Check truncation succeeded in logs
2. Verify all 4 files were provided
3. Check for foreign key errors
4. Ensure correct file naming

### Performance Issues

- Increase Lambda memory if needed (current: 1024 MB)
- Check RDS instance performance
- Monitor network latency

## Future Possible Enhancements

- [ ] Add SNS notifications for failures
- [ ] Implement data validation before loading
- [ ] Add CloudWatch dashboards
- [ ] Support incremental updates
- [ ] Add data quality checks
