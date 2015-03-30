#   Copyright 2013 Rackspace Hosting
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

"""The shelved mode extension."""

import webob
from webob import exc

from nova.api.openstack import common
from nova.api.openstack import extensions as exts
from nova.api.openstack import wsgi
from nova import compute
from nova import exception


ALIAS = 'os-shelve'
auth_shelve = exts.extension_authorizer('compute', 'v3:%s:shelve' % ALIAS)
auth_shelve_offload = exts.extension_authorizer('compute',
                                                'v3:%s:shelve_offload' % ALIAS)
auth_unshelve = exts.extension_authorizer('compute', 'v3:%s:unshelve' % ALIAS)


class ShelveController(wsgi.Controller):
    def __init__(self, *args, **kwargs):
        super(ShelveController, self).__init__(*args, **kwargs)
        self.compute_api = compute.API()

    @exts.expected_errors((404, 409))
    @wsgi.action('shelve')
    def _shelve(self, req, id, body):
        """Move an instance into shelved mode."""
        context = req.environ["nova.context"]
        auth_shelve(context)

        instance = common.get_instance(self.compute_api, context, id,
                                       want_objects=True)
        try:
            self.compute_api.shelve(context, instance)
        except exception.InstanceIsLocked as e:
            raise exc.HTTPConflict(explanation=e.format_message())
        except exception.InstanceInvalidState as state_error:
            common.raise_http_conflict_for_instance_invalid_state(state_error,
                                                                  'shelve')

        return webob.Response(status_int=202)

    @exts.expected_errors((404, 409))
    @wsgi.action('shelve_offload')
    def _shelve_offload(self, req, id, body):
        """Force removal of a shelved instance from the compute node."""
        context = req.environ["nova.context"]
        auth_shelve_offload(context)

        instance = common.get_instance(self.compute_api, context, id,
                                       want_objects=True)
        try:
            self.compute_api.shelve_offload(context, instance)
        except exception.InstanceIsLocked as e:
            raise exc.HTTPConflict(explanation=e.format_message())
        except exception.InstanceInvalidState as state_error:
            common.raise_http_conflict_for_instance_invalid_state(state_error,
                                                              'shelve_offload')

        return webob.Response(status_int=202)

    @exts.expected_errors((404, 409))
    @wsgi.action('unshelve')
    def _unshelve(self, req, id, body):
        """Restore an instance from shelved mode."""
        context = req.environ["nova.context"]
        auth_unshelve(context)
        instance = common.get_instance(self.compute_api, context, id,
                                       want_objects=True)
        try:
            self.compute_api.unshelve(context, instance)
        except exception.InstanceIsLocked as e:
            raise exc.HTTPConflict(explanation=e.format_message())
        except exception.InstanceInvalidState as state_error:
            common.raise_http_conflict_for_instance_invalid_state(state_error,
                                                                  'unshelve')
        return webob.Response(status_int=202)


class Shelve(exts.V3APIExtensionBase):
    """Instance shelve mode."""

    name = "Shelve"
    alias = ALIAS
    version = 1

    def get_controller_extensions(self):
        controller = ShelveController()
        extension = exts.ControllerExtension(self, 'servers', controller)
        return [extension]

    def get_resources(self):
        return []
