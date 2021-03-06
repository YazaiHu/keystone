#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Keystone Identity Server - CLI Management Interface
"""

import datetime
import logging
import optparse
import sys

import tools.tracer  # @UnusedImport # module runs on import
import keystone
from keystone.common import config
import keystone.backends as db
import keystone.backends.api as db_api
import keystone.backends.models as db_models


class RaisingOptionParser(optparse.OptionParser):
    def error(self, msg):
        self.print_usage(sys.stderr)
        raise optparse.OptParseError(msg)


def parse_args(args=None):
    usage = "usage: %prog [options] type command [id [attributes]]"

    # Initialize a parser for our configuration paramaters
    parser = RaisingOptionParser(usage, version='%%prog %s'
                                   % keystone.version())
    _common_group = config.add_common_options(parser)
    config.add_log_options(parser)

    # Parse command-line and load config
    (options, args) = config.parse_options(parser, args)
    _config_file, conf = config.load_paste_config('admin', options, args)

    # Set things up to run the command
    debug = options.get('debug') or conf.get('debug', False)
    debug = debug in [True, "True", "1"]
    verbose = options.get('verbose') or conf.get('verbose', False)
    verbose = verbose in [True, "True", "1"]
    if debug or verbose:
        _config_file = config.find_config_file(options, args)

    config.setup_logging(options, conf)

    db.configure_backends(conf.global_conf)

    return args


def process(*args):
    """
    Usage: keystone-manage [options] type command [id [attributes]]
      type       : role, tenant, user, token, endpoint, endpointTemplates
      command    : add, list, disable, delete, grant, revoke
      id         : name or id
      attributes : depending on type...
        users    : password, tenant
        tokens   : user, tenant, expiration

      role list [tenant] will list roles granted on that tenant

    options
      -c | --config-file : config file to use
      -d | --debug : debug mode

    Example: keystone-manage user add Admin P@ssw0rd
    """
    # Check arguments
    if len(args) == 0:
        raise optparse.OptParseError(
            'No object type specified for first argument')

    object_type = args[0]
    if object_type not in ['user', 'tenant', 'role', 'service',
            'endpointTemplates', 'token', 'endpoint', 'credentials']:
        raise optparse.OptParseError(
            '%s is not a supported object type' % object_type)

    if len(args) == 1:
        raise optparse.OptParseError(
            'No command specified for second argument')
    command = args[1]
    if command not in ['add', 'list', 'disable', 'delete', 'grant', 'revoke']:
        raise optparse.OptParseError('add, disable, delete, and list are the '
            'only supported commands (right now)')

    if len(args) == 2:
        if command != 'list':
            raise optparse.OptParseError('No id specified for third argument')
    if len(args) > 2:
        object_id = args[2]

    if object_type == "user":
        if command == "add":
            if len(args) < 4:
                raise optparse.OptParseError(
                    'No password specified for fourth argument')
            password = args[3]

            try:
                object = db_models.User()
                object.id = object_id
                object.password = password
                object.enabled = True
                if len(args) > 4:
                    tenant = args[4]
                    object.tenant_id = tenant
                db_api.USER.create(object)
                print "SUCCESS: User %s created." % object.id
            except:
                raise Exception("Failed to create user %s" % (object_id,),
                    sys.exc_info())
            return
        elif command == "disable":
            try:
                object = db_api.USER.get(object_id)
                if object == None:
                    raise IndexError("User %s not found" % object_id)
                object.enabled = False
                db_api.USER.update(object_id, object)
                print "SUCCESS: User %s disabled." % object.id
            except:
                raise Exception("Failed to disable user %s" % (object_id,),
                    sys.exc_info())
            return
        elif command == "list":
            try:
                if len(args) > 2:
                    tenant = args[2]
                    objects = db_api.USER.get_by_tenant(tenant)
                    if objects == None:
                        raise IndexError("Users not found")
                    print 'id', 'enabled'
                    print '-' * 20
                    for row in objects:
                        print row.id, row.enabled
                else:
                    objects = db_api.USER.get_all()
                    if objects == None:
                        raise IndexError("Users not found")
                    print 'id', 'enabled', 'tenant'
                    print '-' * 20
                    for row in objects:
                        print row.id, row.enabled, row.tenant_id
            except:
                raise Exception("Error getting all users", sys.exc_info())
            return
    elif object_type == "tenant":
        if command == "add":
            try:
                object = db_models.Tenant()
                object.id = object_id
                object.enabled = True
                db_api.TENANT.create(object)
                print "SUCCESS: Tenant %s created." % object.id
                return
            except:
                raise Exception("Failed to create tenant %s" % (object_id,),
                                sys.exc_info())
        elif command == "list":
            try:
                objects = db_api.TENANT.get_all()
                if objects == None:
                    raise IndexError("Tenants not found")
                print 'tenant', 'enabled'
                print '-' * 20
                for row in objects:
                    print row.id, row.enabled
            except:
                raise Exception("Error getting all tenants", sys.exc_info())
            return
        elif command == "disable":
            try:
                object = db_api.TENANT.get(object_id)
                if object == None:
                    raise IndexError("Tenant %s not found" % object_id)
                object.enabled = False
                db_api.TENANT.update(object_id, object)
                print "SUCCESS: Tenant %s disabled." % object.id
            except:
                raise Exception("Failed to disable tenant %s" % (object_id,),
                    sys.exc_info())
            return
    elif object_type == "role":
        if command == "add":
            try:
                object = db_models.Role()
                object.id = object_id
                db_api.ROLE.create(object)
                print "SUCCESS: Role %s created successfully." % object.id
                return
            except:
                raise Exception("Failed to create role %s" % (object_id,),
                    sys.exc_info())
        elif command == "list":
            if len(args) == 3:
                tenant = args[2]
                try:
                    objects = db_api.TENANT.get_role_assignments(tenant)
                    if objects == None:
                        raise IndexError("Assignments not found")
                    print 'Role assignments for tenant %s' % tenant
                    print 'User', 'Role'
                    print '-' * 20
                    for row in objects:
                        print row.user_id, row.role_id
                except:
                    raise Exception("Error getting all role assignments for %s"
                        % (tenant,), sys.exc_info())
                return
            else:
                tenant = None
                try:
                    objects = db_api.ROLE.get_all()
                    if objects == None:
                        raise IndexError("Roles not found")
                    print 'All roles'
                    print 'Role'
                    print '-' * 20
                    for row in objects:
                        print row.id
                except:
                    raise Exception("Error getting all roles", sys.exc_info())
                return
        elif command == "grant":
            if len(args) < 4:
                raise optparse.OptParseError("Missing arguments: role grant "
                    "'role' 'user' 'tenant (optional)'")
            user = args[3]
            if len(args) > 4:
                tenant = args[4]
            else:
                tenant = None
            try:
                object = db_models.UserRoleAssociation()
                object.role_id = object_id
                object.user_id = user
                if tenant != None:
                    object.tenant_id = tenant
                db_api.USER.user_role_add(object)
                print("SUCCESS: Granted %s the %s role on %s." %
                    (object.user_id, object.role_id, object.tenant_id))
            except:
                raise Exception("Failed to grant role %s to %s on %s" %
                    (object_id, user, tenant), sys.exc_info())
            return
    elif object_type == "endpointTemplates":
        if command == "add":
            if len(args) < 9:
                raise optparse.OptParseError("Missing arguments: "
                    "endpointTemplates add 'region' 'service' 'publicURL' "
                    "'adminURL' 'internalURL' 'enabled' 'global'")
            region = args[2]
            service = args[3]
            public_url = args[4]
            admin_url = args[5]
            internal_url = args[6]
            enabled = args[7]
            is_global = args[8]
            try:
                object = db_models.EndpointTemplates()
                object.region = region
                object.service = service
                object.public_url = public_url
                object.admin_url = admin_url
                object.internal_url = internal_url
                object.enabled = enabled
                object.is_global = is_global
                object = db_api.ENDPOINT_TEMPLATE.create(object)
                print("SUCCESS: Created EndpointTemplates for %s pointing "
                    "to %s." % (object.service, object.public_url))
                return
            except:
                raise Exception("Failed to create EndpointTemplates for %s" %
                    (service,), sys.exc_info())
        elif command == "list":
            if len(args) == 3:
                tenant = args[2]
                try:
                    objects = db_api.ENDPOINT_TEMPLATE.endpoint_get_by_tenant(
                        tenant)
                    if objects == None:
                        raise IndexError("URLs not found")
                    print 'Endpoints for tenant %s' % tenant
                    print 'service', 'region', 'Public URL'
                    print '-' * 30
                    for row in objects:
                        print row.service, row.region, row.public_url
                except:
                    raise Exception("Error getting all endpoints for %s" %
                        (tenant,), sys.exc_info())
                return
            else:
                tenant = None
                try:
                    objects = db_api.ENDPOINT_TEMPLATE.get_all()
                    if objects == None:
                        raise IndexError("URLs not found")
                    print 'All EndpointTemplates'
                    print 'service', 'region', 'Public URL'
                    print '-' * 20
                    for row in objects:
                        print row.service, row.region, row.public_url
                except:
                    raise Exception("Error getting all EndpointTemplates",
                        sys.exc_info())
                return
    elif object_type == "endpoint":
        if command == "add":
            if len(args) < 4:
                raise optparse.OptParseError("Missing arguments: endPoint add "
                    "tenant endPointTemplate'")

            tenant_id = args[2]
            endpoint_template_id = args[3]
            try:
                object = db_models.Endpoints()
                object.tenant_id = tenant_id
                object.endpoint_template_id = endpoint_template_id
                object = db_api.ENDPOINT_TEMPLATE.endpoint_add(object)
                print("SUCCESS: Endpoint %s added to tenant %s." %
                    (endpoint_template_id, tenant_id))
                return
            except:
                raise Exception("Failed to create Endpoint", sys.exc_info())
    elif object_type == "token":
        if command == "add":
            if len(args) < 6:
                raise optparse.OptParseError('Creating a token requires a '
                    'token id, user, tenant, and expiration')
            try:
                object = db_models.Token()
                object.id = object_id
                object.user_id = args[3]
                object.tenant_id = args[4]
                tuple_time = datetime.datetime.strptime(args[5]
                                                        .replace("-", ""),
                                                        "%Y%m%dT%H:%M")
                object.expires = tuple_time
                db_api.TOKEN.create(object)
                print "SUCCESS: Token %s created." % object.id
                return
            except:
                raise Exception("Failed to create token %s" % (object_id,),
                    sys.exc_info())
        elif command == "list":
            try:
                objects = db_api.TOKEN.get_all()
                if objects == None:
                    raise IndexError("Tokens not found")
                print 'token', 'user', 'expiration', 'tenant'
                print '-' * 20
                for row in objects:
                    print row.id, row.user_id, row.expires, row.tenant_id
            except:
                raise Exception("Error getting all tokens", sys.exc_info())
            return
        elif command == "delete":
            try:
                object = db_api.TOKEN.get(object_id)
                if object == None:
                    raise IndexError("Token %s not found" % object_id)
                else:
                    db_api.TOKEN.delete(object_id)
                    print 'SUCCESS: Token %s deleted.' % object_id
            except:
                raise Exception("Failed to delete token %s" % (object_id,),
                    sys.exc_info())
            return
    elif object_type == "service":
        if command == "add":
            try:
                object = db_models.Service()
                object.id = object_id
                db_api.SERVICE.create(object)
                print "SUCCESS: Service %s created successfully." % \
                        (object.id,)
                return
            except:
                raise Exception("Failed to create Service %s" % \
                        (object_id,), sys.exc_info())
        elif command == "list":
            try:
                objects = db_api.SERVICE.get_all()
                if objects == None:
                    raise IndexError("Services not found")
                print objects
                print 'All Services'
                print 'Service'
                print '-' * 20
                for row in objects:
                    print row.id
            except:
                raise Exception("Error getting all services", sys.exc_info())
    elif object_type == "credentials":
        if command == "add":
            if len(args) < 6:
                raise optparse.OptParseError('Creating a credentials requires '
                    'a type, key, secret, and tenant_id (id is user_id)')
            try:
                object = db_models.Token()
                object.user_id = object_id
                object.type = args[3]
                object.key = args[4]
                object.secret = args[5]
                if len(args) == 7:
                    object.tenant_id = args[6]
                result = db_api.CREDENTIALS.create(object)
                print "SUCCESS: Credentials %s created." % result.id
                return
            except:
                raise Exception("Failed to create credentials %s" %
                    (object_id,), sys.exc_info())

    # Command not handled
    print ("ERROR: %s %s not yet supported" % (object_type, command))


def main():
    try:
        process(*parse_args())
    except optparse.OptParseError as exc:
        print >> sys.stderr, exc
        sys.exit(2)
    except Exception as exc:
        try:
            info = exc.args[1]
        except IndexError:
            print "ERROR: %s" % (exc,)
            logging.error(str(exc))
        else:
            print "ERROR: %s: %s" % (exc.args[0], info)
            logging.error(exc.args[0], exc_info=info)
        sys.exit(1)

if __name__ == '__main__':
    main()
