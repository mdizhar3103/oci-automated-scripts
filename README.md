# oci-automated-scripts
This repo contains the automated task using oci cli to manage Oracle Cloud Resources

### Using OCI CLI
```bash
oci iam compartment list --compartment-id-in-subtree true | jq -r '.data[].id' > compartment_ocids.txt
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

# List Terminated VM:
PROBLEM_ID='ocid1.cloudguardproblem.oc1.'

oci cloud-guard impacted-resource-summary list-impacted-resources --problem-id  ${PROBLEM_ID} --all | jq -r '.data.items[]."resource-name"'

## Manual Backup List
comp_id='ocid1.compartment.oc1'
oci bv backup list -c $comp_id --query 'data[?"source-type" == `MANUAL`].{name: "display-name",type: "source-type", time_created: "time-created"}' --output table --all
oci bv boot-volume-backup list -c $comp_id --query 'data[?"source-type" == `MANUAL`].{name: "display-name",type: "source-type", time_created: "time-created"}' --output table --all
```
