#!/bin/bash

instanceIDs=("ocid1.instance1"
"ocid1.instance2"
"ocid1.instance3")

instancePort=3389

statusDate=server_status_`date +"%F_%H_%M_%S"`.log
echo "Subject: Server Connectivity Status" >> ${statusDate}


for instance in ${instanceIDs[@]};
do
    instanceDisplayName=`/bin/oci compute instance get --instance-id ${instance} | jq -r '.data | ."display-name", ."lifecycle-state"'`
    pvtIP=`/bin/oci compute instance list-vnics --instance-id ${instance} | jq -r '.data[]."private-ip"'`
    echo -e "${instanceDisplayName}" >> ${statusDate} && echo "quit" | telnet ${pvtIP} ${instancePort} 2>/dev/null | grep -i "Connected" 2>/dev/null 1>> ${statusDate} && echo "--------------------------------------------------------------------------" >> ${statusDate} 
done

/usr/sbin/sendmail -F 'Server Status' izhar@abc.com,mohd.izhar@xyz.com < ${statusDate}
