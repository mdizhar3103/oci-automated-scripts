#!/bin/bash

###############################################################################################################
# Author: Mohd Izhar
#
# Description: This script is used to Stop All Oracle Cloud Servers.
#
# Version: v1
#
# Requirement: OCI CLI should be installed and configured in the system where it is being used.
################################################################################################################

comp_ids=("ocid1.compartment.oc1.."
"ocid1.compartment.oc1.."
)

instanceAction='SOFTSTOP'
instanceState='STOPPED'
intervalCheck=10

stopDate=stopped_`date +"%F_%H_%M_%S"`.log

for compt in ${comp_ids[@]}:
do 
  instanceIDs=`oci compute instance list -c ${compt} | jq -r '.data[].id'`
  for instance in ${instanceIDs[@]};
  do
    #echo ${instance}
    pvtIP=`oci compute instance list-vnics --instance-id ${instance} | jq -r '.data[]."private-ip"'`
    echo "Stop initiated at $(date +"%T") for Instance with IP: " ${pvtIP} >> ${stopDate} && oci compute instance action --action ${instanceAction} --instance-id ${instance} --wait-for-state ${instanceState} --wait-interval-seconds ${intervalCheck} >/dev/null | echo "--------------------------------------------------------------------------" >> ${stopDate} &
  done
done
