"""
Simple HTTP server to serve the TrackAI authentication system
No external dependencies required - uses only Python standard library
"""

import http.server
import socketserver
import webbrowser
import threading
import time
import json
from datetime import datetime, timedelta
import os

class TrackAIHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        elif self.path.startswith('/api/'):
            self.handle_api_request()
            return
        
        return super().do_GET()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            self.send_error(404)
    
    def handle_api_request(self):
        """Handle API requests with mock data for demo purposes"""
        try:
            if self.path == '/api/health':
                response = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0.0"
                }
                self.send_json_response(response)
            
            elif self.path == '/api/sample-data' and self.command == 'POST':
                response = {
                    "status": "success",
                    "message": "Created 3 sample trains",
                    "trains": ["T001", "T002", "T003"]
                }
                self.send_json_response(response)
            
            elif self.path == '/api/trains':
                # Mock train data
                trains_data = [
                    {
                        "train_id": "T001",
                        "train_number": "12345",
                        "train_name": "Express 1",
                        "train_type": "express",
                        "priority": "high",
                        "current_status": "running",
                        "origin_station": "Station A",
                        "destination_station": "Station D"
                    },
                    {
                        "train_id": "T002",
                        "train_number": "67890",
                        "train_name": "Local 1",
                        "train_type": "local",
                        "priority": "medium",
                        "current_status": "delayed",
                        "origin_station": "Station B",
                        "destination_station": "Station E"
                    },
                    {
                        "train_id": "T003",
                        "train_number": "11111",
                        "train_name": "Freight 1",
                        "train_type": "freight",
                        "priority": "low",
                        "current_status": "scheduled",
                        "origin_station": "Station A",
                        "destination_station": "Station B"
                    }
                ]
                self.send_json_response(trains_data)
            
            elif self.path == '/api/optimize' and self.command == 'POST':
                response = {
                    "status": "success",
                    "message": "Schedule optimized successfully",
                    "schedule": {
                        "status": "optimized",
                        "trains": [
                            {"train_id": "T001", "priority": "high", "sections": ["SEC_001", "SEC_003", "SEC_004"]},
                            {"train_id": "T002", "priority": "medium", "sections": ["SEC_002", "SEC_003", "SEC_005"]},
                            {"train_id": "T003", "priority": "low", "sections": ["SEC_001", "SEC_003", "SEC_002"]}
                        ],
                        "metrics": {"solver_status": "OPTIMAL"}
                    }
                }
                self.send_json_response(response)
            
            elif self.path == '/api/conflicts/detect' and self.command == 'POST':
                # Mock conflict detection
                conflicts = []
                self.send_json_response(conflicts)
            
            elif self.path == '/api/conflicts/resolve' and self.command == 'POST':
                # Mock conflict resolution
                resolutions = []
                self.send_json_response(resolutions)
            
            elif self.path == '/api/sections':
                # Mock section data
                sections_data = [
                    {"section_id": "SEC_001", "section_name": "Main Line 1", "section_type": "double_line", "length_km": 15.5, "current_status": "available", "occupying_trains": [], "max_trains": 2},
                    {"section_id": "SEC_002", "section_name": "Main Line 2", "section_type": "double_line", "length_km": 12.3, "current_status": "occupied", "occupying_trains": ["T002"], "max_trains": 2},
                    {"section_id": "SEC_003", "section_name": "Junction A", "section_type": "junction", "length_km": 2.1, "current_status": "available", "occupying_trains": [], "max_trains": 1},
                    {"section_id": "SEC_004", "section_name": "Platform 1", "section_type": "platform", "length_km": 0.4, "current_status": "occupied", "occupying_trains": ["T001"], "max_trains": 1},
                    {"section_id": "SEC_005", "section_name": "Platform 2", "section_type": "platform", "length_km": 0.4, "current_status": "maintenance", "occupying_trains": [], "max_trains": 1}
                ]
                self.send_json_response(sections_data)
            
            elif self.path == '/api/metrics':
                # Mock metrics
                metrics = {
                    "trains": {
                        "total": 3,
                        "running": 1,
                        "delayed": 1,
                        "on_time_percentage": 66.7
                    },
                    "infrastructure": {
                        "total_sections": 5,
                        "available_sections": 2,
                        "utilization_percentage": 60.0
                    },
                    "schedule": {
                        "has_active_schedule": True
                    },
                    "timestamp": datetime.now().isoformat()
                }
                self.send_json_response(metrics)
            
            elif self.path == '/api/schedule':
                response = {
                    "status": "success",
                    "schedule": {
                        "status": "optimized",
                        "trains": [
                            {"train_id": "T001", "priority": "high", "sections": ["SEC_001", "SEC_003", "SEC_004"]},
                            {"train_id": "T002", "priority": "medium", "sections": ["SEC_002", "SEC_003", "SEC_005"]},
                            {"train_id": "T003", "priority": "low", "sections": ["SEC_001", "SEC_003", "SEC_002"]}
                        ],
                        "metrics": {"solver_status": "OPTIMAL"}
                    },
                    "last_updated": datetime.now().isoformat()
                }
                self.send_json_response(response)
            
            # IRCTC API endpoints (mock)
            elif self.path.startswith('/api/train/'):
                train_number = self.path.split('/')[-1]
                # Mock train schedule data
                response = {
                    "success": True,
                    "train_number": train_number,
                    "train_name": f"Sample Train {train_number}",
                    "source_station": {"station_name": "New Delhi", "station_code": "NDLS", "departure_time": "06:00"},
                    "destination_station": {"station_name": "Mumbai Central", "station_code": "BCT", "arrival_time": "14:30"},
                    "current_status": {"status": "running", "delay_minutes": 0},
                    "total_stations": 12,
                    "last_updated": datetime.now().isoformat(),
                    "stations": [
                        {"station_name": "New Delhi", "station_code": "NDLS", "arrival_time": None, "departure_time": "06:00", "halt_time": "Start", "distance": "0 km"},
                        {"station_name": "Gwalior", "station_code": "GWL", "arrival_time": "09:15", "departure_time": "09:20", "halt_time": "5 min", "distance": "319 km"},
                        {"station_name": "Bhopal", "station_code": "BPL", "arrival_time": "12:10", "departure_time": "12:15", "halt_time": "5 min", "distance": "707 km"},
                        {"station_name": "Mumbai Central", "station_code": "BCT", "arrival_time": "14:30", "departure_time": None, "halt_time": "End", "distance": "1384 km"}
                    ]
                }
                self.send_json_response(response)
            
            else:
                self.send_error(404, "API endpoint not found")
        
        except Exception as e:
            error_response = {
                "status": "error",
                "message": str(e)
            }
            self.send_json_response(error_response, status_code=500)
    
    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        json_data = json.dumps(data, default=str)
        self.wfile.write(json_data.encode())

def run_server():
    PORT = 8000
    
    print("🚂 Starting TrackAI - Smart Train Traffic Control System...")
    print(f"📊 Dashboard available at: http://localhost:{PORT}")
    print(f"🔐 Authentication page: http://localhost:{PORT}/auth.html")
    print(f"🔧 Health Check: http://localhost:{PORT}/api/health")
    print("📖 Press Ctrl+C to stop the server")
    print()
    
    try:
        with socketserver.TCPServer(("", PORT), TrackAIHandler) as httpd:
            print(f"✅ Server running on port {PORT}")
            
            # Open browser after a short delay
            def open_browser():
                time.sleep(2)
                webbrowser.open(f'http://localhost:{PORT}')
            
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            httpd.serve_forever()
    
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    run_server()
