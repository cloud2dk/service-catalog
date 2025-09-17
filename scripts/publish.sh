#!/bin/bash

set -e

# Validate required environment variables
validate_environment() {
    local environment=$1
    echo checking aws credentials
    echo "--------------------------------" 
    aws sts get-caller-identity > /dev/null
    if [ $? -ne 0 ]; then
        echo "Error: AWS credentials are not set"
        exit 1
    else
        echo "AWS credentials are set"  
    fi
    echo "--------------------------------" 
  
    echo "Validating environment variables"
    local required_vars=("VERSION" "GH_TOKEN" "SERVICE_ACCOUNT_ID" "ACTIVE_REGIONS")
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "Error: ${var} environment variable is not set"
            exit 1
        else
            echo "Environment variable ${var} is set"
        fi
    done

    echo "--------------------------------" }
    echo "Validating first argument is dev or prod"
    if [ "$environment" != "dev" ] && [ "$environment" != "prod" ]; then
        echo "Error: Environment must be dev or prod"
        exit 1
    else
        echo "Using environment: ${environment}"
    fi
    echo "--------------------------------" 
}

# Package a single product template
package_product() {
    local portfolio_name=$1
    local product_name=$2

    local service_name
    service_name=$(yq eval '.service' manifest.yaml)

    # Extract product template path from manifest
    local template_path=$(yq eval ".portfolios[] | select(.name == \"$portfolio_name\") | .products[] | select(.name == \"$product_name\") | .template" manifest.yaml | tr -d '"')
    local template_name=$(basename "${template_path%.*}")
    
    # Get the SAM build output directory for this product
    local product_dir=$(dirname "$template_path")/$template_name    
    local template_file="$product_dir/template.yaml"
    
    # Verify template file exists
    if [ ! -f "$template_file" ]; then
        echo "Error: Template file not found at $template_file"
        exit 1
    fi
    
    echo "Packaging $product_name for $(echo $ACTIVE_REGIONS | tr ',' ' ') regions"

    local s3_prefix="services/$service_name/$VERSION"
    # Preserve the original template path structure for S3
    local s3_product_path="$s3_prefix/$(dirname "$template_path")"
    

    IFS=',' read -ra REGIONS <<< "$ACTIVE_REGIONS"
    
    
    for region in "${REGIONS[@]}"; do
        region=$(echo "$region" | xargs)
        
        # Each region has its own bucket, so we're already region-safe
        local sam_deploy_bucket_name="cloud2-sam-deploy-assets-${SERVICE_ACCOUNT_ID}-${region}"
        local region_output_dir="$product_dir/packaged/$region"
        mkdir -p "$region_output_dir"
        local output_template="$region_output_dir/template.yaml"
        
        echo "  → $region: packaging template"
        
        # Redirect SAM package output to keep things clean
        echo "sam package \\
            --template-file \"$template_file\" \\
            --output-template-file \"$output_template\" \\
            --s3-bucket \"$sam_deploy_bucket_name\" \\
            --s3-prefix \"$s3_product_path\" \\
            --region \"$region\""
            
        sam package \
            --template-file "$template_file" \
            --output-template-file "$output_template" \
            --s3-bucket "$sam_deploy_bucket_name" \
            --s3-prefix "$s3_product_path" \
            --region "$region" > /dev/null 2>&1
        
        # Check if packaging was successful
        if [ $? -ne 0 ]; then
            echo "  ✗ $region: packaging failed"
            exit 1
        fi
        
        # Copy the packaged template to S3
        # Use the basename of the template path from the manifest
        local template_filename=$(basename "$template_path")
        local s3_destination="s3://$sam_deploy_bucket_name/$s3_product_path/$template_filename"
        aws s3 cp "$output_template" "$s3_destination" --quiet
        
        if [ $? -ne 0 ]; then
            echo "  ✗ $region: failed to upload template to S3"
            exit 1
        fi
        
        echo "  ✓ $region: template packaged and uploaded to $s3_destination"
    done
}


# Process all portfolios and their products
process_portfolios() {

    # Loop through portfolios from manifest
    echo "--------------------------------"
    yq eval '.portfolios[] | .name' manifest.yaml
    echo "--------------------------------"

    yq eval '.portfolios[] | .name' manifest.yaml | while read -r portfolio_name; do    
        echo "Processing products for portfolio: $portfolio_name"
        echo "--------------------------------"
        yq eval ".portfolios[] | select(.name == \"$portfolio_name\") | .products[].name" manifest.yaml
        echo "--------------------------------"

        # Loop through products within the portfolio        
        yq eval ".portfolios[] | select(.name == \"$portfolio_name\") | .products[].name" manifest.yaml | while read -r product_name; do
            echo "Processing product template: $product_name"
            package_product "$portfolio_name" "$product_name"
        done
    done
}

# Upload service code to S3
upload_to_s3() {
    local asset_bucket=$1
    s3_prefix=$(yq eval '.s3_prefix' manifest.yaml)
    # Remove the slash in the beginning of s3_prefix if present, to avoid double slashes in the s3 path
    s3_prefix=$(echo "$s3_prefix" | sed 's/^[\/]//')
    service_location="s3://${asset_bucket}/${s3_prefix}/${VERSION}"
    echo "Uploading service code to: ${service_location}"
    
    # Sync everything except build artifacts, git, and other unnecessary files
    aws s3 cp --quiet manifest.yaml "${service_location}/manifest.yaml"
}

# Create a GitHub prerelease with the current version and added the assets to the release
create_github_prerelease() {
    service_name=$(yq eval '.service' manifest.yaml)
    release_name="${service_name}-${VERSION}"
    echo "Creating GitHub prerelease: ${release_name}"
    gh release create "${release_name}" --generate-notes --prerelease
    zip -r --quiet "${release_name}.zip" .
    gh release upload "${release_name}" "${release_name}.zip"
}

# Set the final release to non-prerelease
set_final_release() {
    service_name=$(yq eval '.service' manifest.yaml)
    release_name="${service_name}-${VERSION}"
    echo "Setting final release: ${release_name}"
    gh release edit "${release_name}" --prerelease=false
}

# Main execution
main() {
    local environment=$1
    validate_environment "$environment"

    # HACK, we load the asset bucket from the ssm parameter store, will be removed when implemented in the service
    echo "HACK - We fetch the asset bucket from the ssm parameter store"
    asset_bucket=$(aws ssm get-parameter --name "/cloud2/service-assets-bucket-name" --query "Parameter.Value" --output text)
    process_portfolios
    upload_to_s3 "$asset_bucket"
    if [ "$environment" == "prod" ]; then  
        echo "Setting final release"
        set_final_release 
    else        
        echo "Creating GitHub prerelease"
        create_github_prerelease
    fi
}
main $1

