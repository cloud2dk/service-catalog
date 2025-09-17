#!/bin/bash

set -e

validate_environment() {
    local environment=$1
    echo "Checking AWS credentials"
    echo "--------------------------------"
    aws sts get-caller-identity > /dev/null
    if [ $? -ne 0 ]; then
        echo "Error: AWS credentials are not set"
        exit 1
    fi
    echo "AWS credentials are set"
    echo "--------------------------------"

    echo "Checking required tools"
    if ! command -v jq &> /dev/null; then
        echo "Error: jq is required for version lifecycle management"
        exit 1
    fi
    echo "jq is available"
    echo "--------------------------------"

    echo "Validating environment variables"
    local required_vars=("VERSION" "SERVICE_ACCOUNT_ID" "ACTIVE_REGIONS" "MAX_ACTIVE_VERSIONS")

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "Error: ${var} environment variable is not set"
            echo "Required variables: VERSION, SERVICE_ACCOUNT_ID, ACTIVE_REGIONS, MAX_ACTIVE_VERSIONS"
            exit 1
        fi
        echo "Environment variable ${var} is set to: ${!var}"
    done

    # Validate MAX_ACTIVE_VERSIONS is a positive integer
    if ! [[ "$MAX_ACTIVE_VERSIONS" =~ ^[1-9][0-9]*$ ]]; then
        echo "Error: MAX_ACTIVE_VERSIONS must be a positive integer, got: $MAX_ACTIVE_VERSIONS"
        exit 1
    fi

    echo "--------------------------------"
    echo "Validating first argument is dev or prod"
    if [ "$environment" != "dev" ] && [ "$environment" != "prod" ]; then
        echo "Error: Environment must be dev or prod"
        exit 1
    fi
    echo "Using environment: ${environment}"
    echo "--------------------------------"
}

# Create or get portfolio ID in a specific region
setup_portfolio_in_region() {
    local portfolio_name=$1
    local region=$2
    local service_name=$3

    echo "  → $region: setting up portfolio '$portfolio_name'"

    # Check if portfolio exists
    local portfolio_id=$(aws servicecatalog list-portfolios \
        --query "PortfolioDetails[?DisplayName=='$portfolio_name'].Id" \
        --output text --region "$region" 2>/dev/null)

    if [ -z "$portfolio_id" ] || [ "$portfolio_id" = "None" ]; then
        echo "    Creating new portfolio: $portfolio_name"
        portfolio_id=$(aws servicecatalog create-portfolio \
            --display-name "$portfolio_name" \
            --description "Portfolio for $service_name service" \
            --query 'PortfolioDetail.Id' \
            --output text --region "$region")
        echo "    ✓ Portfolio created: $portfolio_id"
    else
        echo "    ✓ Portfolio exists: $portfolio_id"
    fi

    # Set up products in this portfolio
    setup_products_for_portfolio "$portfolio_name" "$portfolio_id" "$region" "$service_name"
}

# Create or update products in portfolio
setup_products_for_portfolio() {
    local portfolio_name=$1
    local portfolio_id=$2
    local region=$3
    local service_name=$4

    # Process each product in this portfolio
    yq eval ".portfolios[] | select(.name == \"$portfolio_name\") | .products[].name" manifest.yaml | while read -r product_name; do
        local template_path=$(yq eval ".portfolios[] | select(.name == \"$portfolio_name\") | .products[] | select(.name == \"$product_name\") | .template" manifest.yaml | tr -d '"')

        # Build template URL using same bucket naming as publish.sh
        local sam_deploy_bucket_name="cloud2-sam-deploy-assets-${SERVICE_ACCOUNT_ID}-${region}"
        local template_url="https://s3.amazonaws.com/$sam_deploy_bucket_name/services/$service_name/$VERSION/$template_path"

        echo "    Setting up product: $product_name"
        setup_product "$product_name" "$portfolio_id" "$template_url" "$region"
    done
}

manage_product_versions() {
    local product_id=$1
    local region=$2
    local product_name=$3

    echo "      Managing versions for product: $product_name (keeping latest $MAX_ACTIVE_VERSIONS active)"

    # Get all provisioning artifacts sorted by creation date (newest first)
    local artifacts=$(aws servicecatalog list-provisioning-artifacts \
        --product-id "$product_id" \
        --query 'ProvisioningArtifactDetails | sort_by(@, &CreatedTime) | reverse(@)' \
        --output json --region "$region")

    if [ $? -ne 0 ]; then
        echo "        Error: Failed to list provisioning artifacts for product $product_id"
        exit 1
    fi

    if [ "$artifacts" = "null" ] || [ -z "$artifacts" ]; then
        echo "        Error: No artifacts found for product $product_id"
        exit 1
    fi

    # Count total artifacts
    local total_artifacts=$(echo "$artifacts" | jq length)
    if [ $? -ne 0 ]; then
        echo "        Error: Failed to parse artifacts JSON"
        exit 1
    fi

    echo "        Found $total_artifacts total versions"

    # Count currently active artifacts
    local active_artifacts=$(echo "$artifacts" | jq '[.[] | select(.Active == true)] | length')
    echo "        Currently active versions: $active_artifacts"

    # If we have more than MAX_ACTIVE_VERSIONS active, deprecate the older ones
    if [ "$active_artifacts" -gt "$MAX_ACTIVE_VERSIONS" ]; then
        echo "        Need to deprecate $(($active_artifacts - $MAX_ACTIVE_VERSIONS)) versions..."

        # Get artifacts to deprecate (skip first MAX_ACTIVE_VERSIONS, which are the newest active ones)
        local artifacts_to_deprecate=$(echo "$artifacts" | jq -r ".[$MAX_ACTIVE_VERSIONS:] | .[] | select(.Active == true) | .Id")

        if [ -z "$artifacts_to_deprecate" ]; then
            echo "        No artifacts to deprecate"
            return 0
        fi

        for artifact_id in $artifacts_to_deprecate; do
            local artifact_name=$(echo "$artifacts" | jq -r ".[] | select(.Id == \"$artifact_id\") | .Name")
            echo "        Deprecating artifact: $artifact_name (ID: $artifact_id)"

            aws servicecatalog update-provisioning-artifact \
                --product-id "$product_id" \
                --provisioning-artifact-id "$artifact_id" \
                --no-active \
                --region "$region"

            if [ $? -ne 0 ]; then
                echo "        Error: Failed to deprecate $artifact_name"
                exit 1
            fi
        done

        echo "        ✓ Version lifecycle management completed"
    else
        echo "        ✓ Active version count ($active_artifacts) is within limit ($MAX_ACTIVE_VERSIONS)"
    fi
}

# Create product or add new version
setup_product() {
    local product_name=$1
    local portfolio_id=$2
    local template_url=$3
    local region=$4

    # Check if product already exists in portfolio
    local existing_products=$(aws servicecatalog search-products-as-admin \
        --portfolio-id "$portfolio_id" \
        --query "ProductViewDetails[?ProductViewSummary.Name=='$product_name'].ProductViewSummary.ProductId" \
        --output text --region "$region" 2>/dev/null)

    if [ -z "$existing_products" ] || [ "$existing_products" = "None" ]; then
        # Create new product
        echo "      Creating new product: $product_name"
        local product_id=$(aws servicecatalog create-product \
            --name "$product_name" \
            --owner "Cloud2 Operations" \
            --product-type "CLOUD_FORMATION_TEMPLATE" \
            --provisioning-artifact-parameters "Name=$VERSION,Description=Version $VERSION,Info={LoadTemplateFromURL=$template_url}" \
            --query 'ProductViewDetail.ProductViewSummary.ProductId' \
            --output text --region "$region")

        # Associate with portfolio
        aws servicecatalog associate-product-with-portfolio \
            --product-id "$product_id" \
            --portfolio-id "$portfolio_id" \
            --region "$region"

        echo "      ✓ Product created and associated: $product_id"
    else
        # Check if this version already exists
        local product_id=$existing_products
        local existing_version=$(aws servicecatalog list-provisioning-artifacts \
            --product-id "$product_id" \
            --query "ProvisioningArtifactDetails[?Name=='$VERSION'].Id" \
            --output text --region "$region" 2>/dev/null)

        if [ -z "$existing_version" ] || [ "$existing_version" = "None" ]; then
            echo "      Adding version $VERSION to existing product"
            aws servicecatalog create-provisioning-artifact \
                --product-id "$product_id" \
                --parameters "Name=$VERSION,Description=Version $VERSION,Info={LoadTemplateFromURL=$template_url},Type=CLOUD_FORMATION_TEMPLATE" \
                --region "$region"
            echo "      ✓ Version $VERSION added to product: $product_id"

            # Manage version lifecycle after adding new version
            manage_product_versions "$product_id" "$region" "$product_name"
        else
            echo "      ✓ Version $VERSION already exists for product: $product_id"

            # Still run lifecycle management to ensure older versions are deprecated
            manage_product_versions "$product_id" "$region" "$product_name"
        fi
    fi
}

install_portfolios() {
    local service_name
    service_name=$(yq eval '.service' manifest.yaml)

    echo "Installing Service Catalog portfolios for: $service_name"
    echo "Version: $VERSION"
    echo "Regions: $(echo $ACTIVE_REGIONS | tr ',' ' ')"
    echo "================================"

    # Iterate through portfolios in the manifest
    yq eval '.portfolios[] | .name' manifest.yaml | while read -r portfolio_name; do
        echo "Processing portfolio: $portfolio_name"

        IFS=',' read -ra REGIONS <<< "$ACTIVE_REGIONS"
        for region in "${REGIONS[@]}"; do
            region=$(echo "$region" | xargs)
            setup_portfolio_in_region "$portfolio_name" "$region" "$service_name"
        done
        echo ""
    done

    echo "================================"
    echo "Portfolio installation completed successfully"
}

main() {
    local environment=$1
    validate_environment "$environment"
    install_portfolios
}

main "$@"