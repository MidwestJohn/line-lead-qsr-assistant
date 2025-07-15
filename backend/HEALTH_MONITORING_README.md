# Enhanced Health Monitoring System

## Overview

The Enhanced Health Monitoring System provides comprehensive monitoring for PydanticAI + Ragie intelligence infrastructure. It extends the existing health monitoring with intelligence-specific metrics and real-time performance tracking.

## Features

### 🧠 Intelligence Service Health
- **Ragie API Health**: Connectivity, response times, search accuracy
- **PydanticAI Agent Coordination**: Agent selection accuracy, coordination success rates
- **Context Preservation**: Cross-modal context preservation tracking
- **Visual Citations**: Citation extraction performance monitoring

### 📊 Real-time Metrics
- **Response Times**: Track processing times across different services
- **Success Rates**: Monitor success rates for various operations
- **Quality Scores**: Track response quality and user satisfaction
- **Resource Usage**: Monitor memory, CPU, and system resources

### 🚨 Alert System
- **Threshold-based Alerts**: Configurable warning and critical thresholds
- **Intelligence-specific Alerts**: Custom alerts for AI service degradation
- **Automatic Resolution**: Alerts automatically resolve when metrics improve

### 📈 Performance Dashboard
- **Real-time Metrics**: Live performance data
- **Historical Trends**: 24-hour trend analysis
- **User Satisfaction**: Response quality and task success metrics
- **System Performance**: Resource utilization and health scores

## Architecture

### Core Components

1. **EnhancedHealthMonitoringSystem**: Main monitoring orchestrator
2. **IntelligenceMetric**: Intelligence-specific metric collection
3. **AgentPerformanceMetrics**: Agent coordination performance tracking
4. **RagieServiceHealth**: Ragie API health monitoring
5. **UniversalIntelligenceHealth**: Overall intelligence system health

### Monitoring Thread
- Runs continuously in background
- Collects metrics at configurable intervals
- Processes alerts and updates component health
- Minimal performance impact on main application

## API Endpoints

### Health Status
- `GET /health/intelligence` - Intelligence services health summary
- `GET /health/dashboard` - Complete performance dashboard
- `GET /health/monitoring-status` - Monitoring system status

### Service-specific Health
- `GET /health/ragie-service` - Ragie API health metrics
- `GET /health/agent-coordination` - Agent coordination health
- `GET /health/context-preservation` - Context preservation metrics

### Monitoring Control
- `POST /health/start-monitoring` - Start monitoring system
- `POST /health/stop-monitoring` - Stop monitoring system

### Performance Data
- `GET /health/real-time-metrics` - Current metric values
- `GET /health/historical-trends` - 24-hour trend data
- `GET /health/user-satisfaction` - User satisfaction metrics

### Interaction Tracking
- `POST /health/record-interaction` - Record interaction performance

## Configuration

### Health Thresholds
```python
intelligence_thresholds = {
    "ragie_response_time": {"warning": 3000, "critical": 8000},  # milliseconds
    "ragie_success_rate": {"warning": 0.95, "critical": 0.90},
    "agent_coordination": {"warning": 0.90, "critical": 0.80},
    "context_preservation": {"warning": 0.95, "critical": 0.85},
    "visual_citation_rate": {"warning": 0.70, "critical": 0.50},
    "cross_modal_sync": {"warning": 0.90, "critical": 0.80}
}
```

### Collection Intervals
```python
collection_intervals = {
    IntelligenceMetricType.RAGIE_API_HEALTH: 30,        # seconds
    IntelligenceMetricType.PYDANTIC_AGENT_COORDINATION: 60,
    IntelligenceMetricType.UNIVERSAL_INTELLIGENCE_HEALTH: 45,
    IntelligenceMetricType.CONTEXT_PRESERVATION: 90,
    IntelligenceMetricType.VOICE_TEXT_SYNC: 120,
    IntelligenceMetricType.CITATION_EXTRACTION_RATE: 60,
    IntelligenceMetricType.RESPONSE_QUALITY: 300
}
```

## Usage

### Starting Monitoring
```python
from health_monitoring_enhanced import enhanced_health_monitoring

# Start monitoring
enhanced_health_monitoring.start_monitoring()

# Get health summary
health_summary = enhanced_health_monitoring.get_intelligence_health_summary()

# Get performance dashboard
dashboard_data = enhanced_health_monitoring.get_performance_dashboard_data()
```

### Recording Interactions
```python
# Record interaction performance
session_id = "user_session_123"
interaction_data = {
    "response_time": 1200,
    "agent_type": "equipment",
    "query_type": "equipment_question",
    "response_quality": 0.92,
    "ragie_used": True,
    "context_preserved": True
}

enhanced_health_monitoring.record_interaction_performance(session_id, interaction_data)
```

### API Usage
```bash
# Check intelligence health
curl http://localhost:8000/health/intelligence

# Get performance dashboard
curl http://localhost:8000/health/dashboard

# Get real-time metrics
curl http://localhost:8000/health/real-time-metrics

# Start monitoring
curl -X POST http://localhost:8000/health/start-monitoring
```

## Testing

### Run Health Monitoring Tests
```bash
cd backend
python test_health_monitoring.py
```

### Run Dashboard Demo
```bash
cd backend
python health_dashboard_demo.py
```

## Metrics Collected

### Ragie Service Metrics
- **ragie_response_time**: API response time in milliseconds
- **ragie_search_accuracy**: Search result relevance score
- **ragie_visual_citations**: Visual citation availability
- **ragie_api_health**: Overall API health status

### Agent Coordination Metrics
- **agent_coordination_success**: Agent selection accuracy
- **agent_selection_accuracy**: Correct agent selection rate
- **cross_modal_performance**: Text/voice consistency

### Context Preservation Metrics
- **context_preservation_rate**: Context retention across interactions
- **voice_text_sync**: Voice and text response consistency
- **universal_intelligence_health**: Overall intelligence system health

### User Experience Metrics
- **response_quality**: Average response quality score
- **task_success_rate**: Task completion success rate
- **user_feedback_score**: User satisfaction rating

## Integration

The enhanced health monitoring integrates seamlessly with:

1. **Existing Health System**: Extends base health monitoring
2. **Main Application**: Automatic startup and monitoring
3. **Intelligence Services**: Direct integration with Ragie and PydanticAI
4. **Performance Dashboard**: Real-time metrics and trends

## Storage

### Metrics Storage
- **In-memory Buffers**: Fast access to recent metrics
- **JSON Files**: Persistent storage for configuration and historical data
- **Automatic Cleanup**: Old session data automatically removed

### Data Retention
- **Real-time Metrics**: Last 5,000 metrics
- **Historical Data**: 24 hours of trend data
- **Session Data**: 24 hours of interaction history
- **Alerts**: Last 500 alerts with resolution status

## Performance Impact

### Minimal Overhead
- **Background Processing**: Runs in separate thread
- **Efficient Collection**: Metrics collected at optimal intervals
- **Smart Sampling**: Intelligent metric sampling to reduce overhead
- **Resource Management**: Automatic cleanup and memory management

### Scalability
- **Thread Pool**: Concurrent metric collection
- **Configurable Intervals**: Adjustable collection frequency
- **Buffer Management**: Efficient memory usage with ring buffers
- **Async Operations**: Non-blocking metric collection

## Troubleshooting

### Common Issues

1. **Monitoring Not Starting**
   - Check if enhanced_health_monitoring is imported correctly
   - Verify thread permissions and system resources
   - Check logs for initialization errors

2. **No Metrics Collected**
   - Ensure services are properly initialized
   - Check collection intervals configuration
   - Verify metric collection permissions

3. **High Memory Usage**
   - Adjust buffer sizes in configuration
   - Enable automatic cleanup
   - Check for memory leaks in custom metrics

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger("health_monitoring_enhanced").setLevel(logging.DEBUG)

# Check monitoring status
status = enhanced_health_monitoring.get_monitoring_status()
print(json.dumps(status, indent=2))
```

## Future Enhancements

### Planned Features
- **Machine Learning**: Predictive health analysis
- **Custom Dashboards**: User-configurable dashboard views
- **Export Capabilities**: Export metrics to external systems
- **Mobile Alerts**: Push notifications for critical alerts
- **Advanced Analytics**: Deeper performance insights

### Integration Opportunities
- **Prometheus/Grafana**: Metrics export for visualization
- **Slack/Teams**: Alert notifications
- **External APIs**: Health data sharing
- **Mobile Apps**: Real-time monitoring on mobile devices

---

Generated with [Memex](https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>