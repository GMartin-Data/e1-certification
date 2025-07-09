# API Documentation

## Overview

The E1 Certification API provides RESTful access to the synchronized Collibra data catalog metadata. The API is deployed on AWS API Gateway with Lambda backend.

## Base URL

```
https://{api-id}.execute-api.{region}.amazonaws.com/{stage}
```

Example: `https://umvo6m118j.execute-api.eu-west-3.amazonaws.com/dev`

## Swagger Documentation

Interactive API documentation is available at:

```
https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/docs
```

## Authentication

The API uses JWT (JSON Web Token) authentication for protected endpoints.

### Login

```bash
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using the Token

Include the token in the Authorization header:

```bash
Authorization: Bearer {token}
```

## Endpoints Overview

### Public Endpoints (No Auth Required)

| Method | Endpoint                      | Description              |
| ------ | ----------------------------- | ------------------------ |
| GET    | `/health`                     | Health check             |
| GET    | `/api/v1/communities`         | List all communities     |
| GET    | `/api/v1/communities/{id}`    | Get community by ID      |
| GET    | `/api/v1/domains`             | List domains (paginated) |
| GET    | `/api/v1/domains/{id}`        | Get domain by ID         |
| GET    | `/api/v1/domains/{id}/tables` | List tables for domain   |
| GET    | `/api/v1/tables/{id}`         | Get table by ID          |
| GET    | `/api/v1/tables/{id}/columns` | List columns for table   |
| GET    | `/api/v1/columns/{id}`        | Get column by ID         |

### Protected Endpoints (Auth Required)

| Method | Endpoint               | Description       |
| ------ | ---------------------- | ----------------- |
| POST   | `/api/v1/tables`       | Create new table  |
| PUT    | `/api/v1/tables/{id}`  | Update table      |
| DELETE | `/api/v1/tables/{id}`  | Delete table      |
| POST   | `/api/v1/columns`      | Create new column |
| PUT    | `/api/v1/columns/{id}` | Update column     |
| DELETE | `/api/v1/columns/{id}` | Delete column     |

## Query Parameters

### Pagination

Supported on list endpoints:

- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 50, max: 100)

Example: `/api/v1/domains?page=2&per_page=25`

### Filtering

- Domains can be filtered by community: `/api/v1/domains?communaute_id=1`
- Tables must be accessed through domain: `/api/v1/domains/{domain_id}/tables`
- Columns must be accessed through table: `/api/v1/tables/{table_id}/columns`

## Example Requests

### Get All Communities

```bash
curl https://api-url/dev/api/v1/communities
```

### Login and Get Token

```bash
# Login
TOKEN=$(curl -s -X POST https://api-url/dev/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

# Use token
curl -H "Authorization: Bearer $TOKEN" \
  https://api-url/dev/api/v1/auth/me
```

### Create a Table (Protected)

```bash
curl -X POST https://api-url/dev/api/v1/tables \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "New Table",
    "description": "Created via API",
    "domaine_id": "domain-uuid-here"
  }'
```

## Response Format

### Success Response

```json
{
  "data": [...],
  "pagination": {
    "total": 100,
    "page": 1,
    "per_page": 50,
    "pages": 2
  }
}
```

### Error Response

```json
{
  "detail": "Resource not found"
}
```

## Rate Limits

- No specific rate limits implemented
- AWS API Gateway default limits apply (10,000 requests per second)

## Known Limitations

1. **CORS in Swagger UI**: OAuth2 flow doesn't work in Swagger UI due to CORS. Use curl or Postman for authentication.
2. **Data Persistence**: All modifications are overwritten by the weekly ETL process.
3. **VPC Configuration**: Lambda runs outside VPC to access SSM parameters. Production deployment should use VPC endpoints.

## Development vs Production

### Development

- Mock users hardcoded for demo purposes
- Public RDS access enabled
- Permissive CORS settings

### Production Recommendations

- Implement proper user management (AWS Cognito or RDS users table)
- Use VPC endpoints for SSM
- Restrict CORS to specific domains
- Enable API Gateway caching
