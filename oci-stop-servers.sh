#!/bin/bash

###############################################################################################################
# Author: Mohd Izhar
#
# Description: This script is used to Stop Oracle Cloud Servers.
#
# Version: v1
#
# Requirement: OCI CLI should be installed and configured in the system where it is being used.
#              Connection testing is done using private IP, so change the IP selection if needed for public IP
#              sendmail, jq, command must be installed.
################################################################################################################

instanceIDs=("ocid1.instance1" "ocid1.instance2")
instanceAction='SOFTSTOP'
instanceState='STOPPED'
intervalCheck=60
instancePort=22

stopDate=stopped_`date +"%F_%H_%M_%S"`.log
echo "Subject: Server Stopped Status" >> ${stopDate}

for instance in ${instanceIDs[@]};
do
    pvtIP=`/bin/oci compute instance list-vnics --instance-id ${instance} | jq -r '.data[]."private-ip"'`
    echo "Stop initiated at $(date +"%T") for Instance with IP: " ${pvtIP} >> ${stopDate} && /bin/oci compute instance action --action ${instanceAction} --instance-id ${instance} --wait-for-state ${instanceState} --wait-interval-seconds ${intervalCheck} >/dev/null | echo "--------------------------------------------------------------------------" >> ${stopDate} && echo "Stopped Finished at $(date +"%T") for Instance with IP: " ${pvtIP} >> ${stopDate} && echo "--------------------------------------------------------------------------" >> ${stopDate} && /usr/sbin/sendmail izhar@xyz.com,mohd.izhar@abc.com < ${stopDate} &
done

/usr/sbin/sendmail izhar@xyz.com,mohd.izhar@abc.com < ${stopDate}
