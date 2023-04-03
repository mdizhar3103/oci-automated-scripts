# from MI_OCI import *
# Tenancy Details
tenancy_details = IdentityClientInfo()

# Compartments
compartments = tenancy_details.get_compartments(tenancy_id)
compartments['Root'] = tenancy_id

# Avalability Domains
ads = tenancy_details.get_availability_domains(tenancy_id)

parser = argparse.ArgumentParser()
parser.add_argument("-dall", "--display_all", help="Display All Operational Resources", action="store_true")
parser.add_argument("-doan", "--display_oracle_anc", help="Display Oracle Announcements", action="store_true")
parser.add_argument("-dfss", "--display_filesystems", help="Display Oracle File System Services", action="store_true")
parser.add_argument("-dobj", "--display_object_storage", help="Display Oracle Object Storage", action="store_true")
parser.add_argument("-dcg", "--display_cg_cr_prbs", help="Display Oracle Cloud Guard Critical Problems", action="store_true")
parser.add_argument("-dosms", "--display_osms", help="Display OSMS", action="store_true")
parser.add_argument("-ddbsys", "--display_db_systems", help="Display DB Systems", action="store_true")
parser.add_argument("-dlbs", "--display_lbs", help="Display Load Balancers", action="store_true")
parser.add_argument("-dvpns", "--display_vpns", help="Display IPSec Tunnels", action="store_true")
parser.add_argument("--show_phases", help="Display IPSec Tunnels phase details", action="store_true")
parser.add_argument("-dins", "--display_instances", help="Display Compute Instances", action="store_true")
parser.add_argument("--show_util", help="Show last 24 hours utlization of server", action="store_true")

args = parser.parse_args()

for comp_name, comp_id in compartments.items():
    display_headers()
    print("#{0:^198}#".format(comp_name))
    display_headers()

    if args.display_oracle_anc or args.display_all:
        display_announcements(comp_id)                      # Get Oracle Announcements


    if args.display_filesystems or args.display_all:
        for ad_name, ad_ocid in ads.items():
            # File Storage Details
            display_fss(comp_id, ad_name)        


    if args.display_object_storage or args.display_all:                         # Object Storage Details
        namespace = ''                                                          # set namespace
        object_name_to_display = ''
        display_object_storage(namespace, comp_id, object_name_to_display)


    if args.display_cg_cr_prbs or args.display_all:
        display_cg_problems(comp_id)                                            # Get Cloud Guard Critical Problems


    if args.display_osms or args.display_all:
        display_osms(comp_id)                                                   # Get OSMS Details


    if args.display_db_systems or args.display_all:
        display_db_systems(comp_id)                                             # Get DB Systems


    if args.display_lbs or args.display_all:
        display_load_balancers(comp_id)                                         # Get Load Balancers


    if (args.display_vpns or args.display_all) and not args.show_phases:
        display_ipsec_tunnels(comp_id, phase_details= False)                    # Get Ipsec Tunnels
    elif (args.display_vpns or args.display_all) and args.show_phases:
        display_ipsec_tunnels(comp_id, phase_details= True)
    elif (not args.display_vpns or args.display_all) and args.show_phases:
        raise SyntaxError('show_phases must be used with display_vpns option')


    if (args.display_instances or args.display_all) and not args.show_util:
        display_instances(comp_id, show_utilzation=False)                       # Get Instances
    elif (args.display_instances or args.display_all) and args.show_util:
        display_instances(comp_id, show_utilzation=True)
    elif (not args.display_instances or args.display_all) and args.show_util:
        raise SyntaxError('show_util must be used with display_instances option')
