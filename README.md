# Cloud2 Service Catalog

This repository contains multiple AWS Service Catalog portfolios and products for Cloud2 infrastructure management. This is a **service catalog management system** - it handles the publishing and release of services into AWS Service Catalog for later provisioning, but is NOT a provisioning system itself.

## Repository Structure

```
service-catalog/
├── .github/
│   ├── actions/                 # Reusable GitHub Actions
│   └── workflows/               # Service-specific deployment workflows
├── scripts/                     # Shared build, validation, and deployment scripts
├── services/                    # Service-specific configurations and templates
│   ├── monitoring-baseline/     # Monitoring and alerting infrastructure
│   │   ├── customer/           # Customer account templates and Lambda functions
│   │   ├── operations/         # Operations account templates and Lambda functions
│   │   ├── artifacts/          # Build artifacts (auto-generated)
│   │   └── manifest.yaml       # Service configuration
│   ├── access-roles/           # IAM roles and access management
│   │   ├── customer/           # Customer account IAM templates
│   │   ├── operations/         # Operations account IAM templates
│   │   ├── artifacts/          # Build artifacts (auto-generated)
│   │   └── manifest.yaml       # Service configuration
│   └── reporting/              # Cost reporting and analytics infrastructure
│       ├── customer/           # Customer account reporting templates
│       ├── operations/         # Operations account reporting templates
│       ├── artifacts/          # Build artifacts (auto-generated)
│       └── manifest.yaml       # Service configuration
└── README.md
```

## Service Architecture

Each service follows a standardized structure:

- **`customer/`**: CloudFormation templates and Lambda functions for customer AWS accounts
- **`operations/`**: CloudFormation templates and Lambda functions for operations AWS accounts
- **`artifacts/`**: Auto-generated build artifacts (SAM builds, packaged templates)
- **`manifest.yaml`**: Service configuration defining portfolios, products, and dependencies

### Lambda Functions
Services can include Lambda functions organized as:
```
customer/lambdas/function-name/
operations/lambdas/function-name/
```

These are automatically built using SAM during the build process.

## Services

### Monitoring Baseline
- **Purpose**: AWS monitoring infrastructure including CloudWatch, OAM, and cost anomaly detection
- **Service Name**: `monitoring-baseline`
- **Portfolios**: `cloud2-monitoring-operations`, `cloud2-monitoring`
- **Products**: Event management, OAM sinks, service management, cost anomalies

### Access Roles
- **Purpose**: IAM role management for secure access control
- **Service Name**: `access-roles`
- **Portfolios**: `cloud2-spotter-access`, `cloud2-access-roles`, `cloud2-operations-access-roles`
- **Products**: Spotter access roles, Cloud2 operations roles, customer access roles

### Reporting
- **Purpose**: Cost and usage reporting infrastructure
- **Service Name**: `reporting-baseline`
- **Portfolios**: `cloud2-reporting-operations`, `cloud2-reporting-customer`
- **Products**: S3 buckets, CUR/FOCUS Glue databases, Athena workgroups, usage exports

## Manifest Configuration

Each service's `manifest.yaml` defines its structure and deployment configuration:

```yaml
service: service-name
description: "Service description"
s3_prefix: services/service-name
github_repository: https://github.com/cloud2dk/repo-name  # Optional

portfolios:
  - name: portfolio-name
    account_type: customer|operations
    description: "Portfolio description"
    stack_name: portfolio-stack-name  # Optional

    products:
      - name: product-name
        description: "Product description"
        template: customer/template.yaml|operations/template.yaml
        scope: global|regional|us-east-1  # Deployment scope
        depends_on:  # Optional dependencies
          - other-product-name
        parameters:  # Optional Service Catalog parameters
          ParameterName:
            Type: String
            Description: Parameter description
```

### Scope Types
- **`global`**: Deploys only to HOME_REGION (eu-central-1)
- **`regional`**: Deploys to all ACTIVE_REGIONS (eu-central-1, eu-west-1, us-east-1)
- **`us-east-1`**: Deploys only to us-east-1 (for region-specific services like BCM Data Exports)

## Deployment Scripts

All services use shared deployment scripts in `scripts/`:

- **`validate.sh`** - Validates manifest.yaml and CloudFormation templates
- **`build.sh`** - Builds SAM applications and packages service artifacts
- **`publish.sh`** - Publishes portfolios and products to AWS Service Catalog
- **`release.sh`** - Manages product version lifecycle in AWS Service Catalog
- **`testing.sh`** - Runs service tests

### Version Lifecycle Management

The release process manages product versions automatically:

- **`MAX_ACTIVE_VERSIONS`** (configurable): Maximum number of active product versions to keep
- **Max Inactive Versions**: 30 (hardcoded): Maximum number of inactive versions to keep
- **Lifecycle**: Active → Deprecated → Deleted

Version management process:
1. New versions are created as active
2. When active versions exceed `MAX_ACTIVE_VERSIONS`, oldest active versions are deprecated
3. When inactive versions exceed 30, oldest inactive versions are deleted

## Deployment

### Automatic Deployment

Each service has its own GitHub Actions workflow with path-based triggers:

- **`services/monitoring-baseline/`** changes → triggers `monitoring-baseline` workflow
- **`services/access-roles/`** changes → triggers `access-roles` workflow
- **`services/reporting/`** changes → triggers `reporting-baseline` workflow
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

Each service deployment goes through two stages:

1. **Build**:
   - Validates `manifest.yaml` and CloudFormation templates
   - Builds SAM applications and packages Lambda functions
   - Creates build artifacts

2. **Deploy**:
   - **Dev Environment**: Publishes portfolios/products to development AWS Service Catalog
   - **Prod Environment**: Publishes portfolios/products to production AWS Service Catalog (after dev success)
   - Manages product version lifecycle automatically

## Environment Variables

The following environment variables are used during deployment:

- **`HOME_REGION`**: Primary AWS region (eu-central-1)
- **`ACTIVE_REGIONS`**: Comma-separated list of deployment regions (eu-central-1,eu-west-1,us-east-1)
- **`SERVICE_ACCOUNT_ID`**: AWS account ID for Service Catalog deployments
- **`VERSION`**: Auto-generated version number (format: 1.2.{github.run_number})
- **`MAX_ACTIVE_VERSIONS`**: Maximum number of active product versions to maintain (configurable)

## Development

### Adding a New Service

1. **Create service structure**:
   ```bash
   mkdir -p services/new-service/{customer,operations,artifacts}
   ```

2. **Create manifest.yaml**:
   ```yaml
   service: new-service
   description: "New service description"
   s3_prefix: services/new-service

   portfolios:
     - name: new-service-portfolio
       account_type: customer|operations
       description: "Portfolio description"
       products:
         - name: product-name
           description: "Product description"
           template: customer/template.yaml
           scope: global|regional|us-east-1
   ```

3. **Add CloudFormation templates** in `customer/` and/or `operations/` directories

4. **Add Lambda functions** (if needed) in `customer/lambdas/` or `operations/lambdas/`

5. **Test locally**:
   ```bash
   cd services/new-service
   ../../scripts/validate.sh
   ../../scripts/build.sh
   ```

6. **Create GitHub workflow** (copy and modify existing workflow in `.github/workflows/`)

7. **Update this README** with new service information

### Adding Products to Existing Services

1. **Update manifest.yaml** - add new product to appropriate portfolio
2. **Create CloudFormation template** in `customer/` or `operations/` directory
3. **Add Lambda functions** (if needed) in respective `lambdas/` directories
4. **Test changes**:
   ```bash
   cd services/service-name
   ../../scripts/validate.sh
   ../../scripts/build.sh
   ```

### Local Development & Testing

```bash
# Validate service configuration
cd services/service-name
../../scripts/validate.sh

# Build service artifacts
../../scripts/build.sh

# Run service tests (if available)
../../scripts/testing.sh

# Build specific templates with SAM
sam build --template-file customer/template.yaml --build-dir artifacts/customer/template
```

### Product Dependencies

Products can depend on other products using the `depends_on` field:

```yaml
products:
  - name: base-product
    template: customer/base.yaml
    scope: global

  - name: dependent-product
    template: customer/dependent.yaml
    scope: regional
    depends_on:
      - base-product
```

Dependencies ensure products are deployed in the correct order.

### Troubleshooting

**Common Issues:**

1. **Build Failures**: Check CloudFormation template syntax and SAM build requirements
2. **Version Conflicts**: Ensure `MAX_ACTIVE_VERSIONS` is appropriate for your deployment frequency
3. **Scope Issues**: Verify region-specific products (like us-east-1) are correctly scoped
4. **Dependency Failures**: Check that dependent products exist and are deployed first

**Debug Commands:**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Validate individual templates
aws cloudformation validate-template --template-body file://template.yaml

# Test SAM builds locally
sam build --template-file template.yaml
```

## AWS Regions

- **Home Region**: eu-central-1 (primary region for global resources)
- **Active Regions**: eu-central-1, eu-west-1, us-east-1 (all deployment regions)