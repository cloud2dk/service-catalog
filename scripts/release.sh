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
    yq eval ".portfolios[] | select(.name == \"$portfolio_name\") | .products[]" manifest.yaml | while IFS= read -r product_line; do
        local product_name=$(echo "$product_line" | yq eval '.name' | tr -d '"')
        local template_path=$(echo "$product_line" | yq eval '.template' | tr -d '"')
        local product_scope=$(echo "$product_line" | yq eval '.scope // "global"' | tr -d '"')

        # Skip regionally-pinned products in wrong regions
        if [ "$product_scope" != "global" ] && [ "$product_scope" != "regional" ] && [ "$product_scope" != "$region" ]; then
            echo "    Skipping product: $product_name (pinned to $product_scope, current region: $region)"
            continue
        fi

        # Build template URL using same bucket naming as publish.sh
        local sam_deploy_bucket_name="cloud2-sam-deploy-assets-${SERVICE_ACCOUNT_ID}-${region}"
        local template_url="https://s3.amazonaws.com/$sam_deploy_bucket_name/services/$service_name/$VERSION/$template_path"

        echo "    Setting up product: $product_name (scope: $product_scope)"
        setup_product "$product_name" "$portfolio_id" "$template_url" "$region"
    done
}

manage_product_versions() {
    local product_id=$1
    local region=$2
    local product_name=$3
    local max_inactive_versions=30

    echo "      Managing versions for product: $product_name (keeping latest $MAX_ACTIVE_VERSIONS active + $max_inactive_versions inactive)"

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

    # Count artifacts
    local total_artifacts=$(echo "$artifacts" | jq length)
    local active_artifacts=$(echo "$artifacts" | jq '[.[] | select(.Active == true)] | length')
    local inactive_artifacts=$(echo "$artifacts" | jq '[.[] | select(.Active == false)] | length')

    echo "        Found $total_artifacts total versions ($active_artifacts active, $inactive_artifacts inactive)"

    # Step 1: Clean up old inactive versions first (keep only latest 30)
    if [ "$inactive_artifacts" -gt "$max_inactive_versions" ]; then
        local inactive_to_delete_count=$(($inactive_artifacts - $max_inactive_versions))
        echo "        Deleting $inactive_to_delete_count old inactive versions..."

        # Get inactive artifacts sorted by creation time, get oldest ones to delete
        local inactive_to_delete=$(echo "$artifacts" | jq -r '[.[] | select(.Active == false)] | sort_by(.CreatedTime) | reverse | .['$max_inactive_versions':] | .[] | .Id')

        for artifact_id in $inactive_to_delete; do
            local artifact_name=$(echo "$artifacts" | jq -r ".[] | select(.Id == \"$artifact_id\") | .Name")
            echo "        Deleting old inactive version: $artifact_name (ID: $artifact_id)"

            aws servicecatalog delete-provisioning-artifact \
                --product-id "$product_id" \
                --provisioning-artifact-id "$artifact_id" \
                --region "$region"

            if [ $? -ne 0 ]; then
                echo "        Error: Failed to delete $artifact_name"
                exit 1
            fi
        done
    fi

    # Step 2: Deprecate excess active versions
    if [ "$active_artifacts" -gt "$MAX_ACTIVE_VERSIONS" ]; then
        local active_to_deprecate_count=$(($active_artifacts - $MAX_ACTIVE_VERSIONS))
        echo "        Deprecating $active_to_deprecate_count excess active versions..."

        # Get active artifacts sorted by creation time (newest first), deprecate oldest
        local active_to_deprecate=$(echo "$artifacts" | jq -r '[.[] | select(.Active == true)] | sort_by(.CreatedTime) | reverse | .['$MAX_ACTIVE_VERSIONS':] | .[] | .Id')

        for artifact_id in $active_to_deprecate; do
            local artifact_name=$(echo "$artifacts" | jq -r ".[] | select(.Id == \"$artifact_id\") | .Name")
            echo "        Deprecating excess active version: $artifact_name (ID: $artifact_id)"

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
    fi

    echo "        ✓ Version cleanup completed"
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
            --provisioning-artifact-parameters "{
                \"Name\": \"$VERSION\",
                \"Description\": \"Version $VERSION\",
                \"Info\": {\"LoadTemplateFromURL\": \"$template_url\"},
                \"Type\": \"CLOUD_FORMATION_TEMPLATE\"
            }" \
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
            # Manage version lifecycle BEFORE adding new version to avoid hitting limits
            manage_product_versions "$product_id" "$region" "$product_name"

            echo "      Adding version $VERSION to existing product"
            aws servicecatalog create-provisioning-artifact \
                --product-id "$product_id" \
                --parameters "{
                    \"Name\": \"$VERSION\",
                    \"Description\": \"Version $VERSION\",
                    \"Info\": {\"LoadTemplateFromURL\": \"$template_url\"},
                    \"Type\": \"CLOUD_FORMATION_TEMPLATE\"
                }" \
                --region "$region"
            echo "      ✓ Version $VERSION added to product: $product_id"
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