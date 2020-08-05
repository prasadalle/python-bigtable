# Copyright 2015 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""User friendly container for Google Cloud Bigtable Cluster."""


import re
from google.cloud.bigtable_admin_v2.types import instance_pb2


_CLUSTER_NAME_RE = re.compile(
    r"^projects/(?P<project>[^/]+)/"
    r"instances/(?P<instance>[^/]+)/clusters/"
    r"(?P<cluster_id>[a-z][-a-z0-9]*)$"
)


class BaseCluster(object):
    """Representation of a Google Cloud Bigtable Cluster.

    We can use a :class:`Cluster` to:

    * :meth:`reload` itself
    * :meth:`create` itself
    * :meth:`update` itself
    * :meth:`delete` itself

    :type cluster_id: str
    :param cluster_id: The ID of the cluster.

    :type instance: :class:`~google.cloud.bigtable.instance.Instance`
    :param instance: The instance where the cluster resides.

    :type location_id: str
    :param location_id: (Creation Only) The location where this cluster's
                        nodes and storage reside . For best performance,
                        clients should be located as close as possible to
                        this cluster.
                        For list of supported locations refer to
                        https://cloud.google.com/bigtable/docs/locations

    :type serve_nodes: int
    :param serve_nodes: (Optional) The number of nodes in the cluster.

    :type default_storage_type: int
    :param default_storage_type: (Optional) The type of storage
                                 Possible values are represented by the
                                 following constants:
                                 :data:`google.cloud.bigtable.enums.StorageType.SSD`.
                                 :data:`google.cloud.bigtable.enums.StorageType.SHD`,
                                 Defaults to
                                 :data:`google.cloud.bigtable.enums.StorageType.UNSPECIFIED`.

    :type _state: int
    :param _state: (`OutputOnly`)
                   The current state of the cluster.
                   Possible values are represented by the following constants:
                   :data:`google.cloud.bigtable.enums.Cluster.State.NOT_KNOWN`.
                   :data:`google.cloud.bigtable.enums.Cluster.State.READY`.
                   :data:`google.cloud.bigtable.enums.Cluster.State.CREATING`.
                   :data:`google.cloud.bigtable.enums.Cluster.State.RESIZING`.
                   :data:`google.cloud.bigtable.enums.Cluster.State.DISABLED`.
    """

    def __init__(
        self,
        cluster_id,
        instance,
        location_id=None,
        serve_nodes=None,
        default_storage_type=None,
        _state=None,
    ):
        self.cluster_id = cluster_id
        self._instance = instance
        self.location_id = location_id
        self.serve_nodes = serve_nodes
        self.default_storage_type = default_storage_type
        self._state = _state

    @classmethod
    def from_pb(cls, cluster_pb, instance):
        """Creates an cluster instance from a protobuf.

        For example:

        .. literalinclude:: snippets.py
            :start-after: [START bigtable_cluster_from_pb]
            :end-before: [END bigtable_cluster_from_pb]

        :type cluster_pb: :class:`instance_pb2.Cluster`
        :param cluster_pb: An instance protobuf object.

        :type instance: :class:`google.cloud.bigtable.instance.Instance`
        :param instance: The instance that owns the cluster.

        :rtype: :class:`Cluster`
        :returns: The Cluster parsed from the protobuf response.
        :raises: :class:`ValueError <exceptions.ValueError>` if the cluster
                 name does not match
                 ``projects/{project}/instances/{instance_id}/clusters/{cluster_id}``
                 or if the parsed instance ID does not match the istance ID
                 on the client.
                 or if the parsed project ID does not match the project ID
                 on the client.
        """
        match_cluster_name = _CLUSTER_NAME_RE.match(cluster_pb.name)
        if match_cluster_name is None:
            raise ValueError(
                "Cluster protobuf name was not in the " "expected format.",
                cluster_pb.name,
            )
        if match_cluster_name.group("instance") != instance.instance_id:
            raise ValueError(
                "Instance ID on cluster does not match the " "instance ID on the client"
            )
        if match_cluster_name.group("project") != instance._client.project:
            raise ValueError(
                "Project ID on cluster does not match the " "project ID on the client"
            )
        cluster_id = match_cluster_name.group("cluster_id")

        result = cls(cluster_id, instance)
        result._update_from_pb(cluster_pb)
        return result

    def _update_from_pb(self, cluster_pb):
        """Refresh self from the server-provided protobuf.
        Helper for :meth:`from_pb` and :meth:`reload`.
        """

        self.location_id = cluster_pb.location.split("/")[-1]
        self.serve_nodes = cluster_pb.serve_nodes
        self.default_storage_type = cluster_pb.default_storage_type
        self._state = cluster_pb.state

    @property
    def name(self):
        """Cluster name used in requests.

        .. note::
          This property will not change if ``_instance`` and ``cluster_id``
          do not, but the return value is not cached.

        For example:

        .. literalinclude:: snippets.py
            :start-after: [START bigtable_cluster_name]
            :end-before: [END bigtable_cluster_name]

        The cluster name is of the form

            ``"projects/{project}/instances/{instance}/clusters/{cluster_id}"``

        :rtype: str
        :returns: The cluster name.
        """
        return self._instance._client.instance_admin_client.cluster_path(
            self._instance._client.project, self._instance.instance_id, self.cluster_id
        )

    @property
    def state(self):
        """google.cloud.bigtable.enums.Cluster.State: state of cluster.

        For example:

        .. literalinclude:: snippets.py
            :start-after: [START bigtable_cluster_state]
            :end-before: [END bigtable_cluster_state]

        """
        return self._state

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        # NOTE: This does not compare the configuration values, such as
        #       the serve_nodes. Instead, it only compares
        #       identifying values instance, cluster ID and client. This is
        #       intentional, since the same cluster can be in different states
        #       if not synchronized. Clusters with similar instance/cluster
        #       settings but different clients can't be used in the same way.
        return other.cluster_id == self.cluster_id and other._instance == self._instance

    def __ne__(self, other):
        return not self == other

    def reload(self):
        raise NotImplementedError

    def exists(self):
        raise NotImplementedError

    def create(self):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError

    def _to_pb(self):
        """ Create cluster proto buff message for API calls """
        client = self._instance._client
        location = client.instance_admin_client.location_path(
            client.project, self.location_id
        )
        cluster_pb = instance_pb2.Cluster(
            location=location,
            serve_nodes=self.serve_nodes,
            default_storage_type=self.default_storage_type,
        )
        return cluster_pb
