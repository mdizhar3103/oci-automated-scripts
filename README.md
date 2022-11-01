# oci-automated-scripts
This repo contains the automated task using oci cli to manage Oracle Cloud Resources

### Using OCI CLI
```bash
oci compute instance list -c <comp_id> --query 'data[*]."display-name"'
oci compute shape list -c <comp_id> --query 'data[*].[shape, "processor-description"]' --output table 
oci compute image list -c <comp_id> --shape <shape_name> 
oci compute image list -c <comp_id> --shape <shape_name> --query 'data[*].["display-name", id]' --output table


# Token Based Authentication
oci session authenticate 
    # will ask to create a profile, just enter a name 
oci compute instance list -c <comp_id> --query 'data[*]."display-name"' --profile <profile-name> --auth security_token

# Interactive mode in Cloud Shell
oci -i 
```
