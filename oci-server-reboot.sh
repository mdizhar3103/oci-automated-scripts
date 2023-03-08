#!/bin/bash

###############################################################################################################
# Author: Mohd Izhar
#
# Description: This script is used to perform reboot of Oracle Cloud Servers.
#
# Version: v1
#
# Requirement: OCI CLI should be installed and configured in the system where it is being used.
#              Connection testing is done using private IP, so change the IP selection if needed for public IP
#              sendmail, jq, nc, telnet command must be installed.
################################################################################################################

instanceIDs=("" "" "")
instanceAction='SOFTRESET'
instanceState='RUNNING'
intervalCheck=60
instancePort=22

rebootDate=reboot_`date +"%F_%H_%M_%S"`.log
echo "Subject: Server Reboot Status" >> ${rebootDate}

for instance in ${instanceIDs[@]};
do
    InstanceDetails=$(oci compute instance get --instance-id ${instance})
    InstanceName=`echo ${InstanceDetails} | jq -r '.data | ."display-name"'`
    pvtIP=`oci compute instance list-vnics --instance-id ${instance} | jq -r '.data[]."private-ip"'`
    echo "Reboot Started at $(date +"%T") for Instance ${InstanceName} with IP: ${pvtIP}" >> ${rebootDate} && oci compute instance action --action ${instanceAction} --instance-id ${instance} --wait-for-state ${instanceState} --wait-interval-seconds ${intervalCheck} >/dev/null | echo "--------------------------------------------------------------------------" >> ${rebootDate} && until nc -z -w30 ${pvtIP} ${instancePort}; do sleep 1; done && echo "quit" | telnet ${pvtIP} ${instancePort} 2>/dev/null | grep -i "Connected" 2>/dev/null 1>> ${rebootDate} && echo "Reboot Finished at $(date +"%T") for Instance ${InstanceName} with IP: ${pvtIP}" >> ${rebootDate} && echo "--------------------------------------------------------------------------" >> ${rebootDate} && /usr/sbin/sendmail mdizhar@abc.com,izhar@xyz.com < ${rebootDate} &
done

/usr/sbin/sendmail mdizhar@abc.com,izhar@xyz.com < ${rebootDate}
