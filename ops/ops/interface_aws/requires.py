# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
"""Implementation of aws interface.

This only implements the requires side, currently, since the providers
is still using the Reactive Charm framework self.
"""
import json
from hashlib import sha256
import logging
import ops
import string
from functools import cached_property
from typing import  Mapping, Optional
from urllib.parse import urljoin
from urllib.request import urlopen, Request


log = logging.getLogger(__name__)

# block size to read data from AWS metadata service
# (realistically, just needs to be bigger than ~20 chars)
READ_BLOCK_SIZE = 2048

# the IP is the AWS metadata service, documented here:
# https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html
_METADATAV2_TOKEN_URL = "http://169.254.169.254/latest/api/token"
_METADATA_URL = "http://169.254.169.254/latest/meta-data/"
_INSTANCE_ID_URL = urljoin(_METADATA_URL, "instance-id")
_AZ_URL = urljoin(_METADATA_URL, "placement/availability-zone")

def _imdv2_request(url):
    token_req = Request(
        _METADATAV2_TOKEN_URL,
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
    )
    setattr(token_req, "method", "PUT")

    with urlopen(token_req) as fd:
        token = fd.read(READ_BLOCK_SIZE).decode("utf8")
        return Request(url, headers={"X-aws-ec2-metadata-token": token})


class AWSIntegrationRequires(ops.Object):
    """Requires side of aws relation.

    Example usage:

    ```python

    class MyCharm(ops.CharmBase):

        def __init__(self, *args):
            super().__init__(*args)
            self.aws = AwsIntegrationRequires(self)
            ...
    
        def request_aws_integration():
            self.aws.request_instance_tags({
                'tag1': 'value1',
                'tag2': None,
            })
            aws.request_load_balancer_management()
            # ...

        def check_aws_integration():
            if self.aws.is_ready():
                update_config_enable_aws()
        ```
    """

    _stored = ops.StoredState()

    def __init__(self, charm: ops.CharmBase, endpoint="aws"):
        super().__init__(charm, f"relation-{endpoint}")
        self.endpoint = endpoint
        self.charm =charm
        
        events = charm.on[endpoint]
        self.framework.observe(events.relation_joined, self._joined)
        self._stored.set_default(instance_id=None,region=None)

    @property
    def relation(self) -> Optional[ops.Relation]:
        """The relation to the integrator, or None."""
        relations = self.charm.model.relations.get(self.endpoint)
        return relations[0] if relations else None

    @property
    def _received(self) -> Mapping[str,str]:
        """
        Helper to streamline access to received data since we expect to only
        ever be connected to a single AWS integration application with a
        single unit.
        """
        if self.relation and self.relation.units:
            return self.relation.data[list(self.relation.units)[0]]
        return {}

    @property
    def _to_publish(self):
        """
        Helper to streamline access to received data since we expect to only
        ever be connected to a single AWS integration application with a
        single unit.
        """
        if self.relation:
            return self.relation.data[self.charm.model.unit]
        return {}


    def _joined(self, _):
        self._to_publish["instance-id"] = self.instance_id
        self._to_publish["region"] = self.region

    @property
    def is_ready(self):
        completed = json.loads(self._received.get("completed", "{}"))
        response_hash = completed.get(self.instance_id)
        return response_hash == self._expected_hash
    
    def evaluate_relation(self, event) -> Optional[str]:
        """Determine if relation is ready."""
        no_relation = not self.relation or (
            isinstance(event, ops.RelationBrokenEvent) and event.relation is self.relation
        )
        if no_relation:
            return f"Missing required {self.endpoint}"
        if not self.is_ready:
            return f"Waiting for {self.endpoint}"
        return None

    @cached_property
    def instance_id(self):
        """This unit's instance-id."""
        if self._stored.instance_id is None:
            req = _imdv2_request(_INSTANCE_ID_URL)
            with urlopen(req) as fd:
                self._stored.instance_id = fd.read(READ_BLOCK_SIZE).decode("utf8")
        return self._stored.instance_id

    @cached_property
    def region(self):
        """The region this unit is in."""
        if self._stored.region is None:
            req = _imdv2_request(_AZ_URL)
            with urlopen(req) as fd:
                az = fd.read(READ_BLOCK_SIZE).decode("utf8")
                self._stored.region = az.rstrip(string.ascii_lowercase)
        return self._stored.region

    @property
    def _expected_hash(self):
        return sha256(
            json.dumps(dict(self._to_publish), sort_keys=True).encode("utf8")
        ).hexdigest()

    def _request(self, keyvals):
        kwds={key: json.dumps(val) for key,val in keyvals.items()}
        self._to_publish.update(**kwds)
        self._to_publish["requested"] = "true"

    def tag_instance(self, tags):
        """
        Request that the given tags be applied to this instance.

        # Parameters
        `tags` (dict): Mapping of tag names to values (or `None`).
        """
        self._request({"instance-tags": dict(tags)})

    def tag_instance_security_group(self, tags):
        """
        Request that the given tags be applied to this instance's
        machine-specific security group (firewall) created by Juju.

        # Parameters
        `tags` (dict): Mapping of tag names to values (or `None`).
        """
        self._request({"instance-security-group-tags": dict(tags)})

    def tag_instance_subnet(self, tags):
        """
        Request that the given tags be applied to this instance's subnet.

        # Parameters
        `tags` (dict): Mapping of tag names to values (or `None`).
        """
        self._request({"instance-subnet-tags": dict(tags)})

    def enable_acm_readonly(self):
        """
        Request readonly for ACM.
        """
        self._request({"enable-acm-readonly": True})

    def enable_acm_fullaccess(self):
        """
        Request fullaccess for ACM.
        """
        self._request({"enable-acm-fullaccess": True})

    def enable_autoscaling_readonly(self):
        """
        Request readonly access for autoscaling.
        """
        self._request({"enable-autoscaling-readonly": True})

    def enable_instance_inspection(self):
        """
        Request the ability to inspect instances.
        """
        self._request({"enable-instance-inspection": True})

    def enable_instance_modification(self):
        """
        Request the ability to modify instances.
        """
        self._request({"enable-instance-modification": True})

    def enable_network_management(self):
        """
        Request the ability to manage networking (firewalls, subnets, etc).
        """
        self._request({"enable-network-management": True})

    def enable_load_balancer_management(self):
        """
        Request the ability to manage load balancers.
        """
        self._request({"enable-load-balancer-management": True})

    def enable_block_storage_management(self):
        """
        Request the ability to manage block storage.
        """
        self._request({"enable-block-storage-management": True})

    def enable_dns_management(self):
        """
        Request the ability to manage DNS.
        """
        self._request({"enable-dns-management": True})

    def enable_region_readonly(self):
        """
        Request the ability to read region features.
        """
        self._request({"enable-region-readonly": True})

    def enable_object_storage_access(self, patterns=None):
        """
        Request the ability to access object storage.

        # Parameters
        `patterns` (list): If given, restrict access to the resources matching
            the patterns. If patterns do not start with the S3 ARN prefix
            (`arn:aws:s3:::`), it will be prepended.
        """
        if patterns:
            for i, pattern in enumerate(patterns):
                if not pattern.startswith("arn:aws:s3:::"):
                    patterns[i] = "arn:aws:s3:::{}".format(pattern)
        self._request(
            {
                "enable-object-storage-access": True,
                "object-storage-access-patterns": patterns,
            }
        )

    def enable_object_storage_management(self, patterns=None):
        """
        Request the ability to manage object storage.

        # Parameters
        `patterns` (list): If given, restrict management to the resources
            matching the patterns. If patterns do not start with the S3 ARN
            prefix (`arn:aws:s3:::`), it will be prepended.
        """
        if patterns:
            for i, pattern in enumerate(patterns):
                if not pattern.startswith("arn:aws:s3:::"):
                    patterns[i] = "arn:aws:s3:::{}".format(pattern)
        self._request(
            {
                "enable-object-storage-management": True,
                "object-storage-management-patterns": patterns,
            }
        )
