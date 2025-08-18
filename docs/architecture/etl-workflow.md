# ETL Workflow Architecture

## Overview

The E1 Certification ETL (Extract, Transform, Load) workflow is a serverless pipeline that automatically refreshes a MySQL database with data from Excel files. The system runs weekly and ensures data consistency through a complete refresh strategy.

## High-Level Architecture

```mermaid
%%{init: {
  'theme': 'dark',
  'themeVariables': {
    'primaryColor': '#1a1a1a',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#ffffff',
    'background': '#000000',
    'mainBkg': '#1a1a1a',
    'lineColor': '#ffffff'
  }
}}%%

graph TB
    subgraph "Local Environment"
        A[Excel Files<br/>data/excel/pending/] -->|Cron: Sunday 1:00 AM| B[upload_to_s3.py]
    end

    subgraph "AWS Cloud"
        B -->|Upload| C[S3 Bucket<br/>incoming/]
        D[EventBridge<br/>Sunday 1:30 AM] -->|Trigger| E[Lambda Function<br/>process_excel]
        C -->|Read Files| E
        E -->|1️⃣ Truncate All Tables| F[(RDS MySQL<br/>Database)]
        E -->|2️⃣ Load Fresh Data| F
        E -->|3️⃣ Move Files| G[S3 Bucket<br/>processed/]
    end

    %% WCAG AA compliant colors optimized for dark background
    classDef localFiles fill:#E8F4F8,stroke:#ffffff,stroke-width:3px,color:#000
    classDef s3Incoming fill:#FFF4E6,stroke:#ffffff,stroke-width:3px,color:#000
    classDef s3Processed fill:#E6FFE6,stroke:#ffffff,stroke-width:3px,color:#000
    classDef database fill:#F0E6FF,stroke:#ffffff,stroke-width:3px,color:#000
    classDef lambda fill:#FFEBE6,stroke:#ffffff,stroke-width:3px,color:#000
    classDef eventbridge fill:#FFE6E6,stroke:#ffffff,stroke-width:3px,color:#000

    class A,B localFiles
    class C s3Incoming
    class G s3Processed
    class F database
    class E lambda
    class D eventbridge
```

## Detailed Workflow

### 1. File Upload Process

```mermaid
%%{init: {
  'theme': 'dark',
  'themeVariables': {
    'primaryColor': '#1a1a1a',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#ffffff',
    'background': '#000000',
    'mainBkg': '#1a1a1a',
    'actorBkg': '#E8F4F8',
    'actorBorder': '#1E5A6E',
    'actorTextColor': '#000000',
    'actorLineColor': '#ffffff',
    'signalColor': '#ffffff',
    'signalTextColor': '#ffffff',
    'labelBoxBkgColor': '#3d3d3d',
    'labelBoxBorderColor': '#ffffff',
    'labelTextColor': '#ffffff',
    'loopTextColor': '#ffffff',
    'activationBorderColor': '#ffffff',
    'activationBkgColor': '#003D82',
    'sequenceNumberColor': '#ffffff',
    'noteBkgColor': '#FFF4E6',
    'noteTextColor': '#000000',
    'noteBorderColor': '#8B6914'
  }
}}%%

sequenceDiagram
    participant Cron
    participant Script as upload_to_s3.py
    participant S3

    Note over Cron: 🕐 Every Sunday 1:00 AM
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
%%{init: {
  'theme': 'dark',
  'themeVariables': {
    'primaryColor': '#1a1a1a',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#ffffff',
    'background': '#000000',
    'mainBkg': '#1a1a1a',
    'lineColor': '#ffffff'
  }
}}%%

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

    %% WCAG AA compliant colors optimized for dark background
    classDef trigger fill:#FFE6E6,stroke:#ffffff,stroke-width:3px,color:#000
    classDef success fill:#E6FFE6,stroke:#ffffff,stroke-width:3px,color:#000
    classDef retry fill:#FFEBE6,stroke:#ffffff,stroke-width:3px,color:#000
    classDef truncate fill:#E8F4F8,stroke:#ffffff,stroke-width:3px,color:#000
    classDef communities fill:#F0E6FF,stroke:#ffffff,stroke-width:3px,color:#000
    classDef domains fill:#FFF4E6,stroke:#ffffff,stroke-width:3px,color:#000
    classDef tables fill:#E8F4F8,stroke:#ffffff,stroke-width:3px,color:#000
    classDef columns fill:#F0E6FF,stroke:#ffffff,stroke-width:3px,color:#000

    class A trigger
    class N success
    class O retry
    class F truncate
    class G communities
    class H domains
    class I tables
    class J columns
```

### 3. Database Refresh Strategy

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#ffffff',
    'primaryTextColor': '#000000',
    'primaryBorderColor': '#000000',
    'background': '#ffffff',
    'mainBkg': '#ffffff',
    'lineColor': '#ffffff'
  }
}}%%

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

    %% WCAG AA compliant colors for accessibility
    classDef startTransaction fill:#FFEBE6,stroke:#8B4513,stroke-width:3px,color:#000
    classDef foreignKeyOff fill:#FFE6E6,stroke:#8B0000,stroke-width:3px,color:#000
    classDef discovery fill:#E8F4F8,stroke:#1E5A6E,stroke-width:3px,color:#000
    classDef loadData fill:#E6FFE6,stroke:#2E7D2E,stroke-width:3px,color:#000
    classDef truncate1 fill:#F0E6FF,stroke:#5A2C7A,stroke-width:3px,color:#000
    classDef truncate2 fill:#F0E6FF,stroke:#5A2C7A,stroke-width:3px,color:#000
    classDef truncate3 fill:#F0E6FF,stroke:#5A2C7A,stroke-width:3px,color:#000
    classDef truncate4 fill:#F0E6FF,stroke:#5A2C7A,stroke-width:3px,color:#000
    classDef truncate5 fill:#F0E6FF,stroke:#5A2C7A,stroke-width:3px,color:#000
    classDef foreignKeyOn fill:#FFE6E6,stroke:#8B0000,stroke-width:3px,color:#000

    class A startTransaction
    class B foreignKeyOff
    class C discovery
    class J loadData
    class D truncate1
    class E truncate2
    class F truncate3
    class G truncate4
    class H truncate5
    class I foreignKeyOn
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
%%{init: {
  'theme': 'dark',
  'themeVariables': {
    'primaryColor': '#1a1a1a',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#ffffff',
    'background': '#000000',
    'mainBkg': '#1a1a1a',
    'lineColor': '#ffffff'
  }
}}%%

graph LR
    A[File 1<br/>20250107_14_communities.xlsx] --> D[Batch: 20250107_14]
    B[File 2<br/>20250107_14_domains.xlsx] --> D
    C[File 3<br/>20250107_14_tables.xlsx] --> D
    E[File 4<br/>20250107_15_columns.xlsx] --> F[Batch: 20250107_15]

    %% Coherent pastel colors with optimal readability
    classDef batchSuccess fill:#E6FFE6,stroke:#ffffff,stroke-width:3px,color:#000
    classDef batchPending fill:#FFE6E6,stroke:#ffffff,stroke-width:3px,color:#000
    classDef fileCommunities fill:#E8F4F8,stroke:#ffffff,stroke-width:3px,color:#000
    classDef fileDomains fill:#F0E6FF,stroke:#ffffff,stroke-width:3px,color:#000
    classDef fileTables fill:#FFF4E6,stroke:#ffffff,stroke-width:3px,color:#000
    classDef fileColumns fill:#FFEBE6,stroke:#ffffff,stroke-width:3px,color:#000

    class D batchSuccess
    class F batchPending
    class A fileCommunities
    class B fileDomains
    class C fileTables
    class E fileColumns
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
%%{init: {
  'theme': 'dark',
  'themeVariables': {
    'primaryColor': '#1a1a1a',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#ffffff',
    'background': '#000000',
    'mainBkg': '#1a1a1a',
    'lineColor': '#ffffff'
  }
}}%%

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

    %% Coherent pastel colors for optimal readability
    classDef fileState fill:#E8F4F8,stroke:#ffffff,stroke-width:3px,color:#000
    classDef processState fill:#F0E6FF,stroke:#ffffff,stroke-width:3px,color:#000
    classDef successState fill:#E6FFE6,stroke:#ffffff,stroke-width:3px,color:#000
    classDef failedState fill:#FFE6E6,stroke:#ffffff,stroke-width:3px,color:#000
    classDef finalState fill:#FFEBE6,stroke:#ffffff,stroke-width:3px,color:#000

    class FileInIncoming fileState
    class Processing processState
    class Success successState
    class Failed failedState
    class FileInProcessed finalState
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
%%{init: {
  'theme': 'dark',
  'themeVariables': {
    'primaryColor': '#1a1a1a',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#ffffff',
    'background': '#000000',
    'mainBkg': '#1a1a1a',
    'lineColor': '#ffffff'
  }
}}%%

graph TD
    A[Files not processing?] --> B{Check S3 incoming/}
    B -->|Files present| C{Check EventBridge}
    B -->|No files| D[Check upload logs]
    C -->|Not triggered| E[Verify schedule]
    C -->|Triggered| F{Check Lambda logs}
    F -->|Errors| G[Fix errors]
    F -->|No logs| H[Check permissions]

    %% Coherent pastel colors for optimal readability
    classDef problemStart fill:#FFE6E6,stroke:#ffffff,stroke-width:3px,color:#000
    classDef checkFiles fill:#E8F4F8,stroke:#ffffff,stroke-width:3px,color:#000
    classDef checkEventBridge fill:#F0E6FF,stroke:#ffffff,stroke-width:3px,color:#000
    classDef verifyActions fill:#FFF4E6,stroke:#ffffff,stroke-width:3px,color:#000
    classDef checkLambda fill:#F0E6FF,stroke:#ffffff,stroke-width:3px,color:#000
    classDef fixActions fill:#FFEBE6,stroke:#ffffff,stroke-width:3px,color:#000

    class A problemStart
    class B checkFiles
    class C checkEventBridge
    class D,E verifyActions
    class F checkLambda
    class G,H fixActions
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
