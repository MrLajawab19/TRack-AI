"""
IRCTC API Service for real-time train schedule data
"""

import os
import httpx
import asyncio
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

class IRCTCService:
    """Service class for interacting with IRCTC API via RapidAPI"""
    
    def __init__(self):
        self.base_url = "https://irctc1.p.rapidapi.com"
        self.api_key = os.getenv("RAPIDAPI_KEY")
        self.api_host = os.getenv("RAPIDAPI_HOST", "irctc1.p.rapidapi.com")
        
        if not self.api_key:
            logger.warning("RAPIDAPI_KEY not found in environment variables")
        
        self.headers = {
            "x-rapidapi-host": self.api_host,
            "x-rapidapi-key": self.api_key
        }
        
        # In-memory cache for train data (in production, use Redis or similar)
        self._cache: Dict[str, Dict] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self.cache_duration = timedelta(minutes=5)  # Cache for 5 minutes
    
    def _is_cache_valid(self, train_no: str) -> bool:
        """Check if cached data is still valid"""
        if train_no not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[train_no]
    
    def _cache_data(self, train_no: str, data: Dict):
        """Cache train data with expiry"""
        self._cache[train_no] = data
        self._cache_expiry[train_no] = datetime.now() + self.cache_duration
    
    async def get_train_schedule(self, train_no: str) -> Dict:
        """
        Get train schedule from IRCTC API
        
        Args:
            train_no: Train number (e.g., "12936")
            
        Returns:
            Dict containing train schedule information
        """
        try:
            # Check cache first
            if self._is_cache_valid(train_no):
                logger.info(f"Returning cached data for train {train_no}")
                return self._cache[train_no]
            
            # Make API request
            url = f"{self.base_url}/api/v1/getTrainScheduleV2"
            params = {"trainNo": train_no}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    processed_data = self._process_train_data(data, train_no)
                    
                    # Cache the processed data
                    self._cache_data(train_no, processed_data)
                    
                    logger.info(f"Successfully fetched train schedule for {train_no}")
                    return processed_data
                else:
                    logger.error(f"API request failed with status {response.status_code}: {response.text}")
                    return self._get_error_response(f"API request failed: {response.status_code}")
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout while fetching train {train_no}")
            return self._get_error_response("Request timeout")
        except Exception as e:
            logger.error(f"Error fetching train schedule for {train_no}: {str(e)}")
            return self._get_error_response(str(e))
    
    def _process_train_data(self, raw_data: Dict, train_no: str) -> Dict:
        """
        Process raw API response into a clean format
        
        Args:
            raw_data: Raw response from IRCTC API
            train_no: Train number
            
        Returns:
            Processed train data
        """
        try:
            # Handle different possible response structures
            if "status" in raw_data and not raw_data.get("status"):
                return self._get_error_response("Train not found or invalid train number")
            
            # Extract train information
            train_info = raw_data.get("data", {}) if "data" in raw_data else raw_data
            
            # Get basic train details
            train_name = train_info.get("train_name", f"Train {train_no}")
            train_type = train_info.get("train_type", "Unknown")
            
            # Process stations/schedule
            stations = train_info.get("stations", [])
            if not stations and "schedule" in train_info:
                stations = train_info["schedule"]
            
            processed_stations = []
            for station in stations:
                processed_station = {
                    "station_code": station.get("station_code", ""),
                    "station_name": station.get("station_name", ""),
                    "arrival_time": station.get("arrival_time", ""),
                    "departure_time": station.get("departure_time", ""),
                    "halt_time": station.get("halt_time", "0 min"),
                    "distance": station.get("distance", 0),
                    "day": station.get("day", 1)
                }
                processed_stations.append(processed_station)
            
            # Determine current status (this would be enhanced with real-time data)
            current_status = self._determine_train_status(train_info)
            
            return {
                "success": True,
                "train_number": train_no,
                "train_name": train_name,
                "train_type": train_type,
                "source_station": processed_stations[0] if processed_stations else {},
                "destination_station": processed_stations[-1] if processed_stations else {},
                "total_stations": len(processed_stations),
                "stations": processed_stations,
                "current_status": current_status,
                "last_updated": datetime.now().isoformat(),
                "data_source": "IRCTC API"
            }
            
        except Exception as e:
            logger.error(f"Error processing train data: {str(e)}")
            return self._get_error_response(f"Data processing error: {str(e)}")
    
    def _determine_train_status(self, train_info: Dict) -> Dict:
        """
        Determine current train status based on available information
        This is a simplified version - in production, you'd use real-time tracking data
        """
        current_time = datetime.now()
        
        # Default status
        status = {
            "status": "scheduled",
            "current_station": "Unknown",
            "delay_minutes": 0,
            "next_station": "Unknown",
            "estimated_arrival": "Unknown"
        }
        
        # In a real implementation, you would:
        # 1. Get current GPS location
        # 2. Compare with schedule
        # 3. Calculate delays
        # 4. Determine current/next stations
        
        # For now, return a simulated status
        status["status"] = "running"  # Could be: scheduled, running, delayed, cancelled
        status["current_station"] = "En Route"
        
        return status
    
    def _get_error_response(self, error_message: str) -> Dict:
        """Generate standardized error response"""
        return {
            "success": False,
            "error": error_message,
            "train_number": None,
            "train_name": None,
            "stations": [],
            "current_status": {
                "status": "error",
                "current_station": "Unknown",
                "delay_minutes": 0,
                "next_station": "Unknown",
                "estimated_arrival": "Unknown"
            },
            "last_updated": datetime.now().isoformat(),
            "data_source": "IRCTC API"
        }
    
    async def get_multiple_trains(self, train_numbers: List[str]) -> Dict[str, Dict]:
        """
        Get schedule data for multiple trains concurrently
        
        Args:
            train_numbers: List of train numbers
            
        Returns:
            Dict mapping train numbers to their schedule data
        """
        tasks = [self.get_train_schedule(train_no) for train_no in train_numbers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        train_data = {}
        for i, train_no in enumerate(train_numbers):
            if isinstance(results[i], Exception):
                train_data[train_no] = self._get_error_response(str(results[i]))
            else:
                train_data[train_no] = results[i]
        
        return train_data
    
    def clear_cache(self):
        """Clear all cached data"""
        self._cache.clear()
        self._cache_expiry.clear()
        logger.info("Train data cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        valid_entries = sum(1 for train_no in self._cache if self._is_cache_valid(train_no))
        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self._cache) - valid_entries
        }

# Global service instance
irctc_service = IRCTCService()
