#------------------------------------------------------------------------------------------------------
# Pushing Bulk Data to OCI Object storage Bucket based on Success Flag and cleaning the old logs/files 
#------------------------------------------------------------------------------------------------------

# dummy folder to push on bucket
var_file=FOLDER_`(date +%Y_%m_%d)`

if [[ -f /path_to_folder/FlagSuccessful ]]
then
    ~/bin/oci os object bulk-upload -ns <BUCKET-NAMESPACE> -bn  <BUCKET-NAME> --src-dir /path_to_folder/ --include $var_file* --overwrite
    rm -rf /path_to_folder/FlagSuccessful
fi

# Cleanup old logs (Have not been accessed for (n) days).
LOGDIR='/path_to_folder/'
find ${LOGDIR} -name "filname_*.log" -atime +30 -print -exec rm {} \;
