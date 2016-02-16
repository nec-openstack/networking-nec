# Copyright 2013 NEC Corporation
# All rights reserved.
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

from oslo_config import cfg
from testtools import matchers
from webob import exc

from neutron.common import exceptions as n_exc
from neutron import context
from neutron.extensions import portbindings
from neutron.tests.unit import _test_extension_portbindings as test_bindings
from neutron.tests.unit.agent import test_securitygroups_rpc as test_sg_rpc

from networking_nec.tests.unit.openflow import test_plugin


class TestNecPortBinding(test_bindings.PortBindingsTestCase,
                         test_plugin.NecPluginV2TestCase):
    VIF_TYPE = portbindings.VIF_TYPE_OVS
    VIF_DETAILS = {portbindings.CAP_PORT_FILTER: True,
                   portbindings.OVS_HYBRID_PLUG: True}
    ENABLE_SG = True
    FIREWALL_DRIVER = test_sg_rpc.FIREWALL_HYBRID_DRIVER

    def setUp(self):
        test_sg_rpc.set_firewall_driver(self.FIREWALL_DRIVER)
        cfg.CONF.set_override(
            'enable_security_group', self.ENABLE_SG,
            group='SECURITYGROUP')
        super(TestNecPortBinding, self).setUp()


class TestNecPortBindingNoSG(TestNecPortBinding):
    VIF_DETAILS = {portbindings.CAP_PORT_FILTER: False,
                   portbindings.OVS_HYBRID_PLUG: False}
    ENABLE_SG = False
    FIREWALL_DRIVER = test_sg_rpc.FIREWALL_NOOP_DRIVER


class TestNecPortBindingHost(
        test_bindings.PortBindingsHostTestCaseMixin,
        test_plugin.NecPluginV2TestCase):
    pass
