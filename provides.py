import json
from hashlib import sha256

from charmhelpers.core import unitdata

from charms.reactive import Endpoint
from charms.reactive import when
from charms.reactive import toggle_flag, clear_flag


class AWSProvides(Endpoint):
    """
    Example usage::

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
    """

    @when('endpoint.{endpoint_name}.changed')
    def check_services(self):
        toggle_flag(self.expand_name('requested'),
                    len(self.requests) > 0)
        clear_flag(self.expand_name('changed'))

    @property
    def requests(self):
        """
        A list of the new or updated :class:`IntegrationRequests` that
        have been made.
        """
        all_requests = [IntegrationRequest(unit)
                        for unit in self.all_joined_units]
        return [request for request in all_requests
                if request.changed]


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
        saved_hash = unitdata.kv().get(self._hash_key)
        return saved_hash == self.hash

    def mark_completed(self):
        """
        Mark this request as having been completed.
        """
        completed = self._unit.relation.to_publish.setdefault('completed', {})
        completed[self.instance_id] = self.hash
        unitdata.kv().set(self._hash_key, self.hash)

    @property
    def instance_id(self):
        """
        The instance ID reported for this request.
        """
        return self._unit.received['instance-id']

    @property
    def instance_tags(self):
        """
        Mapping of tag names to values (or ``None``) to apply to this instance.
        """
        # uses dict() here to make a copy, just to be safe
        return dict(self._unit.received.get('instance-tags', {}))

    @property
    def security_group_tags(self):
        """
        Mapping of tag names to values (or ``None``) to apply to all of this
        instance's security groups.
        """
        # uses dict() here to make a copy, just to be safe
        return dict(self._unit.received.get('security-group-tags', {}))

    @property
    def subnet_tags(self):
        """
        Mapping of tag names to values (or ``None``) to apply to all of this
        instance's subnets.
        """
        # uses dict() here to make a copy, just to be safe
        return dict(self._unit.received.get('subnet-tags', {}))

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
    def requested_s3_write(self):
        """
        Flag indicating whether S3 read/write integration was requested.
        """
        return bool(self._unit.received['enable-s3-write'])
