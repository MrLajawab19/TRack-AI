# IRCTC API Integration for TrackAI

## Overview
This integration adds real-time train schedule data from IRCTC API (via RapidAPI) to the TrackAI system. Users can now search for any Indian train by number and get detailed schedule information including stations, timings, and current status.

## Features Implemented

### Backend (FastAPI)
- ✅ **New API Route**: `/api/train/{trainNo}` - Get train schedule by train number
- ✅ **Bulk API Route**: `/api/trains/bulk-schedule` - Get multiple train schedules
- ✅ **Cache Management**: In-memory caching with 5-minute expiry
- ✅ **Error Handling**: Comprehensive error handling and fallbacks
- ✅ **Security**: API key stored in `.env` file, not exposed to frontend

### Frontend (Enhanced HTML/JavaScript)
- ✅ **Search Interface**: Clean input field with search button
- ✅ **Loading States**: Spinner animation during API calls
- ✅ **Error States**: User-friendly error messages
- ✅ **Train Details Display**: 
  - Train name and number
  - Source and destination stations
  - Current status with color-coded indicators
  - Complete station schedule with timings
- ✅ **Auto-refresh**: Updates every 30 seconds
- ✅ **Professional UI**: Dark theme following TrackAI design system

### Security Features
- ✅ **Environment Variables**: API key stored securely in `.env`
- ✅ **Backend Proxy**: Frontend never directly accesses external API
- ✅ **Rate Limiting**: Built-in caching to reduce API calls
- ✅ **Input Validation**: Train number validation and sanitization

## API Endpoints

### GET `/api/train/{train_no}`
Fetch real-time schedule for a specific train.

**Example Request:**
```
GET /api/train/12936
```

**Example Response:**
```json
{
  "success": true,
  "train_number": "12936",
  "train_name": "Nesari Express",
  "train_type": "Express",
  "source_station": {
    "station_code": "NDLS",
    "station_name": "New Delhi",
    "departure_time": "15:50"
  },
  "destination_station": {
    "station_code": "SBC",
    "station_name": "Bangalore City",
    "arrival_time": "04:00"
  },
  "total_stations": 25,
  "stations": [...],
  "current_status": {
    "status": "running",
    "current_station": "En Route",
    "delay_minutes": 0
  },
  "last_updated": "2025-01-24T12:30:00",
  "data_source": "IRCTC API"
}
```

### POST `/api/trains/bulk-schedule`
Fetch schedules for multiple trains (max 10).

**Request Body:**
```json
["12936", "12937", "12938"]
```

### DELETE `/api/train-cache`
Clear the train data cache.

### GET `/api/train-cache/stats`
Get cache statistics.

## Setup Instructions

### 1. Install Dependencies
```bash
pip install requests httpx python-dotenv loguru
```

### 2. Configure Environment
Create/update `.env` file:
```env
RAPIDAPI_KEY=your_rapidapi_key_here
RAPIDAPI_HOST=irctc1.p.rapidapi.com
```

### 3. Start the Server
```bash
python main.py
```

### 4. Test the Integration
```bash
python test_irctc_integration.py
```

## Usage

### Frontend Usage
1. Navigate to the "Train Status" section
2. Enter a train number (e.g., 12936) in the search box
3. Click "Search" or press Enter
4. View detailed train schedule and status
5. Data automatically refreshes every 30 seconds

### API Usage
```python
import httpx

async def get_train_info(train_no):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:8000/api/train/{train_no}")
        return response.json()

# Usage
train_data = await get_train_info("12936")
```

## Color Scheme (Professional Dark Theme)
Following the TrackAI design system:

- **Running Status**: Light Green (#b5cea8)
- **Delayed Status**: Orange (#f39c12) 
- **Scheduled Status**: Light Blue (#569cd6)
- **Error/Cancelled**: Red (#f44747)
- **Background**: Dark Gray (#1e1e1e to #2b2b2b)
- **Text**: Light Gray (#d4d4d4)

## Caching Strategy
- **Cache Duration**: 5 minutes per train
- **Cache Type**: In-memory (production should use Redis)
- **Cache Key**: Train number
- **Auto-cleanup**: Expired entries are automatically ignored

## Error Handling
- **Network Timeouts**: 30-second timeout with retry logic
- **Invalid Train Numbers**: User-friendly error messages
- **API Failures**: Graceful degradation with cached data
- **Rate Limiting**: Built-in caching reduces API calls

## Performance Features
- **Concurrent Requests**: Bulk API supports multiple trains
- **Caching**: Reduces redundant API calls
- **Auto-refresh**: Smart updates without user intervention
- **Lazy Loading**: Station details loaded on demand

## Testing
Run the test script to verify integration:
```bash
python test_irctc_integration.py
```

Expected output:
```
🚂 Testing IRCTC API Integration
==================================================
📡 Fetching schedule for train 12936...
✅ API Response received
📊 Success: True
🚆 Train Name: Nesari Express
...
✅ Integration test completed successfully!
```

## Troubleshooting

### Common Issues
1. **"RAPIDAPI_KEY not found"**: Check `.env` file exists and contains the API key
2. **"Request timeout"**: Check internet connection and API status
3. **"Train not found"**: Verify train number is correct and active
4. **Cache issues**: Use `/api/train-cache` endpoint to clear cache

### Debug Mode
Set `DEBUG=True` in `.env` for detailed logging.

## Production Considerations
- Replace in-memory cache with Redis
- Add rate limiting middleware
- Implement proper logging
- Add monitoring and alerting
- Use connection pooling for external APIs
- Add API key rotation mechanism

## Future Enhancements
- Real-time GPS tracking integration
- Push notifications for delays
- Historical data analysis
- Predictive delay algorithms
- Mobile app support
- WebSocket for real-time updates

## API Documentation
Full API documentation is available at: `http://localhost:8000/docs` when the server is running.
