# cloudpulse-api

**The application layer of CloudPulse — a FastAPI backend, React dashboard, and monitoring stack that reports on AWS infrastructure and pipeline health.**

The infrastructure this application runs on is provisioned separately in [cloudpulse-infra](https://github.com/sreenidhipalimar98/CloudPulse-Terraform). This repo owns the application code, its tests, its container image, its CI/CD pipeline, and its monitoring configuration.

## What's in this repo

| Component | Description |
|---|---|
| `app/` | FastAPI backend — REST API reporting on AWS resource health, ECS/pipeline status, and active alerts |
| `frontend/` | React dashboard that consumes the API and visualizes infrastructure + pipeline state |
| `monitoring/` | Prometheus scrape config and Grafana dashboard definitions |
| `tests/` | Backend test suite |
| `.github/workflows/` | CI/CD: test → build → push to ECR → deploy to ECS |

## Repository structure

```
cloudpulse-api/
├── app/
│   ├── main.py                       # FastAPI app entrypoint
│   ├── core/
│   │   └── config.py                 # Settings, loaded from env / Secrets Manager
│   ├── routers/
│   │   ├── health.py                 # GET /health — ALB health check target
│   │   ├── infrastructure.py         # GET /infrastructure/* — live AWS resource state
│   │   ├── pipelines.py              # GET /pipelines/* — CI/CD run status
│   │   └── alerts.py                 # GET /alerts/* — active alert feed
│   ├── services/
│   │   ├── aws_client.py             # boto3 wrappers (EC2, ECS, RDS, CloudWatch)
│   │   └── metrics_collector.py      # Aggregates metrics for Prometheus scraping
│   └── models/
│       └── schemas.py                # Pydantic response models
├── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── index.jsx
│   └── public/
├── monitoring/
│   ├── prometheus/prometheus.yml
│   ├── grafana/dashboards/
│   └── docker-compose.monitoring.yml
├── docs/
│   └── DEPLOYMENT.md
├── .github/workflows/
│   └── ci-cd.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, boto3 |
| Frontend | React, hosted on AWS Amplify |
| Monitoring | Prometheus, Grafana |
| CI/CD | GitHub Actions, OIDC federation to AWS (no stored keys) |
| Container | Docker, pushed to ECR repo from `cloudpulse-infra` |

## Getting started

### Prerequisites
- Infrastructure in [cloudpulse-infra](https://github.com/sreenidhipalimar98/CloudPulse-Terraform) should be provisioned first
- Python 3.11+, Node.js 18+, Docker

### Run the API locally
```bash
cp .env.example .env   # fill in DB connection details from cloudpulse-infra outputs
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Run the frontend locally
```bash
cd frontend
npm install
npm start
```

### Run the monitoring stack locally
```bash
cd monitoring
docker-compose -f docker-compose.monitoring.yml up
```

## CI/CD pipeline

On every push to `main`:

1. **Test** — run the Python test suite
2. **Build** — build the Docker image
3. **Push** — push to ECR (URL from `cloudpulse-infra` output)
4. **Deploy** — assume `AWS_DEPLOY_ROLE_ARN` via OIDC, update ECS service

Required GitHub repo secrets (values from `terraform output` in `cloudpulse-infra`):

| Secret | Source |
|--------|--------|
| `AWS_DEPLOY_ROLE_ARN` | `github_actions_deploy_role_arn` output |
| `ECR_REPOSITORY_URL` | `ecr_repository_url` output |
| `ECS_CLUSTER_NAME` | `ecs_cluster_name` output |
| `ECS_SERVICE_NAME` | `ecs_service_name` output |

## Roadmap

- [x] Repository structure and CI/CD pipeline design
- [ ] FastAPI backend with live AWS resource endpoints
- [ ] React dashboard
- [ ] Prometheus + Grafana monitoring stack wired to live metrics
- [ ] Alerting integration

## Related

- [CloudPulse-Terraform](https://github.com/sreenidhipalimar98/CloudPulse-Terraform) — infrastructure repo

## Author

**Sreenidhi Palimar** — DevOps Engineer, AWS Certified Solutions Architect – Associate

## License

MIT
