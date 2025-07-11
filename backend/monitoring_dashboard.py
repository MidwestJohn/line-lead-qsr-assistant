#!/usr/bin/env python3
"""
Real-Time Monitoring Dashboard
Live monitoring of pipeline progress during E2E testing
"""

import asyncio
import time
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import curses
import threading

class MonitoringDashboard:
    """Real-time monitoring dashboard for pipeline testing."""
    
    def __init__(self):
        self.monitoring_active = False
        self.stats_history = []
        self.current_stats = {}
        self.log_file = "pipeline_diagnostic.log"
        self.logger = logging.getLogger('Dashboard')
        
    def start_monitoring(self):
        """Start the monitoring dashboard."""
        self.monitoring_active = True
        
        # Run dashboard in separate thread
        dashboard_thread = threading.Thread(target=self._run_dashboard)
        dashboard_thread.daemon = True
        dashboard_thread.start()
        
        # Start data collection
        collection_thread = threading.Thread(target=self._collect_data)
        collection_thread.daemon = True
        collection_thread.start()
        
        return dashboard_thread
        
    def _collect_data(self):
        """Collect monitoring data."""
        while self.monitoring_active:
            try:
                # Collect Neo4j statistics
                neo4j_stats = self._get_neo4j_stats()
                
                # Collect log file statistics
                log_stats = self._get_log_stats()
                
                # Collect pipeline metrics
                pipeline_stats = self._get_pipeline_stats()
                
                # Combine all stats
                timestamp = datetime.now()
                current_stats = {
                    'timestamp': timestamp.isoformat(),
                    'neo4j': neo4j_stats,
                    'logs': log_stats,
                    'pipeline': pipeline_stats
                }
                
                # Update current stats
                self.current_stats = current_stats
                
                # Add to history
                self.stats_history.append(current_stats)
                
                # Keep only last 100 entries
                if len(self.stats_history) > 100:
                    self.stats_history = self.stats_history[-100:]
                
                time.sleep(2)  # Collect every 2 seconds
                
            except Exception as e:
                self.logger.error(f"Data collection error: {e}")
                time.sleep(5)
                
    def _get_neo4j_stats(self) -> Dict[str, Any]:
        """Get Neo4j statistics."""
        try:
            from services.neo4j_service import neo4j_service
            
            # Get node and relationship counts
            stats_query = """
                MATCH (n) 
                OPTIONAL MATCH ()-[r]->() 
                RETURN count(DISTINCT n) as nodes, count(r) as relationships
            """
            
            result = neo4j_service.execute_query(stats_query)
            
            if result.get('success') and result.get('records'):
                record = result['records'][0]
                
                # Get node type distribution
                types_query = """
                    MATCH (n) 
                    RETURN labels(n) as labels, count(n) as count 
                    ORDER BY count DESC
                """
                
                types_result = neo4j_service.execute_query(types_query)
                node_types = {}
                
                if types_result.get('success'):
                    for type_record in types_result.get('records', []):
                        labels = type_record.get('labels', [])
                        if labels:
                            node_types[labels[0]] = type_record.get('count', 0)
                
                return {
                    'total_nodes': record.get('nodes', 0),
                    'total_relationships': record.get('relationships', 0),
                    'node_types': node_types,
                    'connected': True
                }
                
        except Exception as e:
            self.logger.debug(f"Neo4j stats error: {e}")
            
        return {
            'total_nodes': 0,
            'total_relationships': 0,
            'node_types': {},
            'connected': False
        }
        
    def _get_log_stats(self) -> Dict[str, Any]:
        """Get log file statistics."""
        try:
            if os.path.exists(self.log_file):
                file_size = os.path.getsize(self.log_file)
                mod_time = os.path.getmtime(self.log_file)
                
                # Count log lines by type
                with open(self.log_file, 'r') as f:
                    lines = f.readlines()
                    
                error_count = len([line for line in lines if 'ERROR' in line])
                warning_count = len([line for line in lines if 'WARNING' in line])
                info_count = len([line for line in lines if 'INFO' in line])
                
                return {
                    'file_size': file_size,
                    'last_modified': mod_time,
                    'total_lines': len(lines),
                    'error_count': error_count,
                    'warning_count': warning_count,
                    'info_count': info_count
                }
                
        except Exception as e:
            self.logger.debug(f"Log stats error: {e}")
            
        return {
            'file_size': 0,
            'last_modified': 0,
            'total_lines': 0,
            'error_count': 0,
            'warning_count': 0,
            'info_count': 0
        }
        
    def _get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        try:
            # Look for recent pipeline metrics files
            metrics_files = [f for f in os.listdir('.') if f.startswith('pipeline_metrics_')]
            
            if metrics_files:
                # Get the most recent metrics file
                latest_file = max(metrics_files, key=lambda f: os.path.getmtime(f))
                
                with open(latest_file, 'r') as f:
                    metrics = json.load(f)
                    
                return {
                    'has_metrics': True,
                    'file_name': metrics.get('file_name', ''),
                    'total_duration': metrics.get('total_duration_seconds', 0),
                    'stage_count': len(metrics.get('stages', {})),
                    'success': metrics.get('success', False)
                }
                
        except Exception as e:
            self.logger.debug(f"Pipeline stats error: {e}")
            
        return {
            'has_metrics': False,
            'file_name': '',
            'total_duration': 0,
            'stage_count': 0,
            'success': False
        }
        
    def _run_dashboard(self):
        """Run the curses-based dashboard."""
        try:
            curses.wrapper(self._dashboard_loop)
        except Exception as e:
            self.logger.error(f"Dashboard error: {e}")
            
    def _dashboard_loop(self, stdscr):
        """Main dashboard loop."""
        # Setup curses
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(1)   # Non-blocking input
        
        while self.monitoring_active:
            try:
                # Clear screen
                stdscr.clear()
                
                # Draw dashboard
                self._draw_dashboard(stdscr)
                
                # Refresh screen
                stdscr.refresh()
                
                # Check for quit key
                key = stdscr.getch()
                if key == ord('q'):
                    self.monitoring_active = False
                    break
                    
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Dashboard loop error: {e}")
                break
                
    def _draw_dashboard(self, stdscr):
        """Draw the dashboard content."""
        try:
            height, width = stdscr.getmaxyx()
            
            # Header
            title = "MEMEX PIPELINE MONITORING DASHBOARD"
            stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
            stdscr.addstr(1, 0, "=" * width)
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            stdscr.addstr(2, 0, f"Current Time: {current_time}")
            stdscr.addstr(3, 0, "Press 'q' to quit")
            
            # Neo4j Section
            y = 5
            stdscr.addstr(y, 0, "NEO4J DATABASE:", curses.A_BOLD)
            y += 1
            
            neo4j_stats = self.current_stats.get('neo4j', {})
            connection_status = "✅ Connected" if neo4j_stats.get('connected') else "❌ Disconnected"
            stdscr.addstr(y, 0, f"  Status: {connection_status}")
            y += 1
            
            nodes = neo4j_stats.get('total_nodes', 0)
            relationships = neo4j_stats.get('total_relationships', 0)
            stdscr.addstr(y, 0, f"  Nodes: {nodes:,}")
            stdscr.addstr(y, 20, f"  Relationships: {relationships:,}")
            y += 1
            
            # Node types
            node_types = neo4j_stats.get('node_types', {})
            if node_types:
                stdscr.addstr(y, 0, "  Node Types:")
                y += 1
                for node_type, count in list(node_types.items())[:5]:  # Show top 5
                    stdscr.addstr(y, 4, f"{node_type}: {count}")
                    y += 1
            
            # Logs Section
            y += 1
            stdscr.addstr(y, 0, "LOG FILES:", curses.A_BOLD)
            y += 1
            
            log_stats = self.current_stats.get('logs', {})
            file_size = log_stats.get('file_size', 0)
            total_lines = log_stats.get('total_lines', 0)
            error_count = log_stats.get('error_count', 0)
            warning_count = log_stats.get('warning_count', 0)
            
            stdscr.addstr(y, 0, f"  File Size: {file_size:,} bytes")
            stdscr.addstr(y, 30, f"  Total Lines: {total_lines:,}")
            y += 1
            
            stdscr.addstr(y, 0, f"  Errors: {error_count}")
            stdscr.addstr(y, 15, f"  Warnings: {warning_count}")
            y += 1
            
            # Pipeline Section
            y += 1
            stdscr.addstr(y, 0, "PIPELINE STATUS:", curses.A_BOLD)
            y += 1
            
            pipeline_stats = self.current_stats.get('pipeline', {})
            has_metrics = pipeline_stats.get('has_metrics', False)
            
            if has_metrics:
                file_name = pipeline_stats.get('file_name', '')
                duration = pipeline_stats.get('total_duration', 0)
                stage_count = pipeline_stats.get('stage_count', 0)
                success = pipeline_stats.get('success', False)
                
                stdscr.addstr(y, 0, f"  Current File: {file_name}")
                y += 1
                stdscr.addstr(y, 0, f"  Duration: {duration:.2f}s")
                stdscr.addstr(y, 20, f"  Stages: {stage_count}")
                y += 1
                
                status_text = "✅ Success" if success else "❌ Failed"
                stdscr.addstr(y, 0, f"  Status: {status_text}")
                y += 1
            else:
                stdscr.addstr(y, 0, "  No active pipeline")
                y += 1
            
            # Statistics History
            y += 1
            stdscr.addstr(y, 0, "STATISTICS HISTORY:", curses.A_BOLD)
            y += 1
            
            if len(self.stats_history) >= 2:
                # Show trend
                prev_stats = self.stats_history[-2]
                curr_stats = self.stats_history[-1]
                
                prev_nodes = prev_stats.get('neo4j', {}).get('total_nodes', 0)
                curr_nodes = curr_stats.get('neo4j', {}).get('total_nodes', 0)
                node_change = curr_nodes - prev_nodes
                
                prev_rels = prev_stats.get('neo4j', {}).get('total_relationships', 0)
                curr_rels = curr_stats.get('neo4j', {}).get('total_relationships', 0)
                rel_change = curr_rels - prev_rels
                
                if node_change > 0:
                    stdscr.addstr(y, 0, f"  Nodes added: +{node_change}")
                    y += 1
                
                if rel_change > 0:
                    stdscr.addstr(y, 0, f"  Relationships added: +{rel_change}")
                    y += 1
                
                if node_change == 0 and rel_change == 0:
                    stdscr.addstr(y, 0, "  No changes detected")
                    y += 1
            
            # Footer
            footer_y = height - 2
            stdscr.addstr(footer_y, 0, "=" * width)
            stdscr.addstr(footer_y + 1, 0, "Monitoring Status: ACTIVE")
            
        except Exception as e:
            # If dashboard fails, show error
            try:
                stdscr.addstr(0, 0, f"Dashboard Error: {e}")
                stdscr.addstr(1, 0, "Press 'q' to quit")
            except:
                pass
                
    def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring_active = False
        
    def run_console_dashboard(self):
        """Run a simple console-based dashboard."""
        print("\n" + "=" * 60)
        print("MEMEX PIPELINE MONITORING DASHBOARD")
        print("=" * 60)
        print("Press Ctrl+C to stop monitoring")
        print("Updating every 5 seconds...")
        
        try:
            while True:
                # Clear screen (works on most terminals)
                os.system('clear' if os.name == 'posix' else 'cls')
                
                # Display current time
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"Current Time: {current_time}")
                print("-" * 60)
                
                # Display Neo4j stats
                neo4j_stats = self._get_neo4j_stats()
                print(f"NEO4J:")
                print(f"  Status: {'✅ Connected' if neo4j_stats['connected'] else '❌ Disconnected'}")
                print(f"  Nodes: {neo4j_stats['total_nodes']:,}")
                print(f"  Relationships: {neo4j_stats['total_relationships']:,}")
                
                if neo4j_stats['node_types']:
                    print(f"  Node Types:")
                    for node_type, count in neo4j_stats['node_types'].items():
                        print(f"    {node_type}: {count}")
                
                # Display log stats
                log_stats = self._get_log_stats()
                print(f"\nLOGS:")
                print(f"  File Size: {log_stats['file_size']:,} bytes")
                print(f"  Total Lines: {log_stats['total_lines']:,}")
                print(f"  Errors: {log_stats['error_count']}")
                print(f"  Warnings: {log_stats['warning_count']}")
                
                # Display pipeline stats
                pipeline_stats = self._get_pipeline_stats()
                print(f"\nPIPELINE:")
                if pipeline_stats['has_metrics']:
                    print(f"  File: {pipeline_stats['file_name']}")
                    print(f"  Duration: {pipeline_stats['total_duration']:.2f}s")
                    print(f"  Stages: {pipeline_stats['stage_count']}")
                    print(f"  Status: {'✅ Success' if pipeline_stats['success'] else '❌ Failed'}")
                else:
                    print("  No active pipeline")
                
                print("-" * 60)
                print("Press Ctrl+C to stop monitoring")
                
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")

if __name__ == "__main__":
    dashboard = MonitoringDashboard()
    dashboard.run_console_dashboard()