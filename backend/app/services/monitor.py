import os
import psutil
import time
import logging
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger("omega.monitor")

class HostBackgroundMonitor:
    """
    Background Monitor that collects real-time local machine parameters
    and files modifications inside a protected directory.
    """
    def __init__(self, protected_dir_path: str = None):
        if protected_dir_path is None:
            # Set default protected folder path
            self.protected_dir = Path(__file__).resolve().parent.parent / "protected_folder"
        else:
            self.protected_dir = Path(protected_dir_path)
            
        # Ensure protected folder exists
        self.protected_dir.mkdir(parents=True, exist_ok=True)
        
        # Track file states (filepath -> mtime)
        self.file_states: Dict[str, float] = {}
        self._initialize_file_states()
        
        # Track processes to detect new process creation
        self.known_pids: Set[int] = set()
        self._initialize_known_pids()
        
        # Track simulated / runtime events
        self.failed_logins = 0
        self.scada_commands_count = 0
        self.new_processes_detected: List[str] = []
        self.file_changes_detected: List[str] = []
        
    def _initialize_file_states(self):
        try:
            for file in self.protected_dir.rglob("*"):
                if file.is_file():
                    self.file_states[str(file)] = file.stat().st_mtime
        except Exception as e:
            logger.error(f"Error initializing protected folder states: {e}")

    def _initialize_known_pids(self):
        try:
            self.known_pids = {p.pid for p in psutil.process_iter(attrs=['pid'])}
        except Exception as e:
            logger.error(f"Error initializing process list: {e}")

    def collect_telemetry(self) -> dict:
        """
        Collects all host system metrics, process logs, network connections,
        and protected folder file changes.
        """
        # 1. CPU and Memory Usage
        cpu_usage = psutil.cpu_percent()
        mem_info = psutil.virtual_memory()
        memory_usage = mem_info.percent
        
        # 2. Network Sockets
        connections = []
        outbound_count = 0
        try:
            connections = psutil.net_connections(kind='inet')
            for conn in connections:
                if conn.status == 'ESTABLISHED' and conn.raddr:
                    # Filter for actual outbound remote addresses
                    outbound_count += 1
        except Exception as e:
            # On some platforms/permissions, net_connections can fail
            logger.warning(f"Failed to fetch net connections: {e}")
            
        # 3. Running Processes & New Process Detection
        current_processes = []
        current_pids = set()
        new_processes = []
        try:
            for p in psutil.process_iter(attrs=['pid', 'name']):
                try:
                    pid = p.info['pid']
                    name = p.info['name']
                    current_pids.add(pid)
                    if pid not in self.known_pids and len(self.known_pids) > 0:
                        new_processes.append(f"{name} (PID: {pid})")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Keep a buffer of recently detected new processes
            if new_processes:
                self.new_processes_detected = (new_processes + self.new_processes_detected)[:15]
                # Update known list
                self.known_pids.update(current_pids)
        except Exception as e:
            logger.warning(f"Process monitoring encountered an error: {e}")
            
        # 4. Protected Folder File Modifications
        current_files = {}
        changes = []
        try:
            for file in self.protected_dir.rglob("*"):
                if file.is_file():
                    filepath = str(file)
                    mtime = file.stat().st_mtime
                    current_files[filepath] = mtime
                    
                    if filepath not in self.file_states:
                        changes.append(f"CREATED: {file.name}")
                    elif self.file_states[filepath] != mtime:
                        changes.append(f"MODIFIED: {file.name}")
            
            # Check for deleted files
            for filepath in list(self.file_states.keys()):
                if filepath not in current_files:
                    filename = Path(filepath).name
                    changes.append(f"DELETED: {filename}")
            
            if changes:
                self.file_changes_detected = (changes + self.file_changes_detected)[:15]
                self.file_states = current_files
        except Exception as e:
            logger.warning(f"File monitoring encountered an error: {e}")
            
        # 5. Device Health Score
        # Decreases based on heavy system load
        health_score = 100.0
        if cpu_usage > 85.0:
            health_score -= 20.0
        if memory_usage > 85.0:
            health_score -= 20.0
        if len(changes) > 5:
            health_score -= 15.0
        health_score = max(10.0, health_score)
        
        # 6. User Activity Mock (simulated active workstation state)
        user_active = True
        
        return {
            "host_cpu": cpu_usage,
            "host_memory": memory_usage,
            "total_processes": len(current_pids),
            "new_processes": self.new_processes_detected[:5],
            "total_connections": len(connections),
            "outbound_connections": outbound_count,
            "file_changes": self.file_changes_detected[:5],
            "failed_logins": self.failed_logins,
            "scada_commands_count": self.scada_commands_count,
            "device_health": health_score,
            "user_active": user_active
        }

# Global singleton monitor instance
host_monitor = HostBackgroundMonitor()
