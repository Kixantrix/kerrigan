# Cost Plan: Hello API

## Overview

The Hello API is a simple, stateless REST API service with minimal operational costs. This document outlines expected costs, resource usage, and cost guardrails.

## Cost Drivers

### Compute Resources

**Container Resources**:
- CPU: Minimal (<0.1 vCPU under normal load)
- Memory: ~50-100 MB (Python + Flask + dependencies)
- Disk: ~200 MB (Docker image size)

**Estimated Monthly Costs** (varies by provider):

| Provider | Instance Type | vCPU | RAM | Est. Monthly Cost |
|----------|---------------|------|-----|-------------------|
| AWS ECS Fargate | 0.25 vCPU, 0.5 GB | 0.25 | 512 MB | ~$3-5/month |
| Google Cloud Run | 1 vCPU, 512 MB | 1 | 512 MB | ~$2-4/month (pay per request) |
| Azure Container Instances | 0.5 vCPU, 0.5 GB | 0.5 | 512 MB | ~$5-7/month |
| DigitalOcean App Platform | 512 MB Basic | 1 | 512 MB | ~$5/month |
| Self-hosted (VM) | Shared with other services | - | - | $0 (absorbed by existing infra) |

**Note**: Above estimates assume low to moderate traffic (<10,000 requests/day). Actual costs depend on:
- Request volume
- Response time requirements
- Concurrent connections
- Provider's pricing model

### Network/Bandwidth

- **Ingress**: Free on most platforms
- **Egress**: Minimal cost (responses are tiny JSON payloads)
- **Estimated**: <1 GB/month for typical usage = ~$0.01-0.10/month

### Storage

- **Container Image Storage**: Usually free tier sufficient
- **Logs**: If using managed logging, ~$0.50-1/month for retention

### No External Dependencies

This service has NO costs for:
- Databases (stateless design)
- Message queues
- Object storage
- External APIs
- Third-party services

## Total Estimated Monthly Cost

**Low traffic scenario** (<1,000 requests/day):
- **$0-5/month** (many free tiers cover this)

**Moderate traffic scenario** (10,000-50,000 requests/day):
- **$5-15/month** (depending on provider and region)

**High traffic scenario** (>100,000 requests/day):
- **$15-50/month** (may need multiple instances or larger instance)

## Guardrails

### Budget Alerts

Set up budget alerts at:
- **$5/month**: Informational alert (expected usage)
- **$20/month**: Warning alert (investigate usage spike)
- **$50/month**: Critical alert (potential runaway costs)

### Resource Limits

**CPU**: Cap at 0.5 vCPU per container to prevent runaway usage

**Memory**: Cap at 512 MB (sufficient for this workload)

**Concurrent Instances**: 
- Development: 1 instance max
- Production: Auto-scale between 1-3 instances

**Request Limits**: Consider rate limiting at application or infrastructure level:
- Per IP: 100 requests/minute (prevents abuse)
- Global: 10,000 requests/hour (protects against DDoS)

### Cost Optimization Strategies

1. **Use Free Tiers**:
   - Google Cloud Run: 2 million requests/month free
   - AWS Lambda: 1 million requests/month free (if adapted to Lambda)
   - Fly.io: Free tier for small apps
   
2. **Efficient Container**:
   - Use `python:3.11-slim` base image (not `python:3.11-alpine` or full image)
   - Multi-stage builds to reduce image size
   - Minimize dependencies in requirements.txt

3. **Auto-scaling**:
   - Scale to zero when not in use (if platform supports)
   - Scale up only during traffic spikes
   
4. **Region Selection**:
   - Deploy in lowest-cost region that meets latency requirements
   - us-central1 (GCP), us-east-1 (AWS) typically cheapest

## Scale Assumptions

Current design assumptions:
- **Traffic**: < 100,000 requests/day
- **Concurrency**: < 50 concurrent requests
- **Response Time**: < 100ms per request
- **Availability**: 99% uptime (not HA)

If traffic exceeds these assumptions:
- Scale horizontally (add more container instances)
- Add load balancer (typically $10-20/month)
- Consider CDN for static content (if any added later)
- Monitor and adjust based on actual usage patterns

## Cost Tracking

### Tagging Strategy

Tag all resources with:
```
project: hello-api
environment: production|development
cost-center: examples
managed-by: kerrigan
```

### Regular Reviews

- **Weekly**: Check dashboard for anomalies
- **Monthly**: Review actual costs vs. estimates
- **Quarterly**: Re-evaluate instance sizing and provider

## Cost by Environment

### Development
- **Recommendation**: Use free tier or shared development infrastructure
- **Expected cost**: $0-2/month
- **OK to shut down**: After testing sessions

### Staging
- **Recommendation**: Minimal instance, auto-sleep when idle
- **Expected cost**: $2-5/month
- **OK to shut down**: Nights and weekends

### Production
- **Recommendation**: Right-sized with auto-scaling
- **Expected cost**: $5-15/month
- **Uptime**: Should run continuously

## Failure Mode Costs

### Runaway Scenarios

**Traffic spike** (DDoS or viral traffic):
- **Risk**: Auto-scaling could multiply instances
- **Mitigation**: Set max instance count, enable rate limiting
- **Max cost**: $50/month (with 3-instance cap)

**Memory leak**:
- **Risk**: Container OOM, restart loop
- **Mitigation**: Memory limit, health checks, restart limits
- **Max cost**: No additional cost (container just restarts)

**Logging explosion**:
- **Risk**: Excessive logs increase storage costs
- **Mitigation**: Log retention policy (7-30 days), log level controls
- **Max cost**: $5/month additional (with aggressive logging)

## Cost Reporting

Generate monthly cost report showing:
1. Actual spend by resource type
2. Comparison to budget
3. Trend analysis (compared to previous months)
4. Recommendations for optimization

## Decommissioning

If the service is no longer needed:
1. Stop all running instances
2. Delete container images
3. Remove DNS records (if any)
4. Archive logs (if needed for compliance)
5. **Cost after decommission**: $0

## Summary

The Hello API is intentionally designed to be **extremely low-cost**:
- No external dependencies = no recurring service costs
- Stateless design = minimal resource requirements
- Simple architecture = easy to optimize

**Expected steady-state cost**: **$0-10/month**

This makes it suitable as a learning example without financial concerns.
