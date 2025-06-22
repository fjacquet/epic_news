# Epic News Docker Deployment Guide

This document provides instructions for deploying the Epic News application using Docker containers.

## Container Images

Epic News consists of two main services:

1. **API Service**: Provides the backend API functionality
   - Image: `fjacquet/epic-news-api:latest`
   - Port: 8000

2. **Streamlit UI**: Provides the web interface
   - Image: `fjacquet/epic-news-streamlit:latest`
   - Port: 8501

## Required Volumes and Files

For proper functioning of the containers, you need to mount the following volumes:

### Environment Variables (.env)

Create a `.env` file with the following variables (adjust values as needed):

```
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Database Configuration
DB_PATH=/app/db

# Data Paths
DATA_PATH=/app/data
OUTPUT_PATH=/app/output

# Add any other required environment variables here
# Such as API keys, credentials, etc.
```

### Data Directory

The `/data` directory should contain:

- `feedly.opml`: OPML file with RSS feed subscriptions

### Database Directory

The `/db` directory contains:

- `chroma.sqlite3`: SQLite database file for vector storage
- Various UUID-named directories for database-related storage

### Output Directory

The `/output/dashboard_data` directory is used for storing generated dashboard data.

## Docker Compose Deployment

We provide three docker-compose configurations:

1. **Full Deployment**: Runs both API and Streamlit services
2. **API Only**: Runs only the API service
3. **Streamlit Only**: Runs only the Streamlit service

### Prerequisites

- Docker and Docker Compose installed
- `.env` file created with required variables
- Data directories prepared with necessary files

## Usage Instructions

### Full Deployment

```bash
docker-compose up -d
```

### API Only Deployment

```bash
docker-compose -f docker-compose.api.yml up -d
```

### Streamlit Only Deployment

```bash
docker-compose -f docker-compose.streamlit.yml up -d
```

## Accessing the Services

- API: <http://localhost:8000>
- Streamlit UI: <http://localhost:8501>

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure the db volume is properly mounted
   - Check file permissions on the db directory

2. **Missing Data Files**
   - Verify that the data directory contains the required feedly.opml file

3. **Environment Variables**
   - Confirm all required environment variables are set in the .env file

### Logs

To view container logs:

```bash
# API logs
docker-compose logs api

# Streamlit logs
docker-compose logs streamlit
```

## Maintenance

### Updating Images

Pull the latest images:

```bash
docker-compose pull
```

Restart services with new images:

```bash
docker-compose up -d
```

### Backup

Backup important data regularly:

```bash
# Backup database
cp -r ./db ./db_backup_$(date +%Y%m%d)

# Backup data
cp -r ./data ./data_backup_$(date +%Y%m%d)
```
