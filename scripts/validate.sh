#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions for messaging
print_validation_start() {
    echo -n "$1... "
}

print_validation_result() {
    local success=$1
    local error_message=$2
    if [ $success -eq 0 ]; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}ERROR${NC}"
        [ ! -z "$error_message" ] && echo "$error_message"
    fi
    return $success
}

# New global validation message function
print_validation_message() {
    local message=$1
    local success=$2
    local error_message=$3
    local indent=$4
    
    # Print the message with optional indentation
    if [ -n "$indent" ]; then
        echo -n "$indent$message... "
    else
        echo -n "$message... "
    fi
    
    # Print result
    if [ $success -eq 0 ]; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}ERROR${NC}"
        [ ! -z "$error_message" ] && echo "$error_message"
    fi
    return $success
}

# Helper function to validate file existence
validate_file_exists() {
    local base_dir=$1
    local template_path=$2
    [ -f "$base_dir/$template_path" ]
}

# Helper function to validate required parameters in template
validate_template_required_parameters() {
    local template_file=$1
    shift  # Remove template_file from array
    local required_params=("$@")
    
    # First check if file exists
    if [ ! -f "$template_file" ]; then
        return 1
    fi
    
    # Sort and join required parameters
    local required_params_sorted=$(printf '%s\n' "${required_params[@]}" | sort | tr '\n' ',' | sed 's/,$//')
    
    # Check if Parameters section exists and has exactly the required parameters
    local required_params_exists
    required_params_exists=$(yq eval "(.Parameters | keys | sort | join(\",\")) == \"$required_params_sorted\"" "$template_file")

     if [ "$required_params_exists" != "true" ]; then
        return 1
    fi
    
    return 0
}

# Helper function to validate template paths
validate_template_file_paths() {
    local manifest_file=$1
    local base_dir=$2
    local yq_path=$3
    local message=$4
    local error_prefix=$5
    
    local error_found=0
    yq eval "$yq_path" "$manifest_file" | while read -r template_path; do
        # First try relative to workspace root
        if [ -f "$template_path" ]; then
            continue
        # Then try relative to manifest directory
        elif [ -f "$base_dir/$template_path" ]; then
            continue
        else
            print_validation_message "$message" 1 "$error_prefix: $template_path"
            error_found=1
            break
        fi
    done
    [ $error_found -eq 0 ] && print_validation_message "$message" 0
    return $error_found
}

# Helper function to validate product template parameters
validate_product_template_parameters() {
    local manifest_file=$1
    local base_dir=$(dirname "$manifest_file")
    local has_error=0

    print_validation_start "Validating product template parameters"
    
    local portfolio_count=$(yq eval '.portfolios | length' "$manifest_file")
    for ((i=0; i<portfolio_count; i++)); do
        local portfolio_name=$(yq eval ".portfolios[$i].name" "$manifest_file")
        local product_count=$(yq eval ".portfolios[$i].products | length" "$manifest_file")
        
        for ((j=0; j<product_count; j++)); do
            local product_name=$(yq eval ".portfolios[$i].products[$j].name" "$manifest_file")
            local template_path=$(yq eval ".portfolios[$i].products[$j].template" "$manifest_file")
            
            # Check if the template file exists
            if [ ! -f "$template_path" ]; then
                continue  # Skip this iteration as file existence is checked elsewhere
            fi
            
            # Get template parameters
            local template_params
            template_params=$(yq eval '.Parameters | keys | .[]' "$template_path" 2>/dev/null)
            if [ ! $? -eq 0 ] || [ -z "$template_params" ]; then
                template_params=""
            fi
            
            # Get manifest parameters
            local manifest_params=""
            
            # Get parameters from parameters map
            param_names=$(yq eval ".portfolios[$i].products[$j].parameters | keys | .[]" "$manifest_file" 2>/dev/null)
            if [ $? -eq 0 ] && [ ! -z "$param_names" ]; then
                manifest_params="$param_names"
            fi
            
            # Convert parameters to arrays for comparison
            IFS=$'\n' read -d '' -r -a template_params_array <<< "$template_params"
            IFS=$'\n' read -d '' -r -a manifest_params_array <<< "$manifest_params"
            
            # Validation logic
            if [ ${#template_params_array[@]} -eq 0 ] && [ ${#manifest_params_array[@]} -gt 0 ]; then
                print_validation_result 1 "Error: Product '$product_name' in portfolio '$portfolio_name' defines parameters but template '$template_path' has no Parameters section"
                has_error=1
                break 2
            fi
            
            if [ ${#template_params_array[@]} -gt 0 ] && [ ${#manifest_params_array[@]} -eq 0 ]; then
                print_validation_result 1 "Error: Template '$template_path' requires parameters but product '$product_name' in portfolio '$portfolio_name' defines none"
                has_error=1
                break 2
            fi
            
            # Check if all template parameters are present in manifest
            for template_param in "${template_params_array[@]}"; do
                [ -z "$template_param" ] && continue
                local found=0
                for manifest_param in "${manifest_params_array[@]}"; do
                    [ -z "$manifest_param" ] && continue
                    if [ "$template_param" = "$manifest_param" ]; then
                        found=1
                        break
                    fi
                done
                
                if [ $found -eq 0 ]; then
                    print_validation_result 1 "Error: Parameter '$template_param' required by template '$template_path' is not defined for product '$product_name' in portfolio '$portfolio_name'"
                    has_error=1
                    break 3
                fi
            done
            
            # Check if manifest has extra parameters not in template
            for manifest_param in "${manifest_params_array[@]}"; do
                [ -z "$manifest_param" ] && continue
                local found=0
                for template_param in "${template_params_array[@]}"; do
                    [ -z "$template_param" ] && continue
                    if [ "$manifest_param" = "$template_param" ]; then
                        found=1
                        break
                    fi
                done
                
                if [ $found -eq 0 ]; then
                    print_validation_result 1 "Error: Parameter '$manifest_param' defined for product '$product_name' in portfolio '$portfolio_name' is not used in template '$template_path'"
                    has_error=1
                    break 3
                fi
            done
        done
    done
    
    [ $has_error -eq 0 ] && print_validation_result 0
    return $has_error
}

# Function to validate manifest template paths
validate_manifest_template_paths() {
    local manifest_file=$1
    local base_dir=$(dirname "$manifest_file")
    local has_error=0

    # Validate product template paths
    validate_template_file_paths "$manifest_file" "$base_dir" \
        '.portfolios[].products[] | .template' \
        "Validating product templates" \
        "Error: Product template file not found" || has_error=$((has_error + 1))

    return $has_error
}

# Helper function to validate manifest field
validate_manifest_field() {
    local manifest_file=$1
    local yq_path=$2
    local message=$3
    local error_message=$4
    
    print_validation_start "$message"
    if ! yq eval "$yq_path" "$manifest_file" >/dev/null 2>&1; then
        # Get the specific field that failed validation
        local failed_field=$(yq eval "$yq_path | path | .[]" "$manifest_file" 2>/dev/null | tr '\n' '.' | sed 's/\.$//')
        print_validation_result 1 "$error_message (Field: $failed_field)"
        return 1
    fi
    print_validation_result 0
    return 0
}

# Function to validate manifest structure
validate_manifest_structure() {
    local manifest_file=$1
    
    # Basic YAML validation
    if ! yq eval '.' "$manifest_file" >/dev/null 2>&1; then
        print_validation_message "Validating YAML format" 1 "Error: Invalid manifest format. File must be valid JSON/YAML"
        return 1
    fi
    print_validation_message "Validating YAML format" 0

    # Required fields validation
    if ! yq eval 'select(.service != null)' "$manifest_file" >/dev/null 2>&1; then
        local failed_field=$(yq eval '.service | path | .[]' "$manifest_file" 2>/dev/null | tr '\n' '.' | sed 's/\.$//')
        print_validation_message "Validating service field" 1 "Error: Missing or empty required field 'service' (Field: $failed_field)"
        return 1
    fi
    print_validation_message "Validating service field" 0

    # Required field s3_prefix
    if ! yq eval '.s3_prefix != null' "$manifest_file" >/dev/null 2>&1; then
        local failed_field=$(yq eval '.s3_prefix | path | .[]' "$manifest_file" 2>/dev/null | tr '\n' '.' | sed 's/\.$//')
        print_validation_message "Validating s3_prefix field" 1 "Error: Missing or empty required field 's3_prefix' (Field: $failed_field)"
        return 1
    fi
    print_validation_message "Validating s3_prefix field" 0

    if ! yq eval '.portfolios | type=="array"' "$manifest_file" >/dev/null 2>&1; then
        print_validation_message "Validating portfolios structure" 1 "Error: 'portfolios' must be a list"
        return 1
    fi
    print_validation_message "Validating portfolios structure" 0

    # Check for missing products fields in portfolios
    local portfolio_count=$(yq eval '.portfolios | length' "$manifest_file")
    local has_error=0
    
    print_validation_message "Validating portfolio products fields" 0 "" "" "true"
    for ((i=0; i<portfolio_count; i++)); do
        local portfolio_name=$(yq eval ".portfolios[$i].name" "$manifest_file")
        if [ "$(yq eval ".portfolios[$i].products" "$manifest_file")" = "null" ]; then
            print_validation_message "  Validating portfolio: $portfolio_name" 1 "Error: Portfolio is missing required field 'products'"
            has_error=1
            break
        else
            print_validation_message "  Validating portfolio: $portfolio_name" 0
        fi
    done
    [ $has_error -eq 0 ] || return 1

    # Check for missing template fields in products
    print_validation_message "Validating product template fields" 0 "" "" "true"
    for ((i=0; i<portfolio_count; i++)); do
        local portfolio_name=$(yq eval ".portfolios[$i].name" "$manifest_file")
        local product_count=$(yq eval ".portfolios[$i].products | length" "$manifest_file")
        for ((j=0; j<product_count; j++)); do
            local product_name=$(yq eval ".portfolios[$i].products[$j].name" "$manifest_file")
            if [ "$(yq eval ".portfolios[$i].products[$j].template" "$manifest_file")" = "null" ]; then
                print_validation_message "  Validating product: $product_name" 1 "Error: Product is missing required field 'template'"
                has_error=1
                break 2
            else
                print_validation_message "  Validating product: $product_name" 0
            fi
        done
    done
    [ $has_error -eq 0 ] || return 1

    # Validate launch role product references
    print_validation_message "Validating launch role product references" 0 "" "" "true"
    for ((i=0; i<portfolio_count; i++)); do
        local portfolio_name=$(yq eval ".portfolios[$i].name" "$manifest_file")
        local launch_role_product=$(yq eval ".portfolios[$i].launch_role_product" "$manifest_file")
        
        # Skip if launch_role_product is not set
        if [ "$launch_role_product" = "null" ]; then
            print_validation_message "  Validating portfolio: $portfolio_name" 0 "  Skipping - no launch role product specified"
            continue
        fi

        # Check if the referenced product exists in the portfolio
        local product_exists=0
        local product_count=$(yq eval ".portfolios[$i].products | length" "$manifest_file")
        for ((j=0; j<product_count; j++)); do
            local product_name=$(yq eval ".portfolios[$i].products[$j].name" "$manifest_file")
            if [ "$product_name" = "$launch_role_product" ]; then
                product_exists=1
                break
            fi
        done

        if [ $product_exists -eq 0 ]; then
            print_validation_message "  Validating portfolio: $portfolio_name" 1 "Error: References non-existent product '$launch_role_product' in launch_role_product"
            has_error=1
            break
        else
            print_validation_message "  Validating portfolio: $portfolio_name" 0 "  Launch role product '$launch_role_product' found"
        fi
    done
    [ $has_error -eq 0 ] || return 1

    # Validate account types
    print_validation_message "Validating account types" 0 "" "" "true"
    for ((i=0; i<portfolio_count; i++)); do
        local portfolio_name=$(yq eval ".portfolios[$i].name" "$manifest_file")
        local account_type=$(yq eval ".portfolios[$i].account_type" "$manifest_file")
        
        # Skip if account_type is not set
        if [ "$account_type" = "null" ]; then
            print_validation_message "  Validating portfolio: $portfolio_name" 0 "  Skipping - no account type specified"
            continue
        fi

        # Check if account_type is valid
        if [ "$account_type" != "operations" ] && [ "$account_type" != "customer" ]; then
            print_validation_message "  Validating portfolio: $portfolio_name" 1 "Error: Invalid account_type '$account_type'. Valid values are 'operations' or 'customer'"
            has_error=1
            break
        else
            print_validation_message "  Validating portfolio: $portfolio_name" 0 "  Account type '$account_type' is valid"
        fi
    done
    [ $has_error -eq 0 ] || return 1

    return 0
}

# Helper function to check if sam is installed and working
check_sam() {
    if ! command -v sam &> /dev/null; then
        echo "Error: AWS SAM CLI is not installed. Please install it using:"
        echo "  pip install aws-sam-cli"
        return 1
    fi
    
    # Verify sam is working by checking version
    if ! sam --version &> /dev/null; then
        echo "Error: AWS SAM CLI is installed but not working correctly. Please reinstall it using:"
        echo "  pip install aws-sam-cli"
        return 1
    fi
    return 0
}

# Function to validate CloudFormation templates
validate_cloudformation_templates() {
    local manifest_file=$1
    local base_dir=$(dirname "$manifest_file")
    local has_error=0

    print_validation_message "Validating CloudFormation templates" 0 "" "" "true"
    
    # Check if sam is installed and working
    if ! check_sam; then
        print_validation_message "CloudFormation template validation" 1 "CloudFormation template validation skipped - please install a working version of AWS SAM CLI"
        return 1
    fi
    
    # Extract all template paths from manifest
    local templates=$(yq eval '.portfolios[].products[].template' "$manifest_file")
    
    for template_path in $templates; do
        # First try path relative to current directory
        local template_absolute_path="$template_path"
        
        # If not found, try relative to manifest directory
        if [ ! -f "$template_absolute_path" ]; then
            template_absolute_path="$base_dir/$template_path"
        fi
        
        if [ ! -f "$template_absolute_path" ]; then
            continue  # Skip non-existent files as they're caught by another validation
        fi
        
        # Use sam validate to validate the template
        local validate_output
        if ! validate_output=$(sam validate --lint --template "$template_absolute_path" 2>&1); then
            # Check for specific error types
            local error_message=""
            if [[ "$validate_output" == *"Template format error"* ]]; then
                error_message="    Template format error:\n$validate_output"
            elif [[ "$validate_output" == *"Resource validation failed"* ]]; then
                error_message="    Resource validation failed:\n$validate_output"
            elif [[ "$validate_output" == *"Parameter validation failed"* ]]; then
                error_message="    Parameter validation failed:\n$validate_output"
            else
                error_message="    Error:\n$validate_output"
            fi
            print_validation_message "  Validating template: $template_path" 1 "$error_message"
            has_error=1
            break
        else
            print_validation_message "  Validating template: $template_path" 0
        fi
    done
    
    [ $has_error -eq 0 ] && print_validation_message "CloudFormation template validation" 0
    return $has_error
}

main() {
    # Check if manifest file is provided as argument
    if [ $# -ne 1 ]; then
        echo "Error: Please provide a manifest file as argument"
        echo "Usage: $0 <manifest-file>"
        exit 1
    fi

    MANIFEST_FILE=$1

    # Check if file exists
    if [ ! -f "$MANIFEST_FILE" ]; then
        echo "Error: Manifest file '$MANIFEST_FILE' does not exist"
        exit 1
    fi

    echo "Starting manifest validation..."
    echo "==============================="

    # Run structure validation
    if ! validate_manifest_structure "$MANIFEST_FILE"; then
        echo "==============================="
        echo "Manifest structure validation failed"
        exit 1
    fi

    # Run path validation
    if ! validate_manifest_template_paths "$MANIFEST_FILE"; then
        echo "==============================="
        echo "Manifest path validation failed"
        exit 1
    fi
    
    # Run CloudFormation template validation
    if ! validate_cloudformation_templates "$MANIFEST_FILE"; then
        echo "==============================="
        echo "CloudFormation template validation failed"
        exit 1
    fi

    echo "==============================="
    echo "Manifest validation successful"
    exit 0
}

# Execute main function with all script arguments
main "$@"

