"""
Core scheduling optimization engine using constraint programming
"""

from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import numpy as np
from ortools.sat.python import cp_model

from models.train import Train, TrainMovement, TrainConflict, calculate_priority_score
from models.infrastructure import RailwayNetwork, SectionStatus


class TrainScheduler:
    """
    AI-powered train scheduling optimizer using constraint programming
    """
    
    def __init__(self, network: RailwayNetwork):
        self.network = network
        self.model = None
        self.solver = None
        
    def optimize_schedule(self, trains: List[Train], time_horizon_hours: int = 24) -> Dict:
        """
        Optimize train schedule to maximize throughput and minimize delays
        
        Args:
            trains: List of trains to schedule
            time_horizon_hours: Planning horizon in hours
            
        Returns:
            Dictionary containing optimized schedule and metrics
        """
        
        # Initialize CP-SAT model
        self.model = cp_model.CpModel()
        
        # Time discretization (in minutes)
        time_units = time_horizon_hours * 60
        
        # Decision variables
        train_vars = {}
        section_vars = {}
        
        # Create variables for each train's movement through sections
        for train in trains:
            train_id = train.train_id
            train_vars[train_id] = {}
            
            route_sections = self._get_train_route(train)
            
            for i, section_id in enumerate(route_sections):
                # Start time variable for this section
                start_var = self.model.NewIntVar(0, time_units, f"start_{train_id}_{section_id}")
                # End time variable for this section
                end_var = self.model.NewIntVar(0, time_units, f"end_{train_id}_{section_id}")
                
                train_vars[train_id][section_id] = {
                    'start': start_var,
                    'end': end_var
                }
                
                # Constraint: end time must be after start time
                travel_time = self._estimate_section_travel_time(train, section_id)
                self.model.Add(end_var >= start_var + travel_time)
                
                # Sequential constraint: train must complete previous section before starting next
                if i > 0:
                    prev_section = route_sections[i-1]
                    prev_end = train_vars[train_id][prev_section]['end']
                    self.model.Add(start_var >= prev_end)
        
        # Section capacity constraints
        for section_id, section in self.network.sections.items():
            if section.max_trains == 1:  # Single occupancy sections
                trains_using_section = [
                    train for train in trains 
                    if section_id in self._get_train_route(train)
                ]
                
                # No overlap constraint for single-track sections
                for i in range(len(trains_using_section)):
                    for j in range(i + 1, len(trains_using_section)):
                        train1_id = trains_using_section[i].train_id
                        train2_id = trains_using_section[j].train_id
                        
                        if (train1_id in train_vars and section_id in train_vars[train1_id] and
                            train2_id in train_vars and section_id in train_vars[train2_id]):
                            
                            # Either train1 finishes before train2 starts, or vice versa
                            train1_end = train_vars[train1_id][section_id]['end']
                            train1_start = train_vars[train1_id][section_id]['start']
                            train2_end = train_vars[train2_id][section_id]['end']
                            train2_start = train_vars[train2_id][section_id]['start']
                            
                            # Create boolean variables for ordering
                            b = self.model.NewBoolVar(f"order_{train1_id}_{train2_id}_{section_id}")
                            
                            # If b is true, train1 goes first
                            self.model.Add(train1_end <= train2_start).OnlyEnforceIf(b)
                            # If b is false, train2 goes first
                            self.model.Add(train2_end <= train1_start).OnlyEnforceIf(b.Not())
        
        # Priority-based objective function
        objective_terms = []
        
        for train in trains:
            train_id = train.train_id
            priority_weight = calculate_priority_score(train)
            
            if train_id in train_vars:
                route_sections = self._get_train_route(train)
                if route_sections:
                    # Minimize completion time weighted by priority
                    last_section = route_sections[-1]
                    if last_section in train_vars[train_id]:
                        completion_time = train_vars[train_id][last_section]['end']
                        # Higher priority trains should complete earlier
                        objective_terms.append(completion_time * (10 - priority_weight))
        
        if objective_terms:
            self.model.Minimize(sum(objective_terms))
        
        # Solve the model
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = 30.0  # 30 second time limit for MVP
        
        status = self.solver.Solve(self.model)
        
        # Process results
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            return self._extract_solution(trains, train_vars)
        else:
            return {
                'status': 'infeasible',
                'message': 'No feasible schedule found',
                'trains': [],
                'conflicts': [],
                'metrics': {}
            }
    
    def detect_conflicts(self, trains: List[Train]) -> List[TrainConflict]:
        """
        Detect potential conflicts between trains
        
        Args:
            trains: List of trains to analyze
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        # Group trains by sections they use
        section_usage = {}
        for train in trains:
            route_sections = self._get_train_route(train)
            for section_id in route_sections:
                if section_id not in section_usage:
                    section_usage[section_id] = []
                section_usage[section_id].append(train)
        
        # Check for conflicts in each section
        for section_id, trains_in_section in section_usage.items():
            if len(trains_in_section) > 1:
                section = self.network.sections.get(section_id)
                if section and len(trains_in_section) > section.max_trains:
                    
                    # Create conflict for each pair of trains
                    for i in range(len(trains_in_section)):
                        for j in range(i + 1, len(trains_in_section)):
                            train1 = trains_in_section[i]
                            train2 = trains_in_section[j]
                            
                            conflict = TrainConflict(
                                conflict_id=f"CONF_{train1.train_id}_{train2.train_id}_{section_id}",
                                train_ids=[train1.train_id, train2.train_id],
                                section_id=section_id,
                                conflict_type="capacity_exceeded",
                                conflict_start=min(train1.scheduled_departure, train2.scheduled_departure),
                                conflict_end=max(train1.scheduled_arrival, train2.scheduled_arrival),
                                severity=3
                            )
                            conflicts.append(conflict)
        
        return conflicts
    
    def resolve_conflicts(self, conflicts: List[TrainConflict], trains: List[Train]) -> List[Dict]:
        """
        Propose resolution strategies for conflicts
        
        Args:
            conflicts: List of conflicts to resolve
            trains: List of all trains
            
        Returns:
            List of resolution recommendations
        """
        resolutions = []
        
        for conflict in conflicts:
            train_dict = {train.train_id: train for train in trains}
            conflicting_trains = [train_dict[tid] for tid in conflict.train_ids if tid in train_dict]
            
            if len(conflicting_trains) >= 2:
                # Sort by priority
                conflicting_trains.sort(key=lambda t: calculate_priority_score(t), reverse=True)
                
                higher_priority = conflicting_trains[0]
                lower_priority = conflicting_trains[1]
                
                resolution = {
                    'conflict_id': conflict.conflict_id,
                    'strategy': 'priority_based_delay',
                    'action': f"Delay {lower_priority.train_id} to allow {higher_priority.train_id} to proceed",
                    'affected_train': lower_priority.train_id,
                    'priority_train': higher_priority.train_id,
                    'estimated_delay': 15,  # minutes
                    'confidence': 0.8
                }
                resolutions.append(resolution)
        
        return resolutions
    
    def _get_train_route(self, train: Train) -> List[str]:
        """Get the route sections for a train"""
        if train.route_sections:
            return train.route_sections
        
        # Fallback: try to find route from origin to destination
        return self.network.get_route_sections(train.origin_station, train.destination_station)
    
    def _estimate_section_travel_time(self, train: Train, section_id: str) -> int:
        """Estimate travel time through a section in minutes"""
        section = self.network.sections.get(section_id)
        if not section:
            return 10  # Default 10 minutes
        
        # Calculate based on distance and speed
        distance_km = section.length_km
        speed_kmh = min(train.max_speed, section.max_speed_limit)
        
        if speed_kmh > 0:
            travel_hours = distance_km / speed_kmh
            travel_minutes = int(travel_hours * 60)
            
            # Add buffer based on section type
            buffer_minutes = {
                'platform': 5,
                'junction': 3,
                'single_line': 2,
                'double_line': 1
            }.get(section.section_type.value, 2)
            
            return max(travel_minutes + buffer_minutes, 1)
        
        return 10  # Default fallback
    
    def _extract_solution(self, trains: List[Train], train_vars: Dict) -> Dict:
        """Extract and format the optimization solution"""
        solution = {
            'status': 'optimal',
            'trains': [],
            'movements': [],
            'metrics': {}
        }
        
        total_delay = 0
        completed_trains = 0
        
        for train in trains:
            train_id = train.train_id
            
            if train_id in train_vars:
                train_schedule = {
                    'train_id': train_id,
                    'train_number': train.train_number,
                    'priority': train.priority.value,
                    'sections': []
                }
                
                route_sections = self._get_train_route(train)
                
                for section_id in route_sections:
                    if section_id in train_vars[train_id]:
                        start_time = self.solver.Value(train_vars[train_id][section_id]['start'])
                        end_time = self.solver.Value(train_vars[train_id][section_id]['end'])
                        
                        section_schedule = {
                            'section_id': section_id,
                            'start_time': start_time,
                            'end_time': end_time,
                            'duration': end_time - start_time
                        }
                        train_schedule['sections'].append(section_schedule)
                
                solution['trains'].append(train_schedule)
                completed_trains += 1
        
        # Calculate metrics
        solution['metrics'] = {
            'total_trains': len(trains),
            'scheduled_trains': completed_trains,
            'average_delay': total_delay / max(completed_trains, 1),
            'optimization_time': self.solver.WallTime(),
            'solver_status': self.solver.StatusName()
        }
        
        return solution


class RealTimeOptimizer:
    """
    Real-time optimization engine for handling dynamic updates
    """
    
    def __init__(self, scheduler: TrainScheduler):
        self.scheduler = scheduler
        self.current_schedule = None
        self.last_update = None
    
    def update_schedule(self, trains: List[Train], disruptions: List[Dict] = None) -> Dict:
        """
        Update schedule based on real-time information
        
        Args:
            trains: Current list of trains
            disruptions: List of disruptions (delays, breakdowns, etc.)
            
        Returns:
            Updated schedule
        """
        
        # Apply disruptions to trains
        if disruptions:
            trains = self._apply_disruptions(trains, disruptions)
        
        # Re-optimize with current state
        new_schedule = self.scheduler.optimize_schedule(trains)
        
        # Calculate impact of changes
        impact = self._calculate_schedule_impact(self.current_schedule, new_schedule)
        
        self.current_schedule = new_schedule
        self.last_update = datetime.now()
        
        return {
            'schedule': new_schedule,
            'impact': impact,
            'update_time': self.last_update.isoformat()
        }
    
    def _apply_disruptions(self, trains: List[Train], disruptions: List[Dict]) -> List[Train]:
        """Apply disruptions to train schedules"""
        # This is a simplified implementation
        # In production, this would handle various types of disruptions
        
        for disruption in disruptions:
            if disruption.get('type') == 'delay':
                train_id = disruption.get('train_id')
                delay_minutes = disruption.get('delay_minutes', 0)
                
                for train in trains:
                    if train.train_id == train_id:
                        # Add delay to departure time
                        train.scheduled_departure += timedelta(minutes=delay_minutes)
                        train.scheduled_arrival += timedelta(minutes=delay_minutes)
                        break
        
        return trains
    
    def _calculate_schedule_impact(self, old_schedule: Dict, new_schedule: Dict) -> Dict:
        """Calculate the impact of schedule changes"""
        if not old_schedule or not new_schedule:
            return {'changes': 0, 'affected_trains': []}
        
        # Simple comparison - in production, this would be more sophisticated
        return {
            'changes': abs(len(new_schedule.get('trains', [])) - len(old_schedule.get('trains', []))),
            'affected_trains': [train['train_id'] for train in new_schedule.get('trains', [])],
            'improvement': new_schedule.get('metrics', {}).get('average_delay', 0) < 
                          old_schedule.get('metrics', {}).get('average_delay', float('inf'))
        }
