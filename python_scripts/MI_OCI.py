import oci
import argparse
import time
from datetime import datetime


config = oci.config.from_file()
tenancy_id = config["tenancy"]


def is_empty(obj):
    if len(obj) <= 0:
        return True
    return False


class IdentityClientInfo:

    def __init__(self):
        self.identity_client = oci.identity.IdentityClient(config)

    def get_compartments(self, tenancy_id):
        list_compartments_response = self.identity_client.list_compartments(
            compartment_id = tenancy_id,
            limit = 193,
            access_level = "ANY",
            compartment_id_in_subtree = True,
            sort_by = "NAME",
            sort_order = "ASC")

        compartment_objects = list_compartments_response.data

        if is_empty(compartment_objects):
            return 

        compartments = {}

        for compartment_details in compartment_objects:
            comp_name = compartment_details.name
            comp_id = compartment_details.id
            # "\t{0:>30}: {1:<10}".format(comp_name, comp_id)
            compartments[comp_name] = comp_id

        return compartments
    

    def get_availability_domains(self, comp_id):
        list_availability_domains_response = self.identity_client.list_availability_domains(
            compartment_id = comp_id)
        ad_objects = list_availability_domains_response.data
        
        if is_empty(ad_objects):
            return

        ads = {}

        for ad_details in ad_objects:
            ad_name = ad_details.name
            ad_id = ad_details.id
            ads[ad_name] = ad_id

        return ads 

    def __str__(self):
        return str(self.get_compartments(tenancy_id))
        

class ObjectStorageDetails:

    _NAMESPACE = ""

    def __init__(self):
        self.object_storage_client = oci.object_storage.ObjectStorageClient(config)


    @classmethod
    def  get_namespace(cls):
        return cls._NAMESPACE


    @classmethod
    def set_namespace(cls, value):
        if not value.isalnum() or len(value) == 0:
            raise ValueError("Invalid Value Passed")
        
        cls._NAMESPACE = value

    
    def bucket_lists(self, comp_id):
        list_buckets_response = self.object_storage_client.list_buckets(
            namespace_name = ObjectStorageDetails.get_namespace(),
            compartment_id = comp_id,
            limit=364,)

        bucket_objects = list_buckets_response.data

        if is_empty(bucket_objects):
            return

        buckets = []

        for bucket_details in bucket_objects:
            bucket_name = bucket_details.name
            buckets.append(bucket_name)

        return buckets


    def object_lists(self, BUCKET, OBJECT_NAME):
        list_objects_response = self.object_storage_client.list_objects(
            namespace_name = ObjectStorageDetails.get_namespace(),
            bucket_name = BUCKET,
            prefix = OBJECT_NAME,
            fields = "name,timeCreated,size",
            limit = 880)
            
        obj_objects = list_objects_response.data.objects

        if is_empty(obj_objects):
            return

        objs = []

        for object in obj_objects:
            obj_time_created = object.time_created.strftime('%Y-%m-%d %H:%M:%S')
            obj_name = object.name
            obj_size = object.size
            # print(f"\t{obj_name}\t\t{obj_time_created}\t\t{convert_bytes(obj_size)}")
            objs.append((obj_name, obj_time_created, obj_size))

        return objs


class FSSDetails:

    def __init__(self):
        self.file_storage_client = oci.file_storage.FileStorageClient(config)

    def get_filessytems(self, comp_id, ad_name):
        list_file_systems_response = self.file_storage_client.list_file_systems(
            compartment_id = comp_id,
            availability_domain=ad_name,
            limit=968)
        
        file_system_objects = list_file_systems_response.data
        if is_empty(file_system_objects):
            return

        fss = {}

        for files_system_details in file_system_objects:
            fs_name = files_system_details.display_name
            fs_id = files_system_details.id
            fss[fs_name] = fs_id

        return fss


    def get_snapshots(self, fs_id):
        list_snapshots_response = self.file_storage_client.list_snapshots(
            file_system_id = fs_id,
            limit = 30,)

        snaphot_objects = list_snapshots_response.data

        if is_empty(snaphot_objects):
            return

        snapshots = []

        for snaphot_object_details in snaphot_objects:
            snapshot_name = snaphot_object_details.name
            snapshots.append(snapshot_name)

        return snapshots


class CloudGuardDetails:

    def __init__(self):
        self.cloud_guard_client = oci.cloud_guard.CloudGuardClient(config)

    
    def cloud_guard_problems(self, comp_id):
        list_problems_response = self.cloud_guard_client.list_problems(
            compartment_id = comp_id,
            lifecycle_state = "ACTIVE",
            risk_level = "CRITICAL",
            limit=158,)

        cloud_guard_objects = list_problems_response.data
        
        cg_objects = cloud_guard_objects.items

        if is_empty(cg_objects):
            return

        cg_problems = []

        for cg_object_details in cg_objects:
            detector_rule_id = cg_object_details.detector_rule_id
            resource_name = cg_object_details.resource_name
            cg_problems.append((detector_rule_id, resource_name))

        return cg_problems


class OSMSClient:

    def __init__(self):
        self.os_management_client = oci.os_management.OsManagementClient(config)


    def list_osms_managed_instance_groups(self, comp_id):
        list_managed_instance_groups_response = self.os_management_client.list_managed_instance_groups(
            compartment_id = comp_id,
            limit = 809,)

        osms_managed_instance_grps_objects = list_managed_instance_groups_response.data

        osms_managed_instance_grps = []

        for osms_managed_instance_grp_details in osms_managed_instance_grps_objects:
            display_name = osms_managed_instance_grp_details.display_name
            osms_managed_instance_grp_ocid = osms_managed_instance_grp_details.id
            os_family = osms_managed_instance_grp_details.os_family
            managed_instance_count = osms_managed_instance_grp_details.managed_instance_count
            osms_managed_instance_grps.append((display_name, osms_managed_instance_grp_ocid, os_family, managed_instance_count))

        return osms_managed_instance_grps


    def get_osms_managed_instance_grps(self, osms_managed_instance_group_id):
        get_managed_instance_group_response = self.os_management_client.get_managed_instance_group(
        managed_instance_group_id = osms_managed_instance_group_id,
        )

        get_managed_instance_group_objects = get_managed_instance_group_response.data
        return get_managed_instance_group_objects.managed_instances


    def list_available_updates_for_instance(self, instance_id):
        list_available_updates_for_instance_response = self.os_management_client.list_available_updates_for_managed_instance(
            managed_instance_id = instance_id,
            limit = 418,)

        list_available_updates_for_instance_objects = list_available_updates_for_instance_response.data

        updates_av = []

        for list_available_updates_for_instance_details in list_available_updates_for_instance_objects:
            available_version = list_available_updates_for_instance_details.available_version
            package_name = list_available_updates_for_instance_details.display_name
            update_type = list_available_updates_for_instance_details.update_type
            updates_av.append(f'{package_name} will be updated to {available_version} - {update_type}')

        return updates_av


class OracleAnnouncments:

    def __init__(self) -> None:
        self.announcements_service_client = oci.announcements_service.AnnouncementClient(config)

    def list_oracle_announcement(self, comp_id):
        list_announcements_response = self.announcements_service_client.list_announcements(
            compartment_id = comp_id,
            limit = 714,)

        list_announcements_objects = list_announcements_response.data

        if is_empty(list_announcements_objects.items):
            return 

        announcements = []

        for list_announcement_details in list_announcements_objects.items:
            affected_regions = list_announcement_details.affected_regions
            announcement_type = list_announcement_details.announcement_type
            summary = list_announcement_details.summary
            reference_ticket_number = list_announcement_details.reference_ticket_number
            services = list_announcement_details.services
            time_one_type = list_announcement_details.time_one_type
            time_one_value = list_announcement_details.time_one_value
            time_two_type = list_announcement_details.time_two_type
            time_two_value = list_announcement_details.time_two_value
            time_updated = list_announcement_details.time_updated.strftime('%Y-%m-%d %H:%M:%S')
            announcements.append((affected_regions, announcement_type, summary, 
                                  reference_ticket_number, services, time_one_type, 
                                  time_one_value, time_two_type, time_two_value, time_updated))

        return announcements


class DBSystemDetails:

    def __init__(self):
        self.database_client = oci.database.DatabaseClient(config)


    def list_dbsystems(self, comp_id):
        list_db_systems_response = self.database_client.list_db_systems(
            compartment_id = comp_id,
            limit=260,)

        list_db_systems_objects = list_db_systems_response.data

        if is_empty(list_db_systems_objects):
            return

        list_db_homes_response = self.database_client.list_db_homes(
            compartment_id = comp_id,
            limit=395,)
        
        db_versions = {}

        list_db_homes_objects = list_db_homes_response.data
        if not is_empty(list_db_homes_objects):
            for list_db_homes_details in list_db_homes_objects:
                dbsys_id = list_db_homes_details.db_system_id
                db_ver = list_db_homes_details.db_version
                db_versions[dbsys_id] = db_ver

        db_systems = {}

        for list_db_systems_details in list_db_systems_objects:
            display_name = list_db_systems_details.display_name
            db_shape = list_db_systems_details.shape
            database_edition = list_db_systems_details.database_edition
            hostname = list_db_systems_details.hostname
            storage_type = list_db_systems_details.db_system_options.storage_management
            ocid = list_db_systems_details.id
            db_ver = db_versions.get(ocid, '-')

            db_systems[ocid] = [display_name, db_shape, database_edition, hostname, storage_type, db_ver]

        return db_systems


class LoadBalancerDetails:

    def __init__(self):
        self.load_balancer_client = oci.load_balancer.LoadBalancerClient(config)


    def list_lbs(self, comp_id):
        list_load_balancers_response = self.load_balancer_client.list_load_balancers(
            compartment_id = comp_id,
            limit=320,)

        list_load_balancers_objects = list_load_balancers_response.data

        if is_empty(list_load_balancers_objects):
            return

        lbs = []

        for list_load_balancer_details in list_load_balancers_objects:
            display_name = list_load_balancer_details.display_name
            shape_name = list_load_balancer_details.shape_name
            lb_ip_address = list_load_balancer_details.ip_addresses
            
            lb_ips = ""
            for ip_addresses in lb_ip_address:
                lb_ips = ip_addresses.ip_address + lb_ips + ", "
            
            lb_hostnames = ""
            hostnames = list_load_balancer_details.hostnames
            for hostname_details in hostnames.values():
                hostname = hostname_details.hostname
                lb_hostnames = hostname + ", " + lb_hostnames 
            
            backend_sets = list_load_balancer_details.backend_sets

            lbs.append((display_name, shape_name, lb_ips, lb_hostnames, backend_sets))

        return lbs


class VPNDetails:

    def __init__(self):
        self.core_client = oci.core.VirtualNetworkClient(config)

    def list_ipsecs(self, comp_id):
        list_ip_sec_connections_response = self.core_client.list_ip_sec_connections(
            compartment_id = comp_id,
            limit = 55,)

        list_ip_sec_connections_objects = list_ip_sec_connections_response.data
        if is_empty(list_ip_sec_connections_objects):
            return 

        ipsecs = []

        for list_ip_sec_connection_details in list_ip_sec_connections_objects: 
            cpe_local_identifier = list_ip_sec_connection_details.cpe_local_identifier
            cpe_local_identifier_type = list_ip_sec_connection_details.cpe_local_identifier_type
            display_name = list_ip_sec_connection_details.display_name
            ocid = list_ip_sec_connection_details.id
            static_routes = list_ip_sec_connection_details.static_routes
            ipsecs.append((cpe_local_identifier,  cpe_local_identifier_type, display_name, ocid, static_routes))
        return ipsecs

    def list_tunnels(self, ipsec_id):
        list_ip_sec_connection_tunnels_response = self.core_client.list_ip_sec_connection_tunnels(
            ipsc_id = ipsec_id)

        list_ip_sec_connection_tunnel_objects = list_ip_sec_connection_tunnels_response.data
        if is_empty(list_ip_sec_connection_tunnel_objects):
            return

        tunnels = []

        for list_ip_sec_connection_tunnel_details in list_ip_sec_connection_tunnel_objects:
            display_name = list_ip_sec_connection_tunnel_details.display_name
            dpd_mode = list_ip_sec_connection_tunnel_details.dpd_mode
            dpd_timeout_in_sec = list_ip_sec_connection_tunnel_details.dpd_timeout_in_sec
            encryption_domain_config = list_ip_sec_connection_tunnel_details.encryption_domain_config
            ike_version = list_ip_sec_connection_tunnel_details.ike_version
            oracle_can_initiate = list_ip_sec_connection_tunnel_details.oracle_can_initiate
            phase_one_details = list_ip_sec_connection_tunnel_details.phase_one_details
            phase_two_details = list_ip_sec_connection_tunnel_details.phase_two_details
            routing = list_ip_sec_connection_tunnel_details.routing
            status = list_ip_sec_connection_tunnel_details.status
            time_status_updated = list_ip_sec_connection_tunnel_details.time_status_updated
            vpn_ip = list_ip_sec_connection_tunnel_details.vpn_ip

            tunnels.append((display_name, dpd_mode, dpd_timeout_in_sec, encryption_domain_config, ike_version, oracle_can_initiate, phase_one_details, phase_two_details, routing, status, time_status_updated, vpn_ip))
        return tunnels


class InstanceDetails:
    def __init__(self) -> None:
        self.core_client = oci.core.ComputeClient(config)
        self.metric_client = oci.monitoring.MonitoringClient(config)

    def list_all_compartments(self, comp_id):
        list_instances_response = self.core_client.list_instances(
            compartment_id = comp_id,
            limit = 97,)

        list_instances_objects = list_instances_response.data

        if is_empty(list_instances_objects):
            return

        instances = []

        for list_instances_details in list_instances_objects:
            display_name = list_instances_details.display_name
            lifecycle_state = list_instances_details.lifecycle_state
            shape = list_instances_details.shape
            ocid = list_instances_details.id

            instances.append((ocid, display_name, lifecycle_state, shape))
        return instances


    def instance_utilization(self, comp_id, instance_id):
        if comp_id is None or instance_id is None:
            return "No Compartment ID and Instance ID passed"

        metric_detail = oci.monitoring.models.SummarizeMetricsDataDetails()
        metric_detail.query = 'CPUUtilization[60m]{' + f'resourceId = {instance_id}' + '}.max()'
        now_dt = datetime.today()
        end_dt = datetime(now_dt.year, now_dt.month, now_dt.day, now_dt.hour, now_dt.minute)
        start_dt = datetime(now_dt.year, now_dt.month, now_dt.day - 1, now_dt.hour, now_dt.minute)
        metric_detail.start_time = "{}.000Z".format(start_dt.isoformat())
        metric_detail.end_time = "{}.000Z".format(end_dt.isoformat())
        metric_detail.resolution = "1h"
        metric_detail.namespace = "oci_computeagent"

        return self.metric_client.summarize_metrics_data(comp_id, metric_detail).data


def display_headers(banner='='):
    print(banner * 200)


def get_today_date():
    dt = datetime.today()
    today_date = dt.date().strftime("%Y_%m_%d") 

    return today_date


def convert_bytes(size):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return "%3.1f %s" % (size, x)
        size /= 1024.0

    return size


def latest_announcement(announcements):
    if announcements is None or len(announcements) == 0:
            print(f'\n---> No Latest Announcements recevied from Oracle\n')
    else:
        affected_regions = announcements[0][0]
        announcement_type = announcements[0][1]
        summary = announcements[0][2]
        reference_ticket_number = announcements[0][3]
        services = announcements[0][4]
        time_one_type = announcements[0][5]
        time_one_value = announcements[0][6]
        time_two_type = announcements[0][7]
        time_two_value = announcements[0][8]
        time_updated = announcements[0][9]
        print('\t{0:>15}: {1:<15}'.format('Affected Regions', str(affected_regions)))
        print('\t{0:>15}: {1:<15}'.format('Type', str(announcement_type)))
        print('\t{0:>15}: {1:<15}'.format('Summary', str(summary)))
        print('\t{0:>15}: {1:<15}'.format('Ticket Number', str(reference_ticket_number)))
        print('\t{0:>15}: {1:<15}'.format('Services', str(services)))
        print('\t{0:>15}: {1:<15}'.format(time_one_type, str(time_one_value)))
        print('\t{0:>15}: {1:<15}'.format(time_two_type, str(time_two_value)))
        print('\t{0:>15}: {1:<15}'.format('Update Time', time_updated))


def display_object_storage(ns, comp_id, OBJECT_NAME = None):
    obj_storage = ObjectStorageDetails()
    obj_storage.set_namespace(ns)                                               
    buckets = obj_storage.bucket_lists(comp_id)
    
    if buckets is None:
        print('\n---> No Buckets Found.\n')
    else:
        display_headers()
        
        if OBJECT_NAME in (None, ''):
            OBJECT_PREFIX='RMANBKP_'
            td = get_today_date()
            OBJECT_NAME = OBJECT_PREFIX + td
        
        print('\n---> BUCKETS\n\n')
        for bucket in buckets:
            print(f'\n\t{bucket}\n')

            obj_lists = obj_storage.object_lists(bucket, OBJECT_NAME)
            if obj_lists is None:
                print(f"\t\tNo Object Match Found")                
                continue
        
            for obj_prefix in obj_lists:
                obj_name = obj_prefix[0]
                obj_time_created = obj_prefix[1]
                obj_size = obj_prefix[2]
                print(f"\t\t{obj_name}\t\t{obj_time_created}\t\t{convert_bytes(obj_size)}")


def display_cg_problems(comp_id):
    cloud_guard = CloudGuardDetails()
    cg_problems = cloud_guard.cloud_guard_problems(comp_id)
    if cg_problems is None:
        print('\n---> No Critical Problems Detected By Cloud Guard.\n')
    else:
        display_headers()
        print('\n---> Cloud Guard Critical Problems\n')
        for problem_details in cg_problems:
            problem_name = problem_details[0]
            resource_name = problem_details[1]
            print(f"\tProblem: {problem_name}\n")
            print(f"\t\t Impacted Resource: {resource_name}\n")


def display_osms(comp_id):
    osms_client = OSMSClient()
    osms_grps  = osms_client.list_osms_managed_instance_groups(comp_id)

    if len(osms_grps) == 0:
        print('\n---> No OSMS Group Found.\n')
    else:
        display_headers()
        print('\n---> OSMS Managed Instance Groups\n\n')
        for osms_grp in osms_grps:
            display_name = osms_grp[0]
            osms_managed_instance_grp_ocid = osms_grp[1]
            os_family = osms_grp[2]
            managed_instance_count = osms_grp[3]
            print(f'\n\t{display_name} - total managed instances {managed_instance_count}')
            list_instances = osms_client.get_osms_managed_instance_grps(osms_managed_instance_grp_ocid)

            for instance in list_instances:
                print(f'\n\t\t{instance.display_name}\n')
                if os_family == "LINUX":
                    osms_updates = osms_client.list_available_updates_for_instance(instance.id)
                    for patch_update in osms_updates:
                        print(f'\t\t\t{patch_update}')
        print()


def display_fss(comp_id, ad_name):
    file_storage = FSSDetails()
    filesystems = file_storage.get_filessytems(comp_id, ad_name)
    if filesystems is None:
        print(f'\n---> No File Systems Found in {ad_name}\n')
    else:
        print('\n---> FILE SYSTEMS\n\n')
        cnt = 0
        for fs_name, fs_id in filesystems.items():
            cnt += 1
            snapshots = file_storage.get_snapshots(fs_id)                               # get snapshot of filesystem
            latest_snaphot = snapshots[0]
            formatted_fss_data = str(cnt)+ '.) ' + fs_name 
            print(formatted_fss_data)
            print(f'\t\tLast Snapshot: {latest_snaphot}\n')


def display_announcements(comp_id):
    oracle_announcement = OracleAnnouncments()
    announcements = oracle_announcement.list_oracle_announcement(comp_id)
    if announcements is None:
        print('\n---> No Latest Announcements for this compartments Available.\n')
    else:
        print('\n---> Latest Oracle Announcements for the Compartment\n\n')
        latest_announcement(announcements)


def display_db_systems(comp_id):
    db_systems_details = DBSystemDetails()
    dbsys = db_systems_details.list_dbsystems(comp_id)

    if dbsys is None:
        print('\n---> No DB System Found.\n')
    else:
        display_headers()
        print('\n---> DB Systems\n\n')
        for db_sys_id, db_sys_details in dbsys.items():
            display_name = db_sys_details[0]
            db_shape = db_sys_details[1]
            database_edition = db_sys_details[2]
            hostname = db_sys_details[3]
            storage_type = db_sys_details[4]
            db_ver = db_sys_details[5]
            print("\t{}\n".format(display_name))
            print("\t\t{0:>20}: {1:<30}".format('Shape', db_shape))
            print("\t\t{0:>20}: {1:<30}".format('Database Edition', database_edition))
            print("\t\t{0:>20}: {1:<30}".format('Hostname', hostname))
            print("\t\t{0:>20}: {1:<30}".format('Storage Type', storage_type))
            print("\t\t{0:>20}: {1:<30}\n".format('DB Version', db_ver))


def display_load_balancers(comp_id):
    lb_details = LoadBalancerDetails()
    lbs = lb_details.list_lbs(comp_id)

    if lbs is None:
        print('\n---> No Load Balancers Found.\n')
    else:
        display_headers()
        print('\n---> Load Balancers\n')
        for lb in lbs:
            display_name = lb[0]
            shape_name = lb[1]
            lb_ips = lb[2]
            lb_hostnames = lb[3] 
            backend_sets = lb[4]

            print(f"\t{display_name}\n")
            print("{0:>30}: {1:<30}".format('Shape Name', shape_name))
            print("{0:>30}: {1:<30}".format('IP Addresses', lb_ips))
            print("{0:>30}: {1:<30}".format('Hostnames', lb_hostnames))

            for backend_set_name, backend_set_details in backend_sets.items():
                print("{0:>30}: {1:<30}".format('Backend Set', backend_set_name))
                print("{0:>30}:".format('Backends'))
                for backends in backend_set_details.backends:
                    print("\t\t\t\t", backends.name)
                print()


def display_ipsec_tunnels(comp_id, phase_details = False):
    vpn_details = VPNDetails()
    ipsecs = vpn_details.list_ipsecs(comp_id)

    if ipsecs is None:
        print('\n---> No IPSecs (CPEs) Found.\n')
    else:
        display_headers()
        print('\n---> IPSecs Connections \n\n')
        for ipsec in ipsecs:
            cpe_local_identifier = ipsec[0]
            cpe_local_identifier_type = ipsec[1]
            display_name = ipsec[2]
            ocid = ipsec[3]
            static_routes = ipsec[4]

            print(f"\t=> {display_name}\n")
            print("\t{0:>30}: {1:<30}".format('CPE Identifier', cpe_local_identifier))
            print("\t{0:>30}: {1:<30}".format('CPE Identifier Type', cpe_local_identifier_type))
            print("\t{0:>30}: {1:<30}".format('Static Routes', str(static_routes)))

            tunnels = vpn_details.list_tunnels(ocid)
            if tunnels is None:
                print("\t{0:>30}: {1:<30}\n".format('Associated Tunnels', '0'))
            else:
                print("\t{0:>30}: \n".format('Associated Tunnels'))
                cnt = 0
                for tunnel in tunnels:
                    cnt += 1
                    display_name = tunnel[0] 
                    dpd_mode = tunnel[1]
                    dpd_timeout_in_sec = tunnel[2]
                    encryption_domain_config = tunnel[3]
                    ike_version = tunnel[4]
                    oracle_can_initiate = tunnel[5]
                    phase_one_details = tunnel[6]
                    phase_two_details = tunnel[7]
                    routing = tunnel[8]
                    status = tunnel[9]
                    time_status_updated = tunnel[10]
                    vpn_ip = tunnel[11]

                    print(f"\t\t\t{cnt}) {display_name} - {status}\n")
                    print("\t\t\t{0:>30}: {1:<30}".format('VPN IP', vpn_ip))
                    print("\t\t\t{0:>30}: {1:<30}".format('Tunnel Status Last Update', str(time_status_updated)))
                    print("\t\t\t{0:>30}: {1:<30}".format('DPD Mode', dpd_mode))
                    print("\t\t\t{0:>30}: {1:<30}".format('DPD Timeout In Sec', dpd_timeout_in_sec))
                    print("\t\t\t{0:>30}: {1:<30}".format('IKE Version', ike_version))
                    print("\t\t\t{0:>30}: {1:<30}".format('Oracle Can Initiate', oracle_can_initiate))
                    print("\t\t\t{0:>30}: {1:<30}".format('Routing', routing))

                    if encryption_domain_config is None:
                        continue
                    oracle_traffic_selector = encryption_domain_config.oracle_traffic_selector
                    cpe_traffic_selector = encryption_domain_config.cpe_traffic_selector
                    print("\t\t\t{0:>30}:".format('Encryption Domain Config'))
                    print("\t\t\t\t\t{0:>50}: {1:<30}".format('Oracle Traffic Selector', str(oracle_traffic_selector)))
                    print("\t\t\t\t\t{0:>50}: {1:<30}".format('CPE Traffic Selector', str(cpe_traffic_selector)))
                    if phase_details:
                        if phase_one_details is not None:
                            custom_authentication_algorithm = phase_one_details.custom_authentication_algorithm
                            custom_dh_group = phase_one_details.custom_dh_group
                            custom_encryption_algorithm = phase_one_details.custom_encryption_algorithm
                            is_custom_phase_one_config = phase_one_details.is_custom_phase_one_config
                            is_ike_established = phase_one_details.is_ike_established
                            lifetime = phase_one_details.lifetime
                            negotiated_authentication_algorithm = phase_one_details.negotiated_authentication_algorithm
                            negotiated_dh_group = phase_one_details.negotiated_dh_group
                            negotiated_encryption_algorithm = phase_one_details.negotiated_encryption_algorithm
                            print("\t\t\t{0:>30}:".format('Phase One Details'))
                            print("\t\t\t\t\t{0:>50}: {1:<30}".format('Custom Authentication Algorithm', str(custom_authentication_algorithm)))
                            print("\t\t\t\t\t{0:>50}: {1:<30}".format('custom_dh_group', str(custom_dh_group)))
                            print("\t\t\t\t\t{0:>50}: {1:<30}".format('custom_encryption_algorithm', str(custom_encryption_algorithm)))
                            print("\t\t\t\t\t{0:>50}: {1:<30}".format('is_custom_phase_one_config', str(is_custom_phase_one_config)))
                            print("\t\t\t\t\t{0:>50}: {1:<30}".format('is_ike_established', str(is_ike_established)))
                            print("\t\t\t\t\t{0:>50}: {1:<30}".format('lifetime', str(lifetime)))
                            print("\t\t\t\t\t{0:>50}: {1:<30}".format('negotiated_authentication_algorithm', str(negotiated_authentication_algorithm)))
                            print("\t\t\t\t\t{0:>50}: {1:<30}".format('negotiated_dh_group', str(negotiated_dh_group)))
                            print("\t\t\t\t\t{0:>50}: {1:<30}".format('negotiated_encryption_algorithm', str(negotiated_encryption_algorithm)))

                        if phase_two_details is not None:
                            custom_authentication_algorithm = phase_two_details.custom_authentication_algorithm
                            dh_group = phase_two_details.dh_group
                            custom_encryption_algorithm = phase_two_details.custom_encryption_algorithm
                            is_custom_phase_two_config = phase_two_details.is_custom_phase_two_config
                            is_esp_established = phase_two_details.is_esp_established
                            lifetime = phase_two_details.lifetime
                            is_pfs_enabled = phase_two_details.is_pfs_enabled
                            negotiated_authentication_algorithm = phase_two_details.negotiated_authentication_algorithm
                            negotiated_dh_group = phase_two_details.negotiated_dh_group
                            negotiated_encryption_algorithm = phase_two_details.negotiated_encryption_algorithm
                            print("\t\t\t{0:>30}:".format('Phase Two Details'))
                            print("\t\t\t\t\t{0:>50}: {1:<30}".format('Custom Authentication Algorithm', str(custom_authentication_algorithm)))
                            print("\t\t\t\t\t{0:>50}: {1:<30}".format('custom_dh_group', str(dh_group)))
                            print("\t\t\t\t\t{0:>50}: {1:<30}".format('custom_encryption_algorithm', str(custom_encryption_algorithm)))
                            print("\t\t\t\t\t{0:>50}: {1:<30}".format('is_custom_phase_two_config', str(is_custom_phase_two_config)))
                            print("\t\t\t\t\t{0:>50}: {1:<30}".format('is_esp_established', str(is_esp_established)))
                            print("\t\t\t\t\t{0:>50}: {1:<30}".format('is_pfs_enabled', str(is_pfs_enabled)))
                            print("\t\t\t\t\t{0:>50}: {1:<30}".format('lifetime', str(lifetime)))
                            print("\t\t\t\t\t{0:>50}: {1:<30}".format('negotiated_authentication_algorithm', str(negotiated_authentication_algorithm)))
                            print("\t\t\t\t\t{0:>50}: {1:<30}".format('negotiated_dh_group', str(negotiated_dh_group)))
                            print("\t\t\t\t\t{0:>50}: {1:<30}\n".format('negotiated_encryption_algorithm', str(negotiated_encryption_algorithm)))
                    print()


def display_instances(comp_id, show_utilzation = False):
    instance_details = InstanceDetails()
    compute_instances = instance_details.list_all_compartments(comp_id)

    if compute_instances is None:
        print('\n---> No Compute Instances Found.\n')
    else:
        display_headers()
        print('\n---> Compute Instances\n')
        for ins in compute_instances:
            instance_id = ins[0]
            display_name = ins[1]
            lifecycle_state = ins[2]
            shape = ins[3]
            last_24_utilization = ''
            txt = f"\n\t{display_name}\t\t{lifecycle_state}\t\t{shape}"
            print(txt)
            if show_utilzation:
                if lifecycle_state == 'STOPPED':
                    pass
                else:
                    time.sleep(5)
                    last_utilz = instance_details.instance_utilization(comp_id, instance_id)
                    if is_empty(last_utilz):
                        continue
                    print("\tLast 24 hrs CPU Utilizations")
                    for utlization in last_utilz[0].aggregated_datapoints:
                        # aggregated_datapoints
                        cpu_util = int(utlization.value)
                        ts = utlization.timestamp
                        print(f'\t\t{cpu_util}%\t{ts}')
        print()

