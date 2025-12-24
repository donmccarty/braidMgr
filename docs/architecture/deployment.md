# Deployment Architecture

*Parent: [ARCHITECTURE.md](../ARCHITECTURE.md)*

AWS infrastructure and deployment pipeline.

**Key Concepts**:
- ECS Fargate for containerized backend
- CloudFront for static frontend and API gateway
- Aurora PostgreSQL for database
- Infrastructure as Code (Terraform/CDK)

---

## Environments

| Environment | Purpose | URL |
|-------------|---------|-----|
| Development | Local dev | localhost:3000, localhost:8000 |
| Staging | Pre-production testing | staging.braidmgr.com |
| Production | Live system | app.braidmgr.com |

---

## AWS Infrastructure Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                           VPC                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Public Subnet                            │ │
│  │  ┌──────────────┐  ┌──────────────┐                        │ │
│  │  │    ALB       │  │  CloudFront  │                        │ │
│  │  └──────────────┘  └──────────────┘                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Private Subnet                            │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │ │
│  │  │ ECS Fargate  │  │ ECS Fargate  │  │ ECS Fargate  │     │ │
│  │  │  (API x2)    │  │  (API x2)    │  │  (API x2)    │     │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  Database Subnet                            │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │              Aurora PostgreSQL Cluster                │  │ │
│  │  │  ┌─────────────┐        ┌─────────────┐              │  │ │
│  │  │  │   Writer    │        │   Reader    │              │  │ │
│  │  │  └─────────────┘        └─────────────┘              │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

External:
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│     S3       │  │   Secrets    │  │  CloudWatch  │
│ (Attachments)│  │   Manager    │  │   (Logs)     │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## Service Configuration

### ECS Fargate (API)

| Setting | Value |
|---------|-------|
| CPU | 512 (0.5 vCPU) |
| Memory | 1024 MB |
| Min tasks | 2 |
| Max tasks | 10 |
| Health check | /health |
| Deployment | Rolling update |

### Aurora PostgreSQL

| Setting | Value |
|---------|-------|
| Engine | PostgreSQL 15 |
| Instance | db.r6g.large |
| Writer | 1 |
| Readers | 1-3 (auto-scaling) |
| Storage | Auto-scaling |
| Backup | 7 days retention |

### S3 (Attachments)

| Setting | Value |
|---------|-------|
| Bucket | braidmgr-{env}-attachments |
| Versioning | Enabled |
| Encryption | SSE-S3 |
| Lifecycle | Intelligent-Tiering |

---

## Scaling Strategy

### API Auto-Scaling

```yaml
# ECS Service Auto-Scaling
Target Tracking:
  - Metric: CPUUtilization
    Target: 70%
    ScaleOutCooldown: 60s
    ScaleInCooldown: 300s

  - Metric: MemoryUtilization
    Target: 80%
```

### Database Auto-Scaling

```yaml
# Aurora Read Replica Scaling
Target Tracking:
  - Metric: RDSReaderAverageCPUUtilization
    Target: 70%
    MinCapacity: 1
    MaxCapacity: 3
```

---

## CI/CD Pipeline

```yaml
# GitHub Actions workflow
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run backend tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest
      - name: Run frontend tests
        run: |
          cd frontend
          npm ci
          npm test

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build backend image
        run: docker build -f Dockerfile.backend -t backend .
      - name: Build frontend
        run: |
          cd frontend
          npm ci
          npm run build
      - name: Push to ECR
        run: |
          aws ecr get-login-password | docker login ...
          docker push $ECR_REPO:$GITHUB_SHA

  deploy-staging:
    needs: build
    environment: staging
    steps:
      - name: Deploy to ECS
        run: aws ecs update-service ...
      - name: Run migrations
        run: ./scripts/run-migrations.sh staging
      - name: Smoke tests
        run: ./scripts/smoke-tests.sh staging

  deploy-production:
    needs: deploy-staging
    environment: production
    steps:
      - name: Deploy to ECS
        run: aws ecs update-service ...
      - name: Run migrations
        run: ./scripts/run-migrations.sh production
```

---

## Monitoring

### CloudWatch Metrics

| Metric | Alarm Threshold |
|--------|-----------------|
| API Response Time (p99) | > 2s |
| API Error Rate | > 1% |
| ECS CPU | > 85% |
| Aurora CPU | > 80% |
| Aurora Connections | > 80% |

### Logging

```python
# Structured logging with structlog
logger.info(
    "item_created",
    project_id=str(project_id),
    item_num=item.item_num,
    item_type=item.type,
    correlation_id=correlation_id
)
```

All logs shipped to CloudWatch Logs with 30-day retention.

---

## Disaster Recovery

| Component | RPO | RTO | Strategy |
|-----------|-----|-----|----------|
| Database | 5 min | 30 min | Aurora PITR, cross-region replica |
| Attachments | 0 | 1 hour | S3 cross-region replication |
| Application | 0 | 15 min | Multi-AZ ECS, blue-green deploy |

### Backup Schedule

| Resource | Frequency | Retention |
|----------|-----------|-----------|
| Aurora snapshots | Daily | 7 days |
| Aurora PITR | Continuous | 7 days |
| S3 versioning | Continuous | 90 days |

---

## Security

### Network

- VPC with public/private subnet isolation
- Security groups with minimal ports
- NAT Gateway for private subnet egress
- VPC Flow Logs enabled

### Secrets

- All secrets in AWS Secrets Manager
- IAM roles for ECS task access
- No secrets in environment variables or code

### Encryption

- Data at rest: Aurora encryption, S3 SSE
- Data in transit: TLS 1.3 everywhere
- JWT signing: RS256 with rotated keys
