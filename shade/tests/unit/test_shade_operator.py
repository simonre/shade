# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import mock
import testtools

from openstack.config import cloud_region
import shade
from shade import exc
from shade.tests import fakes
from shade.tests.unit import base


class TestShadeOperator(base.RequestsMockTestCase):

    def setUp(self):
        super(TestShadeOperator, self).setUp()

    def test_operator_cloud(self):
        self.assertIsInstance(self.op_cloud, shade.OperatorCloud)

    def test_get_image_name(self):
        self.use_glance()

        image_id = self.getUniqueString()
        fake_image = fakes.make_fake_image(image_id=image_id)
        list_return = {'images': [fake_image]}

        self.register_uris([
            dict(method='GET',
                 uri='https://image.example.com/v2/images',
                 json=list_return),
            dict(method='GET',
                 uri='https://image.example.com/v2/images',
                 json=list_return),
        ])

        self.assertEqual('fake_image', self.op_cloud.get_image_name(image_id))
        self.assertEqual(
            'fake_image', self.op_cloud.get_image_name('fake_image'))

        self.assert_calls()

    def test_get_image_id(self):
        self.use_glance()

        image_id = self.getUniqueString()
        fake_image = fakes.make_fake_image(image_id=image_id)
        list_return = {'images': [fake_image]}

        self.register_uris([
            dict(method='GET',
                 uri='https://image.example.com/v2/images',
                 json=list_return),
            dict(method='GET',
                 uri='https://image.example.com/v2/images',
                 json=list_return),
        ])

        self.assertEqual(image_id, self.op_cloud.get_image_id(image_id))
        self.assertEqual(
            image_id, self.op_cloud.get_image_id('fake_image'))

        self.assert_calls()

    @mock.patch.object(cloud_region.CloudRegion, 'get_session')
    def test_get_session_endpoint_exception(self, get_session_mock):
        class FakeException(Exception):
            pass

        def side_effect(*args, **kwargs):
            raise FakeException("No service")
        session_mock = mock.Mock()
        session_mock.get_endpoint.side_effect = side_effect
        get_session_mock.return_value = session_mock
        self.op_cloud.name = 'testcloud'
        self.op_cloud.config.region_name = 'testregion'
        with testtools.ExpectedException(
                exc.OpenStackCloudException,
                "Error getting image endpoint on testcloud:testregion:"
                " No service"):
            self.op_cloud.get_session_endpoint("image")

    @mock.patch.object(cloud_region.CloudRegion, 'get_session')
    def test_get_session_endpoint_unavailable(self, get_session_mock):
        session_mock = mock.Mock()
        session_mock.get_endpoint.return_value = None
        get_session_mock.return_value = session_mock
        image_endpoint = self.op_cloud.get_session_endpoint("image")
        self.assertIsNone(image_endpoint)

    @mock.patch.object(cloud_region.CloudRegion, 'get_session')
    def test_get_session_endpoint_identity(self, get_session_mock):
        session_mock = mock.Mock()
        get_session_mock.return_value = session_mock
        self.op_cloud.get_session_endpoint('identity')
        kwargs = dict(
            interface='public', region_name='RegionOne',
            service_name=None, service_type='identity')

        session_mock.get_endpoint.assert_called_with(**kwargs)

    @mock.patch.object(cloud_region.CloudRegion, 'get_session')
    def test_has_service_no(self, get_session_mock):
        session_mock = mock.Mock()
        session_mock.get_endpoint.return_value = None
        get_session_mock.return_value = session_mock
        self.assertFalse(self.op_cloud.has_service("image"))

    @mock.patch.object(cloud_region.CloudRegion, 'get_session')
    def test_has_service_yes(self, get_session_mock):
        session_mock = mock.Mock()
        session_mock.get_endpoint.return_value = 'http://fake.url'
        get_session_mock.return_value = session_mock
        self.assertTrue(self.op_cloud.has_service("image"))

    def test_list_hypervisors(self):
        '''This test verifies that calling list_hypervisors results in a call
        to nova client.'''
        self.register_uris([
            dict(method='GET',
                 uri=self.get_mock_url(
                     'compute', 'public', append=['os-hypervisors', 'detail']),
                 json={'hypervisors': [
                     fakes.make_fake_hypervisor('1', 'testserver1'),
                     fakes.make_fake_hypervisor('2', 'testserver2'),
                 ]}),
        ])

        r = self.op_cloud.list_hypervisors()

        self.assertEqual(2, len(r))
        self.assertEqual('testserver1', r[0]['hypervisor_hostname'])
        self.assertEqual('testserver2', r[1]['hypervisor_hostname'])

        self.assert_calls()
