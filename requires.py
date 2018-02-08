import json
from hashlib import sha256
from urllib.request import urlopen

from charmhelpers.core import unitdata

from charms.reactive import Endpoint
from charms.reactive import when
from charms.reactive import set_flag, clear_flag


class AWSRequires(Endpoint):
    """
    Example usage::

        from charms.reactive import when, endpoint_from_flag

        @when('endpoint.aws.joined')
        def request_aws_integration():
            aws = endpoint_from_flag('endpoint.aws.joined')
            aws.request_instance_tags({
                'tag1': 'value1',
                'tag2': None,
            })
            aws.request_elb()
            # ...

        @when('endpoint.aws.ready')
        def aws_integration_ready():
            update_config_enable_aws()
    """
    instance_id_url = 'http://169.254.169.254/latest/meta-data/instance-id'

    @when('endpoint.{endpoint_name}.joined')
    def send_instance_id(self):
        self.relation.to_publish['instance-id'] = self.instance_id

    @when('endpoint.{endpoint_name}.changed')
    def check_ready(self):
        completed = self.relation.received.get('completed', {})
        actual_hash = completed.get(self.instance_id)
        if actual_hash == self.expected_hash:
            set_flag(self.expand_name('ready'))
        clear_flag(self.expand_name('changed'))

    @property
    def relation(self):
        # we expect to only every be connected to one integration charm
        return self.relations[0]

    @property
    def instance_id(self):
        if not hasattr(self, '_instance_id'):
            cache_key = self.expand_name('instance-id')
            cached = unitdata.kv().get(cache_key)
            if not cached:
                with urlopen(self.instance_id_url) as fd:
                    self._instance_id = fd.read(256).decode('utf8')
                unitdata.kv().set(cache_key, self._instance_id)
        return self._instance_id

    @property
    def expected_hash(self):
        return sha256(json.dumps(dict(self.relation.to_publish),
                                 sort_keys=True).encode('utf8')).hexdigest()

    def request_instance_tags(self, tags):
        """
        Request that the given tags be applied to this instance.

        :param dict tags: Mapping of tag names to values (or ``None``).
        """
        self.relation.to_publish['instance-tags'] = dict(tags)
        clear_flag(self.expand_name('ready'))

    def request_security_group_tags(self, tags):
        """
        Request that the given tags be applied to all of this instance's
        security groups.

        :param dict tags: Mapping of tag names to values (or ``None``).
        """
        self.relation.to_publish['security-group-tags'] = dict(tags)
        clear_flag(self.expand_name('ready'))

    def request_subnet_tags(self, tags):
        """
        Request that the given tags be applied to all of this instance's
        subnets.

        :param dict tags: Mapping of tag names to values (or ``None``).
        """
        self.relation.to_publish['subnet-tags'] = dict(tags)
        clear_flag(self.expand_name('ready'))

    def enable_elb(self):
        """
        Request that ELB integration be enabled for this instance.
        """
        self.relation.to_publish['enable-elb'] = True
        clear_flag(self.expand_name('ready'))

    def enable_ebs(self):
        """
        Request that EBS integration be enabled for this instance.
        """
        self.relation.to_publish['enable-ebs'] = True
        clear_flag(self.expand_name('ready'))

    def enable_route53(self):
        """
        Request that Route53 integration be enabled for this instance.
        """
        self.relation.to_publish['enable-route53'] = True
        clear_flag(self.expand_name('ready'))

    def enable_s3_read(self):
        """
        Request that S3 read-only integration be enabled for this instance.
        """
        self.relation.to_publish['enable-s3-read'] = True
        clear_flag(self.expand_name('ready'))

    def enable_s3_write(self):
        """
        Request that S3 read/write integration be enabled for this instance.
        """
        self.relation.to_publish['enable-s3-write'] = True
        clear_flag(self.expand_name('ready'))
