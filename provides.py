"""
This is the provides side of the interface layer, for use only by the AWS
integration charm itself.

The flags that are set by the provides side of this interface are:

* **`endpoint.{endpoint_name}.requested`** This flag is set when there is
  a new or updated request by a remote unit for AWS integration features.
  The AWS integration charm should then iterate over each request, perform
  whatever actions are necessary to satisfy those requests, and then mark
  them as complete.
"""

import json
from hashlib import sha256

from charmhelpers.core import unitdata

from charms.reactive import Endpoint
from charms.reactive import when
from charms.reactive import toggle_flag, clear_flag


class AWSProvides(Endpoint):
    """
    Example usage:

    ```python
    from charms.reactive import when, endpoint_from_flag

    @when('endpoint.aws.requested')
    def handle_requests():
        aws = endpoint_from_flag('endpoint.aws.requested')
        for request in aws.requests:
            if request.instance_tags:
                tag_instance(request.instance_id, request.instance_tags)
            if request.requested_elb:
                enable_elb(request.instance_id)
            # ...
            request.mark_completed()
    ```
    """

    @when('endpoint.{endpoint_name}.changed')
    def check_requests(self):
        requests = self.requests
        toggle_flag(self.expand_name('requested'), len(requests) > 0)
        clear_flag(self.expand_name('changed'))

    @when('endpoint.{endpoint_name}.departed')
    def cleanup(self):
        for unit in self.all_departed_units:
            request = IntegrationRequest(unit)
            request._clear_hash()
        self.all_departed_units.clear()
        clear_flag(self.expand_name('departed'))

    @property
    def requests(self):
        """
        A list of the new or updated #IntegrationRequests that
        have been made.
        """
        all_requests = [IntegrationRequest(unit)
                        for unit in self.all_joined_units]
        return [request for request in all_requests
                if request.changed]

    @property
    def application_names(self):
        """
        Set of names of all applications that are still joined.
        """
        return {unit.application_name for unit in self.all_joined_units}


class IntegrationRequest:
    """
    A request for integration from a single remote unit.
    """
    def __init__(self, unit):
        self._unit = unit
        self._hash = sha256(json.dumps(dict(unit.received),
                                       sort_keys=True).encode('utf8')
                            ).hexdigest()

    @property
    def hash(self):
        """
        SHA hash of the data for this request.
        """
        return self._hash

    @property
    def _hash_key(self):
        endpoint = self._unit.relation.endpoint
        return endpoint.expand_name('request.{}'.format(self.instance_id))

    @property
    def changed(self):
        """
        Whether this request has changed since the last time it was
        marked completed.
        """
        if not self.instance_id:
            return False
        saved_hash = unitdata.kv().get(self._hash_key)
        result = saved_hash != self.hash
        return result

    def mark_completed(self):
        """
        Mark this request as having been completed.
        """
        completed = self._unit.relation.to_publish.get('completed', {})
        completed[self.instance_id] = self.hash
        unitdata.kv().set(self._hash_key, self.hash)
        self._unit.relation.to_publish['completed'] = completed

    def _clear_hash(self):
        unitdata.kv().unset(self._hash_key)

    @property
    def application_name(self):
        """
        The name of the application making the request.
        """
        return self._unit.application_name

    @property
    def instance_id(self):
        """
        The instance ID reported for this request.
        """
        return self._unit.received['instance-id']

    @property
    def region(self):
        """
        The region reported for this request.
        """
        return self._unit.received['region']

    @property
    def instance_tags(self):
        """
        Mapping of tag names to values (or `None`) to apply to this instance.
        """
        # uses dict() here to make a copy, just to be safe
        return dict(self._unit.received.get('instance-tags', {}))

    @property
    def unit_security_group_tags(self):
        """
        Mapping of tag names to values (or `None`) to apply to this instance's
        unit-specific security group.
        """
        # uses dict() here to make a copy, just to be safe
        return dict(self._unit.received.get('instance-sec-grp-tags', {}))

    @property
    def instance_subnet_tags(self):
        """
        Mapping of tag names to values (or `None`) to apply to this instance's
        subnet.
        """
        # uses dict() here to make a copy, just to be safe
        return dict(self._unit.received.get('instance-subnet-tags', {}))

    @property
    def requested_elb(self):
        """
        Flag indicating whether ELB integration was requested.
        """
        return bool(self._unit.received['enable-elb'])

    @property
    def requested_ebs(self):
        """
        Flag indicating whether EBS integration was requested.
        """
        return bool(self._unit.received['enable-ebs'])

    @property
    def requested_route53(self):
        """
        Flag indicating whether Route53 integration was requested.
        """
        return bool(self._unit.received['enable-route53'])

    @property
    def requested_s3_read(self):
        """
        Flag indicating whether S3 read-only integration was requested.
        """
        return bool(self._unit.received['enable-s3-read'])

    @property
    def s3_read_patterns(self):
        """
        List of patterns to which to restrict S3 read access.
        """
        return list(self._unit.received['s3-read-patterns'] or [])

    @property
    def requested_s3_write(self):
        """
        Flag indicating whether S3 read/write integration was requested.
        """
        return bool(self._unit.received['enable-s3-write'])

    @property
    def s3_write_patterns(self):
        """
        List of patterns to which to restrict S3 write access.
        """
        return list(self._unit.received['s3-write-patterns'] or [])
