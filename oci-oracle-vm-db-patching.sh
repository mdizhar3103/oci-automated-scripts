#!/bin/bash

####################################################################################################################
# Author: Mohd Izhar
#
# Description: This script is to perform Database patching for Virtual Machine (VM) based Oracle Database with
#              Logical Volume Manager Storage using OCI CLI.
#
# Requirement: OCI-CLI, JQ must be installed to run this script and OCI CLI must be configured to perform operation.
#
# Version: v1.1
####################################################################################################################

DB_OCID="ocid1.database.oc1."

get_header() {
    echo -e "--> $1 \n" >> ${log_file}
}

get_banner() {
    echo "============================================================================================================" >> ${log_file}
}

patch_details() {
    echo -e "\t$1" >> ${log_file}
}

get_db_details() {
    patch_details "DB System Name: $db_system_name"
    patch_details "Database Name: \"$DB_NAME\""
    patch_details "Database Version: $db_home_version"
}

# Check Patch Status
get_patch_status(){
    oci db patch-history list by-database --database-id $DB_OCID 
}

check_failure_status() {
    if [[ `get_patch_status | jq -r '.data[0]."lifecycle-state"'` =~ "FAILED" ]]; 
    then 
        patch_details "Precheck End Time: $(date +"%T")"
        patch_details "Result: FAILED"
        patch_details "Error Log: $(get_patch_status | jq -r '.data[0]."lifecycle-details"')" 
        get_banner
        exit 1; 
    fi
}

wait_for_result() {
    until [[ `get_patch_status | jq -r '.data[0]."lifecycle-state"'` =~ "SUCCEEDED" ]] ; 
    do 
        sleep 30;
        check_failure_status  
    done
}

log_file=db_patch_`(date +%Y_%m_%d_%H_%M_%S)`.log

# Get DB System Details
get_banner 
PATCH_START_TIME=$(date +"%T") 
echo -e "Oracle VM Database Patching Started At $PATCH_START_TIME " >> ${log_file}
get_banner

db_details=$(oci db database get --database-id $DB_OCID)
DB_SYSTEM_OCID=`echo $db_details | jq -r  '.data | ."db-system-id"'`
db_system_name=$(oci db system get --db-system-id $DB_SYSTEM_OCID --query 'data."display-name"')

DB_HOME_OCID=`echo $db_details | jq -r  '.data | ."db-home-id"'`
db_home_version=$(oci db db-home get --db-home-id $DB_HOME_OCID --query 'data."db-version"')
DB_NAME=`echo $db_details | jq -r  '.data | ."db-name"'`

get_header "DB System Details" 
get_db_details

#=====================================================================================================================

# List Available Patches
get_banner
get_header "Available Patches Details for Database ${DB_NAME}"
db_patch_list=$(oci db patch list by-database --database-id $DB_OCID --all)
echo $db_patch_list | jq -r  '.data[] | [.description, .version] | @tsv' >> ${log_file}
get_banner

get_header "Important Instruction Before Running Script"
echo -e "Note: If multiple updates are available, by default script will apply the latest update within next 10 mins.\nPlease take appropriate action before Precheck is completed." >> ${log_file}
get_banner
sleep 3

get_header "Latest Patch Details" 
db_latest_patch=`echo $db_patch_list | jq -r  '.data[0] | .description + " --> " + .version'`
latest_patch=`echo $db_latest_patch`
patch_id=`echo $db_patch_list | jq -r  '.data[0] | .id'`
patch_details "Patch Description: $latest_patch"
patch_details "Patch ID: $patch_id" 
get_banner

#=====================================================================================================================

# Running Precheck
get_header "Patching Precheck Details" 
PATCH_PRECHECK='PRECHECK'

# check if precheck already performed
patch_history=`get_patch_status`
last_patch_history_action=`echo $patch_history | jq -r '.data[0]."action"'`
last_patch_history_state=`echo $patch_history | jq -r '.data[0]."lifecycle-state"'`
last_patch_history_patch_id=`echo $patch_history | jq -r '.data[0]."patch-id"'`

patch_details "Precheck Start Time: $(date +"%T")"

if [[ ($last_patch_history_action == "PRECHECK") && ($last_patch_history_state == "SUCCEEDED") && ($last_patch_history_patch_id == $patch_id)]]
then
    patch_details "Precheck End Time: $(date +"%T")"
    patch_details "Result: SKIPPED (Precheck already Performed)"
    get_banner
else
    oci db database patch --database-id $DB_OCID --patch-action $PATCH_PRECHECK --patch-id $patch_id > /dev/null

    wait_for_result

    patch_details "Precheck End Time: $(date +"%T")"
    patch_details "Result: SUCCEEDED"
fi

#=====================================================================================================================

# Applying Patch
PATCH_APPLY='APPLY'
get_header "Apply Patching Details"
patch_details "Patch Start Time: $(date +"%T")"
sleep 300
oci db database patch --database-id $DB_OCID --patch-action $PATCH_APPLY --patch-id $patch_id > /dev/null

wait_for_result

patch_details "Patch End Time: $(date +"%T")"
patch_details "Result: SUCCEEDED"
get_banner

PATCH_END_TIME=$(date +"%T")
echo -e "Oracle VM Database Patching Finished At $PATCH_END_TIME " >> ${log_file}
get_banner

#=====================================================================================================================

# Patch Result
get_header "Checking Patching Results"
sleep 30
db_home_version=$(oci db db-home get --db-home-id $DB_HOME_OCID --query 'data."db-version"')
get_db_details

