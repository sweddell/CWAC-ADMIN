# API Reference

Complete reference for the CWAC-ADMIN REST API.

## Overview

CWAC-ADMIN provides a REST API for programmatic access to all features. This enables:

- Integration with CI/CD pipelines
- Custom dashboards and reporting
- Automated workflows
- Third-party tool integration

**Base URL**: `http://localhost:5001/api`

**Authentication**: Session-based (login required)

**Response Format**: JSON

## Authentication

### Login

**Endpoint**: `POST /login`

**Description**: Authenticate and create session

**Request Body**:
```json
{
  "username": "admin",
  "password": "admin"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "username": "admin",
    "email": "admin@cwac-admin.org",
    "is_admin": true
  }
}
```

**Status Codes**:
- `200` - Success
- `401` - Invalid credentials
- `400` - Missing parameters

### Logout

**Endpoint**: `POST /logout`

**Description**: End session

**Response**:
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

## Sites API

### List All Sites

**Endpoint**: `GET /api/sites`

**Description**: Get all monitored sites

**Response**:
```json
{
  "sites": [
    {
      "id": 1,
      "url": "https://www.example.com",
      "organisation": "Example Corp",
      "sector": "Technology",
      "last_scan": "2024-11-12T10:30:00",
      "latest_score": 85.5,
      "total_issues": 42
    }
  ]
}
```

### Get Site Details

**Endpoint**: `GET /api/sites/{id}`

**Description**: Get detailed information about a specific site

**Response**:
```json
{
  "site": {
    "id": 1,
    "url": "https://www.example.com",
    "organisation": "Example Corp",
    "sector": "Technology",
    "created_at": "2024-01-01T00:00:00"
  },
  "latest_scan": {
    "scan_id": "scan_20241112_103000",
    "scan_date": "2024-11-12T10:30:00",
    "a11y_score": 85.5,
    "pages_scanned": 20,
    "total_issues": 42,
    "critical_issues": 3,
    "serious_issues": 12,
    "moderate_issues": 18,
    "minor_issues": 9
  },
  "scan_history": [...]
}
```

### Add Site

**Endpoint**: `POST /api/sites`

**Description**: Add a new site to monitor

**Request Body**:
```json
{
  "url": "https://www.newsite.com",
  "organisation": "New Organization",
  "sector": "Education"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Site added successfully",
  "site_id": 2
}
```

**Status Codes**:
- `201` - Created
- `400` - Invalid data
- `409` - Site already exists

### Update Site

**Endpoint**: `PUT /api/sites/{id}`

**Description**: Update site information

**Request Body**:
```json
{
  "organisation": "Updated Organization Name",
  "sector": "Government"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Site updated successfully"
}
```

### Delete Site

**Endpoint**: `DELETE /api/sites/{id}`

**Description**: Remove a site

**Response**:
```json
{
  "success": true,
  "message": "Site deleted successfully"
}
```

**Note**: Deletes all associated scan data.

## Scans API

### Start Scan

**Endpoint**: `POST /api/scans/start`

**Description**: Initiate a new scan

**Request Body**:
```json
{
  "config_name": "config_standard_scan.json",
  "site_url": "https://www.example.com"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Scan started",
  "scan_id": "scan_20241112_153045"
}
```

### Get Scan Status

**Endpoint**: `GET /api/scans/{scan_id}`

**Description**: Check scan progress and results

**Response**:
```json
{
  "scan_id": "scan_20241112_153045",
  "status": "completed",
  "progress": 100,
  "pages_scanned": 20,
  "scan_date": "2024-11-12T15:30:45",
  "results": {
    "a11y_score": 85.5,
    "total_issues": 42,
    "critical_issues": 3
  }
}
```

**Status Values**:
- `running` - Scan in progress
- `completed` - Scan finished successfully
- `failed` - Scan encountered error

### Get Scan Results

**Endpoint**: `GET /api/scans/{scan_id}/results`

**Description**: Get detailed scan results

**Query Parameters**:
- `format` - Response format (`json` or `csv`)
- `severity` - Filter by severity (`critical`, `serious`, `moderate`, `minor`)
- `wcag` - Filter by WCAG criterion (e.g., `1.3.1`)

**Response**:
```json
{
  "scan_id": "scan_20241112_153045",
  "summary": {
    "total_pages": 20,
    "total_issues": 42,
    "a11y_score": 85.5
  },
  "pages": [...],
  "issues": [...]
}
```

## Schedules API

### List Schedules

**Endpoint**: `GET /api/schedules`

**Description**: Get all scan schedules

**Response**:
```json
{
  "schedules": [
    {
      "id": 1,
      "config_name": "Daily Full Scan",
      "config_path": "config/full_scan.json",
      "schedule_type": "daily",
      "schedule_value": "09:00",
      "enabled": true,
      "last_run": "2024-11-12T09:00:00",
      "next_run": "2024-11-13T09:00:00"
    }
  ]
}
```

### Create Schedule

**Endpoint**: `POST /api/schedules`

**Description**: Create automated scan schedule

**Request Body**:
```json
{
  "config_name": "Weekly Audit",
  "config_path": "config/weekly_scan.json",
  "schedule_type": "weekly",
  "schedule_value": "monday,09:00",
  "enabled": true
}
```

**Response**:
```json
{
  "success": true,
  "message": "Schedule created successfully",
  "schedule_id": 2
}
```

### Update Schedule

**Endpoint**: `PUT /api/schedules/{id}`

**Description**: Modify existing schedule

**Request Body**:
```json
{
  "schedule_value": "10:00",
  "enabled": false
}
```

### Delete Schedule

**Endpoint**: `DELETE /api/schedules/{id}`

**Description**: Remove schedule

**Response**:
```json
{
  "success": true,
  "message": "Schedule deleted successfully"
}
```

### Run Schedule Now

**Endpoint**: `POST /api/schedules/{id}/run`

**Description**: Execute schedule immediately (doesn't affect next scheduled run)

**Response**:
```json
{
  "success": true,
  "message": "Scan started",
  "scan_id": "scan_20241112_160000"
}
```

## Dashboard API

### Get Dashboard Metrics

**Endpoint**: `GET /api/dashboard/metrics`

**Description**: Get overview metrics for dashboard

**Response**:
```json
{
  "total_sites": 15,
  "total_scans": 127,
  "average_score": 78.5,
  "total_issues": 2345,
  "recent_scans": [...],
  "top_sites": [...]
}
```

### Get Accessibility Trends

**Endpoint**: `GET /api/dashboard/accessibility-trends`

**Query Parameters**:
- `days` - Number of days to include (default: 30)
- `site_id` - Filter by specific site

**Response**:
```json
{
  "labels": ["2024-11-01", "2024-11-02", ...],
  "datasets": [
    {
      "site_name": "Example.com",
      "data": [85.2, 85.8, 86.1, ...]
    }
  ]
}
```

### Get Issue Distribution

**Endpoint**: `GET /api/dashboard/issues`

**Description**: Get issues breakdown by severity

**Response**:
```json
{
  "critical": 45,
  "serious": 128,
  "moderate": 287,
  "minor": 156
}
```

## System API

### Get System Status

**Endpoint**: `GET /api/system/status`

**Description**: System health and status

**Response**:
```json
{
  "database": {
    "status": "connected",
    "size_mb": 45.2
  },
  "scanner": {
    "status": "available",
    "chrome_version": "119.0.6045.105",
    "chromedriver_version": "119.0.6045.105"
  },
  "scheduler": {
    "status": "running",
    "active_jobs": 5
  },
  "disk_space": {
    "available_gb": 125.3,
    "results_size_gb": 2.3
  }
}
```

### Get Activity Log

**Endpoint**: `GET /api/system/activity`

**Query Parameters**:
- `limit` - Number of records (default: 100)
- `event_type` - Filter by event type
- `since` - ISO 8601 timestamp

**Response**:
```json
{
  "activity": [
    {
      "timestamp": "2024-11-12T10:30:00",
      "event_type": "scan_complete",
      "event_name": "Harvard University",
      "details": "20 pages scanned, 42 issues found"
    }
  ]
}
```

## Error Responses

All endpoints may return error responses:

### 400 Bad Request

```json
{
  "success": false,
  "error": "Invalid request",
  "message": "Missing required parameter: url"
}
```

### 401 Unauthorized

```json
{
  "success": false,
  "error": "Unauthorized",
  "message": "Please log in to access this resource"
}
```

### 403 Forbidden

```json
{
  "success": false,
  "error": "Forbidden",
  "message": "Admin privileges required"
}
```

### 404 Not Found

```json
{
  "success": false,
  "error": "Not found",
  "message": "Site with ID 999 not found"
}
```

### 500 Internal Server Error

```json
{
  "success": false,
  "error": "Internal server error",
  "message": "An unexpected error occurred"
}
```

## Rate Limiting

Currently no rate limiting is enforced. For production deployments, consider:

- Implementing rate limiting middleware
- Using API keys for authentication
- Monitoring API usage

## Examples

### Python

```python
import requests

# Login
session = requests.Session()
response = session.post('http://localhost:5001/login', json={
    'username': 'admin',
    'password': 'admin'
})

# Get sites
sites = session.get('http://localhost:5001/api/sites').json()

# Start scan
scan = session.post('http://localhost:5001/api/scans/start', json={
    'config_name': 'config_standard_scan.json',
    'site_url': 'https://www.example.com'
}).json()

print(f"Scan started: {scan['scan_id']}")
```

### cURL

```bash
# Login and save cookies
curl -c cookies.txt -X POST http://localhost:5001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Get sites
curl -b cookies.txt http://localhost:5001/api/sites

# Start scan
curl -b cookies.txt -X POST http://localhost:5001/api/scans/start \
  -H "Content-Type: application/json" \
  -d '{"config_name":"config_standard_scan.json","site_url":"https://www.example.com"}'
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const api = axios.create({
  baseURL: 'http://localhost:5001',
  withCredentials: true
});

// Login
await api.post('/login', {
  username: 'admin',
  password: 'admin'
});

// Get sites
const sites = await api.get('/api/sites');
console.log(sites.data);

// Start scan
const scan = await api.post('/api/scans/start', {
  config_name: 'config_standard_scan.json',
  site_url: 'https://www.example.com'
});
console.log(`Scan started: ${scan.data.scan_id}`);
```

## Next Steps

- Implement authentication with API keys
- Add webhooks for scan completion
- Create language-specific SDKs
- Add GraphQL endpoint

## Reference

- [Admin Interface Guide](admin-interface.md)
- [Configuration Guide](configuration.md)
- [Scheduling Guide](scheduling.md)
