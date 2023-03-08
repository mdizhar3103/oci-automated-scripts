#!/usr/bin/env python3

#
# Copyright (c) 2019, 2020 Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at
#  http://oss.oracle.com/licenses/upl
#

import os
import sys
import oci
import time
import logging
import logging.handlers

from argparse import ArgumentParser, ArgumentError, Namespace, SUPPRESS
from oci.os_management import OsManagementClient
from oci.identity import IdentityClient

PROGRAM_NAME = os.path.basename(sys.argv[0]).replace('.py', '')
PROGRAM_VERSION = '0.1.0'


def setup_logger(enable_logfile=False, verbose=False, debug=False):
    class LevelsFilter(logging.Filter):
        def __init__(self, levels, name=''):
            logging.Filter.__init__(self, name)
            self.levels = levels

        def filter(self, record):
            if record.levelno in self.levels:
                return True
            return False

    flat_formatter = logging.Formatter('{message}', style='{')
    level_formatter = logging.Formatter('{levelname:8s}: {message}', style='{')
    log_file_handler = None
    if enable_logfile or debug:
        try:
            formatter = logging.Formatter('{asctime} - {name} - {levelname}({module}:{lineno}) - {message}', style='{')
            log_file_handler = logging.handlers.RotatingFileHandler('{0}.log'.format(PROGRAM_NAME),
                                                                    mode='a',
                                                                    maxBytes=1024 * 1024,
                                                                    backupCount=3)
            log_file_handler.setFormatter(formatter)
            log_file_handler.setLevel(logging.NOTSET)
        except IOError:
            pass

    logger = logging.getLogger(PROGRAM_NAME)
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setFormatter(flat_formatter)
    logger.setLevel(logging.ERROR)
    if verbose:
        stdout_handler.addFilter(LevelsFilter([logging.INFO]))
        logger.setLevel(logging.INFO)
    if debug:
        log_file_handler.setFormatter(level_formatter)
        log_file_handler.addFilter(LevelsFilter([logging.DEBUG,
                                                 logging.INFO,
                                                 logging.WARNING,
                                                 logging.ERROR,
                                                 logging.CRITICAL]))
        logger.setLevel(logging.DEBUG)
    stderr_handler = logging.StreamHandler(stream=sys.stderr)
    stderr_handler.setFormatter(level_formatter)
    stderr_handler.addFilter(LevelsFilter([logging.WARNING, logging.ERROR, logging.CRITICAL]))
    if log_file_handler is not None:
        logger.addHandler(log_file_handler)
    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)
    return logger


class OCIClients(object):
    def __init__(self, options):
        self.compartment_id = options.compartment_id
        if options.use_instance_principles:
            config = {}
            if options.region is not None:
                config['region'] = options.region
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            if self.compartment_id is None:
                self.compartment_id = signer.tenancy_id
            self.osms_client = OsManagementClient(config,
                                                  timeout=(10, 600),
                                                  retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,
                                                  signer=signer)
            self.iam_client = IdentityClient(config,
                                             timeout=(10, 600),
                                             retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,
                                             signer=signer)
        else:
            config = oci.config.from_file(file_location=options.config_file, profile_name=options.config_profile)
            if options.region is not None:
                config['region'] = options.region
            if self.compartment_id is None:
                self.compartment_id = config.get('tenancy')
            else:
                config['compartment'] = self.compartment_id
            self.osms_client = OsManagementClient(config,
                                                  timeout=(10, 600),
                                                  retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
            self.iam_client = IdentityClient(config,
                                             timeout=(10, 600),
                                             retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)

    def get_osms_client(self):
        return self.osms_client

    def get_iam_client(self):
        return self.iam_client


class Data(object):
    def __init__(self):
        self.managed_instance_group_id = None
        self.total_instances = 0
        self.vulnerable_instances = []

    def show_overview(self):
        print()
        print('        Patch Compliance Report Sample')
        print('        ==============================')
        print()
        if self.managed_instance_group_id is not None:
            print('Managed Instance Group ID: {0}'.format(self.managed_instance_group_id))
        vulnerable_instances = len(self.vulnerable_instances) if len(self.vulnerable_instances) > 0 else 'None'
        linking_verb = 'are' if len(self.vulnerable_instances) > 1 else 'is'
        plural = 's' if self.total_instances > 1 else ''
        print('\nDetected out of {0} managed instance{1}, {2} {3} '
              'missing security patches!\n'.format(self.total_instances, plural, vulnerable_instances, linking_verb))

    def show_details(self):
        for instance in self.vulnerable_instances:
            print('Managed Instance {0} ({1})'.format(instance.get('display_name'), instance.get('id')))
            print(' has the following outstanding security patches:')
            for update in instance.get('security_updates', []):
                print('  {0}'.format(update.get('display_name')))
                if update.get('related_cves', None) is not None:
                    print('      CVEs:', end='')
                    num_cve = 0
                    num_cves = len(update.get('related_cves', []))
                    cve_line = ''
                    for cve in update.get('related_cves', []):
                        num_cve += 1
                        cve_line = '{0} {1:<17}'.format(cve_line, cve + ',')
                        if len(cve_line) >= 65:
                            if num_cve < num_cves:
                                print(cve_line.rstrip(' '))
                                print('           ', end='')
                            else:
                                print(cve_line.rstrip(', '))
                            cve_line = ''
                    if cve_line != '':
                        print(cve_line.rstrip(', '))
            print()


def find_all_compartments(iam_client, compartment_id):
    LOGGER.info('Find sub compartments')
    compartment_ids = [compartment_id]
    if compartment_id.startswith('ocid1.tenancy.'):
        c_response = iam_client.list_compartments(compartment_id, compartment_id_in_subtree=True)
        compartment_ids.extend([c.id for c in c_response.data
                                if c.lifecycle_state == 'ACTIVE' and c.name != 'ManagedCompartmentForPaaS'])
    else:
        compartment_ids.extend(list_compartments(iam_client, compartment_ids))
    return compartment_ids


def list_compartments(iam_client, compartments):
    if compartments is None:
        return []
    sub_compartments = []
    for compartment in compartments:
        LOGGER.debug('List Compartment: {0}'.format(compartment))
        c_response = iam_client.list_compartments(compartment)
        sub_compartments.extend([c.id for c in c_response.data
                                 if c.lifecycle_state == 'ACTIVE' and c.name != 'ManagedCompartmentForPaaS'])
        sub_names = [c.name for c in c_response.data
                     if c.lifecycle_state == 'ACTIVE' and c.name != 'ManagedCompartmentForPaaS']
        LOGGER.debug('Sub Compartments: {0}'.format(sub_names))
        sub_compartments.extend(list_compartments(iam_client, sub_compartments))
    return sub_compartments


def query_managed_instance_group(osms_client, managed_instance_group_id):
    LOGGER.info('Retrieving Managed Instance Group ({0}) info'.format(managed_instance_group_id))
    mig_response = osms_client.get_managed_instance_group(managed_instance_group_id)
    total_instances, vuln_instances = query_managed_instances(osms_client, mig_response.data.managed_instances)
    return total_instances, vuln_instances


def query_compartment(osms_client, compartment_id):
    LOGGER.info('Retrieving Managed Instance list from compartment "{0}"'.format(compartment_id))
    request_options = {'limit':      10,
                       'sort_by':    'TIMECREATED',
                       'sort_order': 'ASC',
                       }
    managed_instances = []
    next_page = None
    has_next_page = True
    while has_next_page:
        if next_page is not None:
            request_options['page'] = next_page
        elif request_options.get('page', False):
            request_options.pop('page')
        try:
            mil_response = osms_client.list_managed_instances(compartment_id)  # , **request_options)
        except oci.exceptions.ServiceError as service_error:
            LOGGER.info('Service Exception "{0}")'.format(service_error.code))
            LOGGER.debug('OCI Request ID: "{0}"'.format(service_error.request_id))
            raise
        if mil_response is None:
            raise RuntimeError('Unable to retrieve updates from compartment {0}'.format(compartment_id))
        has_next_page = mil_response.has_next_page
        next_page = mil_response.next_page
        managed_instances.extend(mil_response.data)
    total_instances, vuln_instances = query_managed_instances(osms_client, managed_instances)
    return total_instances, vuln_instances


def query_managed_instances(osms_client, managed_instances):
    vuln_instances = []
    total_instances = len(managed_instances)
    for mi in managed_instances:
        LOGGER.info('Retrieving Managed Instance "{0}" info'.format(mi.display_name))
        mi_response = osms_client.get_managed_instance(mi.id)
        mi_data = mi_response.data
        LOGGER.debug('Managed Instance: {0}'.format(mi_data))
        linux_mi = mi_data.os_family == 'LINUX'
        available_security_updates = 0
        security_updates = []
        updates = None
        if mi_data.updates_available > 0:
            LOGGER.info('Retrieving Update info for Managed Instance "{0}"'.format(mi.display_name))
            request_options = {'limit':      10,
                               'sort_by':    'TIMECREATED',
                               'sort_order': 'ASC',
                               }
            next_page = None
            has_next_page = True
            while has_next_page:
                if next_page is not None:
                    request_options['page'] = next_page
                elif request_options.get('page', False):
                    request_options.pop('page')
                try:
                    if linux_mi:
                        updates = osms_client.list_available_updates_for_managed_instance(mi.id, **request_options)
                    else:
                        updates = osms_client.list_available_windows_updates_for_managed_instance(mi.id,
                                                                                                  **request_options)
                except oci.exceptions.ServiceError as service_error:
                    LOGGER.info('Service Exception "{0}")'.format(service_error.code))
                    LOGGER.debug('OCI Request ID: "{0}"'.format(service_error.request_id))
                if updates is None:
                    raise RuntimeError('Unable to retrieve updates from {0}'.format(mi.display_name))
                has_next_page = updates.has_next_page
                next_page = updates.next_page
                for update in updates.data:
                    LOGGER.debug('Update: {0}'.format(update))
                    if update.update_type == 'SECURITY':
                        available_security_updates += 1
                        if linux_mi:
                            security_updates.append({'display_name': update.display_name,
                                                     'related_cves': update.related_cves})
                        else:
                            security_updates.append({'display_name': update.display_name})
            if available_security_updates > 0:
                managed_instance = {
                        'compartment_id':             mi_data.compartment_id,
                        'display_name':               mi_data.display_name,
                        'id':                         mi_data.id,
                        'is_reboot_required':         mi_data.is_reboot_required,
                        'last_boot':                  mi_data.last_boot,
                        'last_checkin':               mi_data.last_checkin,
                        'managed_instance_groups':    mi_data.managed_instance_groups,
                        'os_family':                  mi_data.os_family,
                        'os_kernel_version':          mi_data.os_kernel_version,
                        'os_name':                    mi_data.os_name,
                        'os_version':                 mi_data.os_version,
                        'status':                     mi_data.status,
                        'updates_available':          mi_data.updates_available,
                        'security_updates_available': available_security_updates,
                        'security_updates':           security_updates
                }
                vuln_instances.append(managed_instance)
    return total_instances, vuln_instances


def main(argv=None):
    if argv is None:
        argv = sys.argv
    program_version_message = '{0} {1}'.format(PROGRAM_NAME, PROGRAM_VERSION)
    program_description = 'OS Management Reporting'
    options = Namespace()
    try:
        the_parser = ArgumentParser(description=program_description)
        select_grp = the_parser.add_mutually_exclusive_group()
        authop_grp = the_parser.add_mutually_exclusive_group()
        the_parser.add_argument('--compartment-ocid', '-c',
                                dest='compartment_id',
                                action='store',
                                default=None,
                                required=True,
                                help="Compartment to run query against, defaults to the root compartment")
        the_parser.add_argument('--region', '-r',
                                dest='region',
                                action='store',
                                default=None,
                                required=False,
                                help="Region to run query against")
        authop_grp.add_argument('--use-instance-principles', '-I',
                                dest='use_instance_principles',
                                action='store_true',
                                default=False,
                                required=False,
                                help="Authenticate using Instance Principles")
        select_grp.add_argument('--managed-instance-group-ocid', '-g',
                                dest='managed_instance_group_id',
                                action='store',
                                default=None,
                                required=False,
                                help="Managed Instance Group to query")
        authop_grp.add_argument('--oci-config', '-C',
                                dest='config_file',
                                action='store',
                                default=os.path.join('~', '.oci', 'config'),
                                required=False,
                                help="Oracle Cloud Infrastructure config file")
        the_parser.add_argument('--oci-config-profile', '-P',
                                dest='config_profile',
                                action='store',
                                default='DEFAULT',
                                required=False,
                                help="Oracle Cloud Infrastructure config profile to use")
        the_parser.add_argument('--show-details', '-d',
                                dest='show_details',
                                action='store_true',
                                default=False,
                                required=False,
                                help='Show detailed report')
        select_grp.add_argument('--recursive', '-R',
                                dest='scan_sub_compartments',
                                action='store_true',
                                default=False,
                                required=False,
                                help='Recursively scan sub-compartments')
        the_parser.add_argument('--verbose', '-v',
                                dest='verbose',
                                action='store_true',
                                default=False,
                                required=False,
                                help='Enable verbose mode')
        the_parser.add_argument("--version",
                                action="version",
                                version=program_version_message)
        the_parser.add_argument("--debug",
                                dest='debug_enabled',
                                action='store_true',
                                default=False,
                                required=False,
                                help=SUPPRESS)
        the_parser.parse_args(args=argv[1:], namespace=options)
    except ArgumentError:
        return 1
    # noinspection PyGlobalUndefined
    global LOGGER
    LOGGER = setup_logger(verbose=options.verbose, debug=options.debug_enabled)
    oci_clients = OCIClients(options)
    data = Data()
    if options.managed_instance_group_id is not None:
        total_instances, vulnerable_instances = query_managed_instance_group(oci_clients.osms_client,
                                                                             options.managed_instance_group_id)
        data.total_instances += total_instances
        data.vulnerable_instances.extend(vulnerable_instances)
        data.managed_instance_group_id = options.managed_instance_group_id
        LOGGER.debug('MIG Query: Total Instances {0}, Vulnerable Instances {1}'.format(total_instances,
                                                                                       vulnerable_instances))
    else:
        compartment_ids = [options.compartment_id]
        if options.scan_sub_compartments:
            compartment_ids = find_all_compartments(oci_clients.iam_client, options.compartment_id)
        for compartment_id in compartment_ids:
            total_instances, vulnerable_instances = query_compartment(oci_clients.osms_client, compartment_id)
            data.total_instances += total_instances
            data.vulnerable_instances.extend(vulnerable_instances)
            LOGGER.debug('Compartment ({0}) Instances: Total {1}, Vulnerable {2}'.format(compartment_id,
                                                                                         total_instances,
                                                                                         len(vulnerable_instances)))
    data.show_overview()
    if options.show_details:
        data.show_details()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('\n{0}: Cancelled by user'.format(PROGRAM_NAME))
        sys.exit(127)
