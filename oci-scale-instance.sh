#!/bin/bash

###############################################################################################################
# Author: Mohd Izhar
#
# Description: This script is used to perform Instances (VMs) scaling of Oracle Cloud Servers.
#              Note: Only Standard Shape are supported to run this script.
# Version: v1
#
# Requirement: OCI CLI should be installed and configured in the system where it is being used.
#              sendmail, jq, nc, telnet command must be installed.
################################################################################################################

new_instance_shape='VM.x.x'
instance_id='ocid1.instance.oc1.'
instancePort=3389

scalingDate=scaling_`date +"%F_%H_%M_%S"`.log
echo "Subject: Server Scaling Status" >> ${scalingDate}


# get current instance configurations
get_instance_details() {
    InstanceDetails=$(oci compute instance get --instance-id ${instance_id});
    InstanceName=`echo ${InstanceDetails} | jq -r '.data."display-name"'`;
    InstanceState=`echo ${InstanceDetails} | jq -r '.data."lifecycle-state"'`;
    InstanceShape=`echo ${InstanceDetails} | jq -r '.data."shape"'`;
    echo -e "\nInstance ${InstanceName} is in ${InstanceState} State and current configuration is ${InstanceShape}" >> ${scalingDate}
}


pvtIP=`oci compute instance list-vnics --instance-id ${instance_id} | jq -r '.data[]."private-ip"'`

get_instance_details
sleep 5
echo -e "Instance ${InstanceName} will be updated to ${new_instance_shape}" >> ${scalingDate}
sleep 5

SCALING_START_TIME=$(date +"%T") 
echo -e "Instance Scaling Started At $SCALING_START_TIME" >> ${scalingDate}

if [[ ($InstanceState == "STOPPED") ]]
then
    oci compute instance update --instance-id ${instance_id} --shape ${new_instance_shape}
else
    # scale instance
    oci compute instance update --instance-id ${instance_id} --shape ${new_instance_shape} --wait-for-state RUNNING && until nc -z -w30 ${pvtIP} ${instancePort}; do sleep 1; done && echo "quit" | telnet ${pvtIP} ${instancePort} 2>/dev/null | grep -i "Connected" 2>/dev/null 1>> ${scalingDate}
fi

SCALING_END_TIME=$(date +"%T") 
echo -e "Instance Scaling Completed At $SCALING_END_TIME" >> ${scalingDate}

echo -e "Verifying the upgrade" >> ${scalingDate}
get_instance_details

# /usr/sbin/sendmail mdizhar@abc.com,izhar@xyz.com < ${scalingDate}
