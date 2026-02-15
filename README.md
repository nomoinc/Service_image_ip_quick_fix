# MongoDB URL Migration Service

A Python service that continuously polls MongoDB collections and replaces old IP addresses with new domain URLs.

## Features

- ✅ Polls two MongoDB collections every second
- ✅ Replaces `http://155.248.254.206:9000` with `https://images.nomo.software`
- ✅ Handles multiple URL fields in each collection
- ✅ Automatic reconnection on errors
- ✅ Detailed logging to file and console
- ✅ Statistics tracking

## Collections Monitored

1. **wearapp_groundtruth.imageUrl**
   - Fields checked: `minioUrlOracle`, `minioUrlThinker`, `minioUrl`, `s3Url`

2. **wearapp_user.userUploadedClothes**
   - Fields checked: `imageUrl`, `segmentedImageUrl`
   - Automatically updates `updatedAt` timestamp

## Installation

1. **Clone or download the files**

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
```bash
cp .env.example .env
```

Edit `.env` with your MongoDB connection details:
```env
MONGO_URI=mongodb://your-mongo-host:27017/
MONGO_DB_NAME=wearapp
GROUNDTRUTH_COLLECTION=imageUrl
USER_CLOTHES_COLLECTION=userUploadedClothes
OLD_URL=http://155.248.254.206:9000
NEW_URL=https://images.nomo.software
POLL_INTERVAL=1
```

## Usage

### Run the service:
```bash
python url_migration_service.py
```

### Run as a background service:
```bash
# Linux/Mac
nohup python url_migration_service.py &

# Or use screen
screen -S url_migration
python url_migration_service.py
# Press Ctrl+A then D to detach
```

### Stop the service:
Press `Ctrl+C` for graceful shutdown with statistics.

## Logging

Logs are written to:
- **Console**: Real-time output
- **File**: `url_migration.log` in the same directory

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://localhost:27017/` | MongoDB connection string |
| `MONGO_DB_NAME` | `wearapp` | Database name |
| `GROUNDTRUTH_COLLECTION` | `imageUrl` | Groundtruth collection name |
| `USER_CLOTHES_COLLECTION` | `userUploadedClothes` | User clothes collection name |
| `OLD_URL` | `http://155.248.254.206:9000` | URL pattern to replace |
| `NEW_URL` | `https://images.nomo.software` | New URL pattern |
| `POLL_INTERVAL` | `1` | Polling interval in seconds |

## Example Output

```
2025-02-15 10:30:00 - __main__ - INFO - Starting URL Migration Service...
2025-02-15 10:30:00 - __main__ - INFO - Connected to MongoDB: mongodb://localhost:27017/
2025-02-15 10:30:00 - __main__ - INFO - Database: wearapp
2025-02-15 10:30:00 - __main__ - INFO - Old URL: http://155.248.254.206:9000
2025-02-15 10:30:00 - __main__ - INFO - New URL: https://images.nomo.software
2025-02-15 10:30:00 - __main__ - INFO - Polling interval: 1 second(s)
2025-02-15 10:30:00 - __main__ - INFO - Service running. Press Ctrl+C to stop.
2025-02-15 10:30:01 - __main__ - INFO - Updated groundtruth document: ObjectId('688d8ef34a99a6a32dd168f0')
2025-02-15 10:30:01 - __main__ - INFO - Groundtruth: Updated 1 documents
2025-02-15 10:30:01 - __main__ - INFO - Updated user clothes document: ObjectId('507f1f77bcf86cd799439011')
2025-02-15 10:30:01 - __main__ - INFO - User Clothes: Updated 1 documents
```

## Production Deployment

### Using systemd (Linux):

1. Create service file `/etc/systemd/system/url-migration.service`:
```ini
[Unit]
Description=MongoDB URL Migration Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/service
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /path/to/url_migration_service.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable url-migration
sudo systemctl start url-migration
sudo systemctl status url-migration
```

### Using Docker:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY url_migration_service.py .
COPY .env .
CMD ["python", "url_migration_service.py"]
```

Build and run:
```bash
docker build -t url-migration .
docker run -d --name url-migration --restart unless-stopped url-migration
```

## Troubleshooting

**Connection errors:**
- Verify MongoDB is running and accessible
- Check `MONGO_URI` in `.env` file
- Ensure network connectivity

**No documents being updated:**
- Verify collection names are correct
- Check that documents actually contain the old URL
- Review logs for any errors

**High CPU usage:**
- Increase `POLL_INTERVAL` to reduce polling frequency
- Consider running during off-peak hours for large migrations

## License

MIT
