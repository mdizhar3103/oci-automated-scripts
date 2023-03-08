#!/bin/bash

####################################################################################################################
# Author: Mohd Izhar
#
# Description: This script is to check the compliance status of OCI Servers managed via OSMS.
#
# Requirement: OCI-CLI must be configured to perform operation and python3 must be installed.
#
# Version: v1.1
####################################################################################################################

COMP_ID='ocid1.compartment.'
REGION='xx-region-x'
COMPLIANCE_FILE='/path_to/compliance_report.py'
Managed_Instance_ID='ocid1.osmsmanagedinstancegroup.'

LOG_FILE=osms_report_`date +"%F_%H_%M_%S"`.log


echo "Subject: OSMS Compliance Status" >> ${LOG_FILE}

/bin/python3 $COMPLIANCE_FILE --compartment-ocid=$COMP_ID  --show-details --region=$REGION -g=$Managed_Instance_ID >> ${LOG_FILE}

sleep 2

# Remove OCID from log file
sed -i -e 's/(ocid[A-Za-z0-9.)]*//g' ${LOG_FILE}

sleep 2

/usr/sbin/sendmail izhar@xyz.com,mohd.izhar@abc.com < ${LOG_FILE}
