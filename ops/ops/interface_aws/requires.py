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
from typing import Mapping, Optional
from urllib.error import HTTPError, URLError
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


def _metadata(url):
    """Retrieve instance metadata from AWS.
    https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-data-retrieval.html
    """
    token_req = Request(
        _METADATAV2_TOKEN_URL,
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
        method="PUT",
    )
    try:
        with urlopen(token_req) as fd:
            token = fd.read(READ_BLOCK_SIZE).decode("utf8")
            req = Request(url, headers={"X-aws-ec2-metadata-token": token})
        with urlopen(req) as fd:
            return fd.read(READ_BLOCK_SIZE).decode("utf8")
    except (URLError, HTTPError) as e:
        raise AWSIntegrationError(url, "Failed to get instance metadata") from e


class AWSIntegrationError(Exception):
    def __init__(self, url: str, *args: object) -> None:
        super().__init__(*args)
        self.url = url


class AWSIntegrationRequires(ops.Object):
    """Requires side of aws relation.

    Example usage:

    ```python

    class MyCharm(ops.CharmBase):

        def __init__(self, *args):
            super().__init__(*args)
            self.aws = AwsIntegrationRequires(self)
            ...

        def request_aws_integration(self):
            self.aws.request_instance_tags({
                'tag1': 'value1',
                'tag2': None,
            })
            self.aws.request_load_balancer_management()
            # ...

        def check_aws_integration(self):
            if self.aws.is_ready():
                update_config_enable_aws()
        ```
    """

    _stored = ops.StoredState()

    def __init__(self, charm: ops.CharmBase, endpoint="aws"):
        super().__init__(charm, f"relation-{endpoint}")
        self.endpoint = endpoint
        self.charm = charm

        events = charm.on[endpoint]
        self.framework.observe(events.relation_joined, self._joined)
        self._stored.set_default(instance_id=None, region=None)

    @property
    def relation(self) -> Optional[ops.Relation]:
        """The relation to the integrator, or None."""
        relations = self.charm.model.relations.get(self.endpoint)
        return relations[0] if relations else None

    @property
    def _received(self) -> Mapping[str, str]:
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
        log.info(
            "%s is instance=%s in region=%s",
            self.charm.unit.name,
            self.instance_id,
            self.region,
        )
        self._request({"instance-id": self.instance_id, "region": self.region})

    @property
    def is_ready(self):
        completed = json.loads(self._received.get("completed", "{}"))
        response_hash = completed.get(self.instance_id)
        ready = response_hash == self._expected_hash
        if not response_hash:
            log.warning("Remote end is yet to calculate a response")
        elif not ready:
            log.warning(
                "Waiting for response_hash=%s to be self._expected_hash=%s",
                response_hash,
                self._expected_hash,
            )
        return ready

    def evaluate_relation(self, event) -> Optional[str]:
        """Determine if relation is ready."""
        no_relation = not self.relation or (
            isinstance(event, ops.RelationBrokenEvent)
            and event.relation is self.relation
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
            self._stored.instance_id = _metadata(_INSTANCE_ID_URL)
        return self._stored.instance_id

    @cached_property
    def region(self):
        """The region this unit is in."""
        if self._stored.region is None:
            az = _metadata(_AZ_URL)
            self._stored.region = az.rstrip(string.ascii_lowercase)
        return self._stored.region

    @property
    def _expected_hash(self):
        def from_json(s: str):
            try:
                return json.loads(s)
            except json.decoder.JSONDecodeError:
                return s

        to_sha = {key: from_json(val) for key, val in self._to_publish.items()}
        return sha256(json.dumps(to_sha, sort_keys=True).encode()).hexdigest()

    def _request(self, keyvals):
        kwds = {key: json.dumps(val) for key, val in keyvals.items()}
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
