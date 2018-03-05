"""
This is the requires side of the interface layer, for use in charms that
wish to request integration with AWS native features.  The integration will
be provided by the AWS integration charm, which allows the requiring charm
to not require cloud credentials itself and not have a lot of AWS specific
API code.

The flags that are set by the requires side of this interface are:

* **`endpoint.{endpoint_name}.joined`** This flag is set when the relation
  has been joined, and the charm should then use the methods documented below
  to request specific AWS features.  This flag is automatically removed if
  the relation is broken.  It should not be removed by the charm.

* **`endpoint.{endpoint_name}.ready`** This flag is set once the requested
  features have been enabled for the AWS instance on which the charm is
  running.  This flag is automatically removed if new integration features
  are requested.  It should not be removed by the charm.
"""


import json
import string
from hashlib import sha256
from urllib.parse import urljoin
from urllib.request import urlopen

from charmhelpers.core import unitdata

from charms.reactive import Endpoint
from charms.reactive import when
from charms.reactive import set_flag, clear_flag


class AWSRequires(Endpoint):
    """
    Example usage:

    ```python
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
    ```
    """
    _metadata_url = 'http://169.254.169.254/latest/meta-data/'
    _instance_id_url = urljoin(_metadata_url, 'instance-id')
    _az_url = urljoin(_metadata_url, 'placement/availability-zone')

    @property
    def _received(self):
        """
        Helper to streamline access to received data since we expect to only
        ever be connected to a single AWS integration application with a
        single unit.
        """
        return self.relations[0].joined_units.received

    @property
    def _to_publish(self):
        """
        Helper to streamline access to received data since we expect to only
        ever be connected to a single AWS integration application with a
        single unit.
        """
        return self.relations[0].to_publish

    @when('endpoint.{endpoint_name}.joined')
    def send_instance_info(self):
        self._to_publish['instance-id'] = self.instance_id
        self._to_publish['region'] = self.region

    @when('endpoint.{endpoint_name}.changed')
    def check_ready(self):
        completed = self._received.get('completed', {})
        actual_hash = completed.get(self.instance_id)
        if actual_hash == self.expected_hash:
            set_flag(self.expand_name('ready'))
        clear_flag(self.expand_name('changed'))

    @property
    def instance_id(self):
        if not hasattr(self, '_instance_id'):
            cache_key = self.expand_name('instance-id')
            cached = unitdata.kv().get(cache_key)
            if cached:
                self._instance_id = cached
            else:
                with urlopen(self._instance_id_url) as fd:
                    self._instance_id = fd.read(256).decode('utf8')
                unitdata.kv().set(cache_key, self._instance_id)
        return self._instance_id

    @property
    def region(self):
        if not hasattr(self, '_region'):
            cache_key = self.expand_name('region')
            cached = unitdata.kv().get(cache_key)
            if cached:
                self._region = cached
            else:
                with urlopen(self._az_url) as fd:
                    az = fd.read(256).decode('utf8')
                    self._region = az.rstrip(string.ascii_lowercase)
                unitdata.kv().set(cache_key, self._region)
        return self._region

    @property
    def expected_hash(self):
        return sha256(json.dumps(dict(self._to_publish),
                                 sort_keys=True).encode('utf8')).hexdigest()

    def request_instance_tags(self, tags):
        """
        Request that the given tags be applied to this instance.

        # Parameters
        tags (dict): Mapping of tag names to values (or `None`).
        """
        self._to_publish['instance-tags'] = dict(tags)
        clear_flag(self.expand_name('ready'))

    def request_security_group_tags(self, tags):
        """
        Request that the given tags be applied to all of this instance's
        security groups.

        # Parameters
        tags (dict): Mapping of tag names to values (or `None`).
        """
        self._to_publish['security-group-tags'] = dict(tags)
        clear_flag(self.expand_name('ready'))

    def request_subnet_tags(self, tags):
        """
        Request that the given tags be applied to all of this instance's
        subnets.

        # Parameters
        tags (dict): Mapping of tag names to values (or `None`).
        """
        self._to_publish['subnet-tags'] = dict(tags)
        clear_flag(self.expand_name('ready'))

    def enable_elb(self):
        """
        Request that ELB integration be enabled for this instance.
        """
        self._to_publish['enable-elb'] = True
        clear_flag(self.expand_name('ready'))

    def enable_ebs(self):
        """
        Request that EBS integration be enabled for this instance.
        """
        self._to_publish['enable-ebs'] = True
        clear_flag(self.expand_name('ready'))

    def enable_route53(self):
        """
        Request that Route53 integration be enabled for this instance.
        """
        self._to_publish['enable-route53'] = True
        clear_flag(self.expand_name('ready'))

    def enable_s3_read(self):
        """
        Request that S3 read-only integration be enabled for this instance.
        """
        self._to_publish['enable-s3-read'] = True
        clear_flag(self.expand_name('ready'))

    def enable_s3_write(self):
        """
        Request that S3 read/write integration be enabled for this instance.
        """
        self._to_publish['enable-s3-write'] = True
        clear_flag(self.expand_name('ready'))
