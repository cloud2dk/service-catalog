#!/bin/bash

# Exit on any error
set -e

# Get artifacts directory from first argument, default to "artifacts" if not provided
artifacts_dir="${1:-artifacts}"
new_manifest="$artifacts_dir/manifest.yaml"

initialize_artifacts_directory() {
    rm -rf "$artifacts_dir"
    mkdir -p "$artifacts_dir"
}


build_template() {
    local template_file="$1"
    
    echo "template_file: $template_file"

    # Get the directory and name of the template
    template_dir=$(dirname "$template_file")
    template_name=$(basename "${template_file%.*}")

    
    # Create a unique build directory for this template
    unique_build_dir="$artifacts_dir/$template_dir/$template_name"
    echo "artifacts_dir: $artifacts_dir"
    echo "template_dir: $template_dir"
    echo "template_name: $template_name"    
    echo "unique_build_dir: $unique_build_dir"

    mkdir -p "$unique_build_dir"
    
    # Perform SAM build
    echo "Building template: $template_file" >&2
    if ! sam build --template-file "$template_file" --build-dir "$unique_build_dir"; then
        echo "Error: Failed to build template: $template_file" >&2
        return 1
    fi
    return 0
}

update_manifest_template() {
    local manifest_file="$1"
    local portfolio_name="$2"
    local product_name="$3"
    local new_template="$4"
    
    if [ -z "$product_name" ]; then
        # Update portfolio template
        yq eval ".portfolios[] |= (select(.name == \"$portfolio_name\") | .template = \"$new_template\")" -i "$manifest_file"
    else
        # Update product template
        yq eval ".portfolios[] |= (select(.name == \"$portfolio_name\") | .products[] |= (select(.name == \"$product_name\") | .template = \"$new_template\"))" -i "$manifest_file"
    fi
}

process_products() {
    local portfolio_name="$1"
    local has_errors=0
    
    # Check if portfolio exists in the manifest
    if ! yq eval ".portfolios[] | select(.name == \"$portfolio_name\")" manifest.yaml > /dev/null 2>&1; then
        echo "Error: Portfolio '$portfolio_name' not found in manifest" >&2
        return 1
    fi
    
    # Iterate through products in the portfolio
    yq eval ".portfolios[] | select(.name == \"$portfolio_name\") | .products[].name" manifest.yaml | while read -r product_name; do
        # Get the current product template path
        product_template=$(yq eval ".portfolios[] | select(.name == \"$portfolio_name\") | .products[] | select(.name == \"$product_name\") | .template" manifest.yaml | tr -d '"')
        
        # Validate template path
        if [ -z "$product_template" ]; then
            echo "Error: No template found for product '$product_name' in portfolio '$portfolio_name'" >&2
            has_errors=1
            continue
        fi
        
        # Check if template file exists
        if [ ! -f "$product_template" ]; then
            echo "Error: Template file '$product_template' does not exist" >&2
            has_errors=1
            continue
        fi
        
        # Build product template and get the new template path
        if ! build_template "$product_template"; then
            has_errors=1
            continue
        fi
    done
    
    return $has_errors
}

process_portfolios() {
    local has_errors=0
    
    # Iterate through portfolios in the manifest
    yq eval '.portfolios[] | .name' manifest.yaml | while read -r portfolio_name; do
        echo "Processing portfolio: $portfolio_name" >&2
        # Process products within the portfolio
        if ! process_products "$portfolio_name"; then
            has_errors=1
        fi
    done
    
    return $has_errors
}

main() {
    local has_errors=0
    
    if ! initialize_artifacts_directory; then
        echo "Error: Failed to initialize artifacts directory" >&2
        return 1
    fi
    
    if ! process_portfolios; then
        has_errors=1
    fi    
    cp manifest.yaml "$artifacts_dir/manifest.yaml"
    return $has_errors
}

main "$artifacts_dir"