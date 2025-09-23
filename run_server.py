"""
Simple HTTP server to run the Train Traffic Control System
"""

import http.server
import socketserver
import webbrowser
import threading
import time
import json
from datetime import datetime, timedelta
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our models
try:
    from models.train import Train, TrainType, TrainPriority
    from models.infrastructure import create_sample_network
    from optimization.simple_scheduler import SimpleTrainScheduler
    print("✅ All modules imported successfully!")
except ImportError as e:
    print(f"❌ Import error: {e}")

# Global data
network = create_sample_network()
scheduler = SimpleTrainScheduler(network)
active_trains = []
current_schedule = None

class TrainControlHandler(http.server.SimpleHTTPRequestHandler):
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
        global active_trains, current_schedule
        
        try:
            if self.path == '/api/health':
                response = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0.0"
                }
                self.send_json_response(response)
            
            elif self.path == '/api/sample-data' and self.command == 'POST':
                # Create sample trains
                active_trains = [
                    Train(
                        train_id="T001",
                        train_number="12345",
                        train_name="Express 1",
                        train_type=TrainType.EXPRESS,
                        priority=TrainPriority.HIGH,
                        origin_station="SEC_001",
                        destination_station="SEC_004",
                        scheduled_departure=datetime.now(),
                        scheduled_arrival=datetime.now() + timedelta(hours=2),
                        route_sections=["SEC_001", "SEC_003", "SEC_004"]
                    ),
                    Train(
                        train_id="T002",
                        train_number="67890",
                        train_name="Local 1",
                        train_type=TrainType.LOCAL,
                        priority=TrainPriority.MEDIUM,
                        origin_station="SEC_002",
                        destination_station="SEC_005",
                        scheduled_departure=datetime.now() + timedelta(minutes=30),
                        scheduled_arrival=datetime.now() + timedelta(hours=2, minutes=30),
                        route_sections=["SEC_002", "SEC_003", "SEC_005"]
                    ),
                    Train(
                        train_id="T003",
                        train_number="11111",
                        train_name="Freight 1",
                        train_type=TrainType.FREIGHT,
                        priority=TrainPriority.LOW,
                        origin_station="SEC_001",
                        destination_station="SEC_002",
                        scheduled_departure=datetime.now() + timedelta(hours=1),
                        scheduled_arrival=datetime.now() + timedelta(hours=4),
                        route_sections=["SEC_001", "SEC_003", "SEC_002"]
                    )
                ]
                
                response = {
                    "status": "success",
                    "message": f"Created {len(active_trains)} sample trains",
                    "trains": [t.train_id for t in active_trains]
                }
                self.send_json_response(response)
            
            elif self.path == '/api/trains':
                # Convert trains to dict format
                trains_data = []
                for train in active_trains:
                    trains_data.append({
                        "train_id": train.train_id,
                        "train_number": train.train_number,
                        "train_name": train.train_name,
                        "train_type": train.train_type.value,
                        "priority": train.priority.value,
                        "current_status": train.current_status.value,
                        "origin_station": train.origin_station,
                        "destination_station": train.destination_station
                    })
                self.send_json_response(trains_data)
            
            elif self.path == '/api/optimize' and self.command == 'POST':
                if active_trains:
                    current_schedule = scheduler.optimize_schedule(active_trains)
                    response = {
                        "status": "success",
                        "message": "Schedule optimized successfully",
                        "schedule": current_schedule
                    }
                else:
                    response = {
                        "status": "error",
                        "message": "No trains to optimize"
                    }
                self.send_json_response(response)
            
            elif self.path == '/api/conflicts/detect' and self.command == 'POST':
                conflicts = scheduler.detect_conflicts(active_trains)
                conflicts_data = []
                for conflict in conflicts:
                    conflicts_data.append({
                        "conflict_id": conflict.conflict_id,
                        "train_ids": conflict.train_ids,
                        "section_id": conflict.section_id,
                        "conflict_type": conflict.conflict_type,
                        "severity": conflict.severity
                    })
                self.send_json_response(conflicts_data)
            
            elif self.path == '/api/conflicts/resolve' and self.command == 'POST':
                conflicts = scheduler.detect_conflicts(active_trains)
                resolutions = scheduler.resolve_conflicts(conflicts, active_trains)
                self.send_json_response(resolutions)
            
            elif self.path == '/api/sections':
                sections_data = []
                for section_id, section in network.sections.items():
                    sections_data.append({
                        "section_id": section.section_id,
                        "section_name": section.section_name,
                        "section_type": section.section_type.value,
                        "length_km": section.length_km,
                        "current_status": section.current_status.value,
                        "occupying_trains": section.occupying_trains,
                        "max_trains": section.max_trains
                    })
                self.send_json_response(sections_data)
            
            elif self.path == '/api/metrics':
                total_trains = len(active_trains)
                running_trains = len([t for t in active_trains if t.current_status.value == "running"])
                delayed_trains = len([t for t in active_trains if t.current_status.value == "delayed"])
                
                available_sections = len(network.get_available_sections())
                total_sections = len(network.sections)
                
                metrics = {
                    "trains": {
                        "total": total_trains,
                        "running": running_trains,
                        "delayed": delayed_trains,
                        "on_time_percentage": ((total_trains - delayed_trains) / max(total_trains, 1)) * 100
                    },
                    "infrastructure": {
                        "total_sections": total_sections,
                        "available_sections": available_sections,
                        "utilization_percentage": ((total_sections - available_sections) / max(total_sections, 1)) * 100
                    },
                    "schedule": {
                        "has_active_schedule": current_schedule is not None
                    },
                    "timestamp": datetime.now().isoformat()
                }
                self.send_json_response(metrics)
            
            elif self.path == '/api/schedule':
                if current_schedule:
                    response = {
                        "status": "success",
                        "schedule": current_schedule,
                        "last_updated": datetime.now().isoformat()
                    }
                else:
                    response = {
                        "status": "no_schedule",
                        "message": "No schedule available. Run optimization first."
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
    
    print("🚂 Starting AI-Powered Train Traffic Control System...")
    print(f"📊 Dashboard will be available at: http://localhost:{PORT}")
    print("🔧 Health Check at: http://localhost:8000/api/health")
    print("📖 Press Ctrl+C to stop the server")
    
    try:
        with socketserver.TCPServer(("", PORT), TrainControlHandler) as httpd:
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
