# Copyright 2015-2016 NEC Corporation.  All rights reserved.
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

from neutron.common import constants as q_const
from neutron.db import api as db_api
from neutron.db import models_v2
from neutron import manager
from neutron.plugins.ml2 import db as db_ml2
from neutron.plugins.ml2 import models as models_ml2
from neutron.plugins.ml2 import rpc
from oslo_log import log as logging
from oslo_serialization import jsonutils
from sqlalchemy.orm import exc as sa_exc

from networking_nec._i18n import _LE, _LI
from networking_nec.plugins.necnwa.db import api as necnwa_api

LOG = logging.getLogger(__name__)


class TenantBindingServerRpcCallback(rpc.RpcCallbacks):

    RPC_VERSION = '1.0'

    def get_nwa_network_by_port_id(self, rpc_context, **kwargs):
        plugin = manager.NeutronManager.get_plugin()
        port_id = kwargs.get('port_id')
        port = plugin.get_port(rpc_context, port_id)

        network = plugin.get_network(rpc_context, port['network_id'])

        return network

    def get_nwa_network_by_subnet_id(self, rpc_context, **kwargs):
        plugin = manager.NeutronManager.get_plugin()
        subnet_id = kwargs.get('subnet_id')
        subnet = plugin.get_subnet(rpc_context, subnet_id)

        network = plugin.get_network(rpc_context, subnet['network_id'])

        return network

    def get_nwa_network(self, rpc_context, **kwargs):
        plugin = manager.NeutronManager.get_plugin()
        net_id = kwargs.get('network_id')
        network = plugin.get_network(rpc_context, net_id)

        return network

    def get_nwa_networks(self, rpc_context, **kwargs):
        plugin = manager.NeutronManager.get_plugin()
        networks = plugin.get_networks(rpc_context)

        return networks

    def get_nwa_tenant_binding(self, rpc_context, **kwargs):
        """get nwa_tenant_binding from neutorn db.

        @param rpc_context: rpc context.
        @param kwargs: tenant_id, nwa_tenant_id
        @return: success = dict of nwa_tenant_binding, error = dict of empty.
        """
        LOG.debug("context=%s, kwargs=%s" % (rpc_context, kwargs))
        tenant_id = kwargs.get('tenant_id')
        nwa_tenant_id = kwargs.get('nwa_tenant_id')

        LOG.debug("tenant_id=%s, nwa_tenant_id=%s" %
                  (tenant_id, nwa_tenant_id))
        session = db_api.get_session()
        with session.begin(subtransactions=True):
            recode = necnwa_api.get_nwa_tenant_binding(
                session, tenant_id, nwa_tenant_id
            )
            if recode is not None:
                LOG.debug(
                    "nwa_data=%s", jsonutils.dumps(
                        recode.value_json, indent=4, sort_keys=True)
                )
                return recode.value_json

        return dict()

    def add_nwa_tenant_binding(self, rpc_context, **kwargs):
        """get nwa_tenant_binding from neutorn db.

        @param rpc_context: rpc context.
        @param kwargs: tenant_id, nwa_tenant_id
        @return: dict of status
        """

        LOG.debug("context=%s, kwargs=%s" % (rpc_context, kwargs))
        tenant_id = kwargs.get('tenant_id')
        nwa_tenant_id = kwargs.get('nwa_tenant_id')
        nwa_data = kwargs.get('nwa_data')

        session = db_api.get_session()
        with session.begin(subtransactions=True):
            if necnwa_api.add_nwa_tenant_binding(
                    session,
                    tenant_id,
                    nwa_tenant_id,
                    nwa_data
            ):
                return {'status': 'SUCCESS'}

        return {'status': 'FAILED'}

    def set_nwa_tenant_binding(self, rpc_context, **kwargs):
        tenant_id = kwargs.get('tenant_id')
        nwa_tenant_id = kwargs.get('nwa_tenant_id')
        nwa_data = kwargs.get('nwa_data')
        LOG.debug("tenant_id=%s, nwa_tenant_id=%s" %
                  (tenant_id, nwa_tenant_id))
        LOG.debug(
            "nwa_data=%s", jsonutils.dumps(nwa_data, indent=4, sort_keys=True)
        )

        session = db_api.get_session()
        with session.begin(subtransactions=True):
            if necnwa_api.set_nwa_tenant_binding(
                    session,
                    tenant_id,
                    nwa_tenant_id,
                    nwa_data
            ):
                return {'status': 'SUCCESS'}

        return {'status': 'FAILED'}

    def delete_nwa_tenant_binding(self, rpc_context, **kwargs):
        LOG.debug("context=%s, kwargs=%s" % (rpc_context, kwargs))
        tenant_id = kwargs.get('tenant_id')
        nwa_tenant_id = kwargs.get('nwa_tenant_id')

        session = db_api.get_session()
        with session.begin(subtransactions=True):
            if necnwa_api.del_nwa_tenant_binding(
                    session,
                    tenant_id,
                    nwa_tenant_id
            ):
                return {'status': 'SUCCESS'}

        return {'status': 'FAILED'}

    def update_tenant_rpc_servers(self, rpc_context, **kwargs):
        ret = {'servers': []}

        servers = kwargs.get('servers')
        plugin = manager.NeutronManager.get_plugin()
        session = db_api.get_session()

        with session.begin(subtransactions=True):
            queues = necnwa_api.get_nwa_tenant_queues(session)
            for queue in queues:
                tenant_ids = [server['tenant_id'] for server in servers]
                if queue.tenant_id in tenant_ids:
                    LOG.info(_LI("RPC Server active(tid=%s)") %
                             queue.tenant_id)
                    continue
                else:
                    # create rpc server for tenant
                    LOG.debug("create_server: tid=%s", queue.tenant_id)
                    plugin.nwa_rpc.create_server(
                        rpc_context, queue.tenant_id
                    )
                    ret['servers'].append({'tenant_id': queue.tenant_id})

        return ret

    def update_port_state_with_notifier(self, rpc_context, **kwargs):
        device = kwargs.get('device')
        agent_id = kwargs.get('agent_id')
        port_id = kwargs.get('port_id')
        network_id = kwargs.get('network_id')
        network_type = kwargs.get('network_type')
        segmentation_id = kwargs.get('segmentation_id')
        physical_network = kwargs.get('physical_network')

        LOG.debug("device %(device)s "
                  "agent_id %(agent_id)s "
                  "port_id %(port_id)s "
                  "segmentation_id %(segmentation_id)d "
                  "physical_network %(physical_network)s ",
                  {'device': device, 'agent_id': agent_id,
                   'port_id': port_id,
                   'segmentation_id': segmentation_id,
                   'physical_network': physical_network})

        # 1 update segment
        session = db_api.get_session()
        with session.begin(subtransactions=True):
            try:
                query = (session.query(models_ml2.NetworkSegment).
                         filter_by(network_id=network_id))
                query = query.filter_by(physical_network=physical_network)
                query = query.filter_by(is_dynamic=True)
                record = query.one()
                record.segmentation_id = segmentation_id
            except sa_exc.NoResultFound:
                pass

        # 2 change port state
        plugin = manager.NeutronManager.get_plugin()
        plugin.update_port_status(
            rpc_context,
            port_id,
            q_const.PORT_STATUS_ACTIVE
        )

        # 3 serch db from port_id
        session = db_api.get_session()
        port = None
        with session.begin(subtransactions=True):
            try:
                port_db = (session.query(models_v2.Port).
                           enable_eagerloads(False).
                           filter(models_v2.Port.id.startswith(port_id)).
                           one())
                port = plugin._make_port_dict(port_db)
            except sa_exc.NoResultFound:
                LOG.error(_LE("Can't find port with port_id %s"),
                          port_id)
            except sa_exc.MultipleResultsFound:
                LOG.error(_LE("Multiple ports have port_id starting with %s"),
                          port_id)
        # 4 send notifier
        if port is not None:
            LOG.debug("notifier port_update %s, %s, %s" %
                      (network_type, segmentation_id, physical_network))
            plugin.notifier.port_update(
                rpc_context, port,
                network_type,
                segmentation_id,
                physical_network
            )

        return {}

    def release_dynamic_segment_from_agent(self, context, **kwargs):
        network_id = kwargs.get('network_id')
        physical_network = kwargs.get('physical_network')

        session = db_api.get_session()
        del_segment = db_ml2.get_dynamic_segment(
            session, network_id, physical_network=physical_network,
        )
        if del_segment:
            LOG.debug("release_dynamic_segment segment_id=%s" %
                      del_segment['id'])
            db_ml2.delete_network_segment(session, del_segment['id'])
