# from MI_OCI import *
# Tenancy Details
tenancy_details = IdentityClientInfo()

# Compartments
compartments = tenancy_details.get_compartments(tenancy_id)
compartments['Root'] = tenancy_id

# Avalability Domains
ads = tenancy_details.get_availability_domains(tenancy_id)

for comp_name, comp_id in compartments.items():
    display_headers()
    print("#{0:^198}#".format(comp_name))
    display_headers()

    # Get Oracle Announcements
    display_announcements(comp_id)
    for ad_name, ad_ocid in ads.items():
        # File Storage Details
        display_fss(comp_id, ad_name)        

    # Object Storage Details
    namespace = ''                                              # set namespace
    object_name_to_display = ''
    display_object_storage(namespace, comp_id, object_name_to_display)

    # Get Cloud Guard Critical Problems
    display_cg_problems(comp_id)        

    # OSMS Details
    display_osms(comp_id)

    # Get DB Systems
    display_db_systems(comp_id)

    # Get Load Balancers
    display_load_balancers(comp_id)
