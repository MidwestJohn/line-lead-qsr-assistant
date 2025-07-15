# Health Monitoring Quick Reference

## 🚀 **Getting Started**

### Check System Health
```bash
curl http://localhost:8000/health
```

### View Intelligence Health Dashboard
```bash
curl http://localhost:8000/health/dashboard | jq
```

### Check Real-time Metrics
```bash
curl http://localhost:8000/health/real-time-metrics | jq
```

## 📊 **Key Endpoints**

| Endpoint | Description | Method |
|----------|-------------|---------|
| `/health` | Overall system health | GET |
| `/health/intelligence` | Intelligence services health | GET |
| `/health/dashboard` | Complete performance dashboard | GET |
| `/health/ragie-service` | Ragie API health | GET |
| `/health/agent-coordination` | PydanticAI agent health | GET |
| `/health/real-time-metrics` | Current metrics | GET |
| `/health/historical-trends` | 24h trends | GET |
| `/health/start-monitoring` | Start monitoring | POST |
| `/health/stop-monitoring` | Stop monitoring | POST |

## 🧠 **Intelligence Metrics**

### Ragie Service
- **ragie_response_time** - API response time (ms)
- **ragie_search_accuracy** - Search relevance score
- **ragie_visual_citations** - Citation availability

### PydanticAI Agents
- **agent_coordination_success** - Agent coordination rate
- **agent_selection_accuracy** - Correct agent selection
- **cross_modal_performance** - Text/voice consistency

### Context & Quality
- **context_preservation_rate** - Context retention
- **response_quality** - Response quality score
- **voice_text_sync** - Voice-text synchronization

## 🚨 **Alert Thresholds**

| Metric | Warning | Critical |
|--------|---------|----------|
| Ragie Response Time | 3000ms | 8000ms |
| Agent Coordination | 90% | 80% |
| Context Preservation | 95% | 85% |
| Visual Citation Rate | 70% | 50% |

## 📈 **Dashboard Sections**

1. **intelligence_health** - Overall intelligence status
2. **real_time_metrics** - Current performance data
3. **historical_trends** - 24-hour trend analysis
4. **user_satisfaction** - User experience metrics
5. **system_performance** - Resource utilization
6. **base_system_health** - Core system health
7. **dashboard_timestamp** - Last update time

## 🔧 **Python Usage**

```python
from health_monitoring_enhanced import enhanced_health_monitoring

# Start monitoring
enhanced_health_monitoring.start_monitoring()

# Get health summary
health = enhanced_health_monitoring.get_intelligence_health_summary()
print(f"Health: {health['overall_intelligence_health']}")

# Get dashboard data
dashboard = enhanced_health_monitoring.get_performance_dashboard_data()

# Record interaction
enhanced_health_monitoring.record_interaction_performance(
    session_id="user_123",
    interaction_data={
        "response_time": 1200,
        "agent_type": "equipment",
        "response_quality": 0.92,
        "ragie_used": True
    }
)
```

## 🎯 **Health Status Levels**

- **healthy** - All systems operational
- **warning** - Some metrics below optimal
- **critical** - Critical thresholds breached
- **degraded** - Performance impacted
- **unknown** - Unable to determine status

## 🏥 **Troubleshooting**

### No Metrics Collected
```bash
# Check monitoring status
curl http://localhost:8000/health/monitoring-status

# Restart monitoring
curl -X POST http://localhost:8000/health/start-monitoring
```

### High Response Times
```bash
# Check Ragie service health
curl http://localhost:8000/health/ragie-service

# Check system performance
curl http://localhost:8000/health/dashboard | jq '.system_performance'
```

### Context Issues
```bash
# Check context preservation
curl http://localhost:8000/health/context-preservation

# Check agent coordination
curl http://localhost:8000/health/agent-coordination
```

## 📱 **Production Monitoring**

### Health Check Script
```bash
#!/bin/bash
# health_check.sh
HEALTH=$(curl -s http://localhost:8000/health | jq -r '.status')
if [ "$HEALTH" != "healthy" ]; then
    echo "🚨 System health: $HEALTH"
    # Send alert
fi
```

### Continuous Monitoring
```bash
# Monitor every 30 seconds
watch -n 30 "curl -s http://localhost:8000/health/real-time-metrics | jq '.ragie_response_time'"
```

---

Generated with [Memex](https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>