# Copyright 2012 NEC Corporation.  All rights reserved.
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

from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from networking_nec.plugins.openflow import ofc_driver_base


LOG = logging.getLogger(__name__)


class StubOFCDriver(ofc_driver_base.OFCDriverBase):
    """Stub OFC driver for testing.

    This driver can be used not only for unit tests but also for real testing
    as a logging driver. It stores the created resources on OFC and returns
    them in get methods().

    If autocheck is enabled, it checks whether the specified resource exists
    in OFC and raises an exception if it is different from expected status.
    """

    def __init__(self, conf):
        self.autocheck = False
        self.reset_all()

    def reset_all(self):
        self.ofc_tenant_dict = {}
        self.ofc_network_dict = {}
        self.ofc_port_dict = {}

    def enable_autocheck(self):
        self.autocheck = True

    def disable_autocheck(self):
        self.autocheck = False

    @log_helpers.log_method_call
    def create_tenant(self, description, tenant_id=None):
        ofc_id = "ofc-" + tenant_id[:-4]
        if self.autocheck:
            if ofc_id in self.ofc_tenant_dict:
                raise Exception(_('(create_tenant) OFC tenant %s '
                                  'already exists') % ofc_id)
        self.ofc_tenant_dict[ofc_id] = {'tenant_id': tenant_id,
                                        'description': description}
        return ofc_id

    @log_helpers.log_method_call
    def delete_tenant(self, ofc_tenant_id):
        if ofc_tenant_id in self.ofc_tenant_dict:
            del self.ofc_tenant_dict[ofc_tenant_id]
        else:
            if self.autocheck:
                raise Exception(_('(delete_tenant) OFC tenant %s not found')
                                % ofc_tenant_id)
        LOG.debug('delete_tenant: SUCCEED')

    @log_helpers.log_method_call
    def create_network(self, ofc_tenant_id, description, network_id=None):
        ofc_id = "ofc-" + network_id[:-4]
        if self.autocheck:
            if ofc_tenant_id not in self.ofc_tenant_dict:
                raise Exception(_('(create_network) OFC tenant %s not found')
                                % ofc_tenant_id)
            if ofc_id in self.ofc_network_dict:
                raise Exception(_('(create_network) OFC network %s '
                                  'already exists') % ofc_id)
        self.ofc_network_dict[ofc_id] = {'tenant_id': ofc_tenant_id,
                                         'network_id': network_id,
                                         'description': description}
        return ofc_id

    @log_helpers.log_method_call
    def update_network(self, ofc_network_id, description):
        if self.autocheck:
            if ofc_network_id not in self.ofc_network_dict:
                raise Exception(_('(update_network) OFC network %s not found')
                                % ofc_network_id)
        data = {'description': description}
        self.ofc_network_dict[ofc_network_id].update(data)
        LOG.debug('update_network: SUCCEED')

    @log_helpers.log_method_call
    def delete_network(self, ofc_network_id):
        if ofc_network_id in self.ofc_network_dict:
            del self.ofc_network_dict[ofc_network_id]
        else:
            if self.autocheck:
                raise Exception(_('(delete_network) OFC network %s not found')
                                % ofc_network_id)
        LOG.debug('delete_network: SUCCEED')

    @log_helpers.log_method_call
    def create_port(self, ofc_network_id, info, port_id=None):
        ofc_id = "ofc-" + port_id[:-4]
        if self.autocheck:
            if ofc_network_id not in self.ofc_network_dict:
                raise Exception(_('(create_port) OFC network %s not found')
                                % ofc_network_id)
            if ofc_id in self.ofc_port_dict:
                raise Exception(_('(create_port) OFC port %s already exists')
                                % ofc_id)
        self.ofc_port_dict[ofc_id] = {'network_id': ofc_network_id,
                                      'port_id': port_id}
        return ofc_id

    @log_helpers.log_method_call
    def delete_port(self, ofc_port_id):
        if ofc_port_id in self.ofc_port_dict:
            del self.ofc_port_dict[ofc_port_id]
        else:
            if self.autocheck:
                raise Exception(_('(delete_port) OFC port %s not found')
                                % ofc_port_id)
        LOG.debug('delete_port: SUCCEED')

    def convert_ofc_tenant_id(self, context, ofc_tenant_id):
        return ofc_tenant_id

    def convert_ofc_network_id(self, context, ofc_network_id, tenant_id):
        return ofc_network_id

    def convert_ofc_port_id(self, context, ofc_port_id, tenant_id, network_id):
        return ofc_port_id
