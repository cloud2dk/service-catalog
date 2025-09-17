# Cloud2 Service Catalog

This repository contains multiple AWS Service Catalog portfolios and products for Cloud2 infrastructure management.

## Repository Structure

```
service-catalog/
├── .github/workflows/           # GitHub Actions workflows
├── scripts/                     # Shared build, validation, and deployment scripts
├── services/                    # Service-specific configurations and templates
│   ├── monitoring-baseline/     # Monitoring and alerting infrastructure
│   ├── access-roles/           # IAM roles and access management
│   └── reporting/              # Cost reporting and analytics infrastructure
└── README.md
```

## Services

### Monitoring Baseline
- **Purpose**: AWS monitoring infrastructure including CloudWatch, OAM, and cost anomaly detection
- **Location**: `services/monitoring-baseline/`
- **Products**: Event management, OAM sinks, service management, cost anomalies

### Access Roles
- **Purpose**: IAM role management for secure access control
- **Location**: `services/access-roles/`
- **Products**: Spotter access roles, Cloud2 operations roles, customer access roles

### Reporting
- **Purpose**: Cost and usage reporting infrastructure
- **Location**: `services/reporting/`
- **Products**: S3 buckets, CUR/FOCUS Glue databases, Athena workgroups, usage exports

## Shared Scripts

All services use the same set of deployment scripts located in `scripts/`:

- `validate.sh` - Validates manifest.yaml and CloudFormation templates
- `build.sh` - Builds and packages service artifacts
- `publish.sh` - Publishes portfolios and products to AWS Service Catalog
- `testing.sh` - Runs service tests

## Deployment

### Automatic Deployment

Each service has its own GitHub Actions workflow with path-based triggers:

- **`services/monitoring-baseline/`** changes → triggers `monitoring-baseline` workflow
- **`services/access-roles/`** changes → triggers `access-roles` workflow
- **`services/reporting/`** changes → triggers `reporting` workflow
- **`scripts/`** changes → triggers **all 3 workflows** (shared scripts)

### Manual Deployment

Each service can be deployed independently:

1. Go to GitHub Actions tab
2. Select the specific service workflow:
   - `monitoring-baseline`
   - `access-roles`
   - `reporting-baseline`
3. Click "Run workflow" to manually trigger deployment

### Pipeline Stages

Each service goes through:
1. **Build**: Validation and artifact creation
2. **Dev Deploy**: Deployment to development environment
3. **Prod Deploy**: Deployment to production environment (after dev success)

## Development

### Adding a New Service

1. Create new directory in `services/`
2. Add `manifest.yaml`, `customer/`, and `operations/` directories
3. Create `artifacts/` directory (will be populated during build)
4. Update this README
5. The GitHub Actions workflow will automatically detect and deploy the new service

### Modifying Scripts

Changes to `scripts/` will trigger deployment of all services since they share the same build process.

### Environment Variables

- `HOME_REGION`: Primary AWS region (eu-central-1)
- `ACTIVE_REGIONS`: Comma-separated list of deployment regions
- `SERVICE_ACCOUNT_ID`: AWS account ID for deployments
- `VERSION`: Auto-generated version number

## AWS Regions

- **Home Region**: eu-central-1 (primary)
- **Active Regions**: eu-central-1, eu-west-1, us-east-1