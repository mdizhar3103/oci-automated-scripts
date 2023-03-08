#!/bin/bash

###############################################################################################################
# Author: Mohd Izhar
#
# Description: This script is used to take Backup of Oracle Cloud Servers Boot Volume and having 1 Block Volume attached.
#
# Version: v1
#
# Requirement: OCI CLI should be installed and configured in the system where it is being used.
#              Connection testing is done using private IP, so change the IP selection if needed for public IP
#              sendmail, jq, command must be installed.
#
# Note: This is script is configured as per our requirement, kindly modify it before using it. (To understand See if/else block )
################################################################################################################

# compartment OCID
CompID='ocid'

instanceIDs=("ocid1.instance.oc1d"
"ocid1.instance.oc1d"
"ocid1.instance.oc1d")

displayName='-DISPLAY-NAME-'
type='FULL'
BackupState='AVAILABLE'
intervalCheck=60

BackupDate=backup_`date +"%F_%H_%M_%S"`.log
echo "Subject: Volume Backup Status" >> ${BackupDate}

for instance in ${instanceIDs[@]};
do
    ##############################################################################################
    #                           Gathering Instance/Server Details
    ##############################################################################################

    InstanceDetails=$(oci compute instance get --instance-id ${instance})
    AvailDomainID=`echo ${InstanceDetails} | jq -r '.data | ."availability-domain"'`
    InstanceName=`echo ${InstanceDetails} | jq -r '.data | ."display-name"'`

    ##############################################################################################
    #                              Boot Volume Backup Steps
    ##############################################################################################

    BootVolDetails=$(oci compute boot-volume-attachment list --availability-domain ${AvailDomainID} --compartment-id ${CompID} --instance-id ${instance})
    BootVolID=`echo ${BootVolDetails} | jq -r '.data[] | ."boot-volume-id"'`

    BootVolBackupName=${InstanceName}${displayName}`date +"%F"`-IST
    echo -e "-------------------------------------------------------------------------------\nBoot Volume Backup Started for ${InstanceName} at $(date +"%T")" >> ${BackupDate} && oci bv boot-volume-backup create --boot-volume-id ${BootVolID} --type ${type} --wait-for-state ${BackupState} --wait-interval-seconds ${intervalCheck} --display-name ${BootVolBackupName} && echo -e "-------------------------------------------------------------------------------\nBoot Volume Backup Ended for ${InstanceName} at $(date +"%T")\n-------------------------------------------------------------------------------" >> ${BackupDate} && /usr/sbin/sendmail mdizhar@abc.com,izhar@xyz.com < ${BackupDate} &

    ##############################################################################################
    #                              Block Volume Backup Steps
    ##############################################################################################

    BlockVolID=$(oci compute volume-attachment list --compartment-id ${CompID} --instance-id ${instance} | jq -r '.data[]."volume-id"')
    BlockVolName=$(oci bv volume get --volume-id ${BlockVolID} | jq -r '.data."display-name"')

    BlkVolName=BLV-${InstanceName}
    BlockVolBackupName=${BlockVolName}${displayName}`date +"%F"`-IST

    if [ "$BlockVolName" == "$BlkVolName" ]
    then
        echo -e "-------------------------------------------------------------------------------\nBlock Volume Backup Started for ${InstanceName} at $(date +"%T")" >> ${BackupDate} && oci bv backup create --volume-id ${BlockVolID} --type ${type} --wait-for-state ${BackupState} --wait-interval-seconds ${intervalCheck} --display-name ${BlockVolBackupName} && echo -e "Block Volume Backup Ended for ${InstanceName} at $(date +"%T")\n-------------------------------------------------------------------------------" >> ${BackupDate} && /usr/sbin/sendmail mdizhar@abc.com,izhar@xyz.com < ${BackupDate}&
    else
        echo "Block Volume Name Doesn't Match for ${InstanceName} Skipping the Block Volume Backup" >> ${BackupDate}
    fi
done

/usr/sbin/sendmail mdizhar@abc.com,izhar@xyz.com < ${BackupDate}



