<h1 id="requires">requires</h1>


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

<h1 id="requires.AWSRequires">AWSRequires</h1>

```python
AWSRequires(self, endpoint_name, relation_ids=None)
```

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

<h2 id="requires.AWSRequires.enable_route53">enable_route53</h2>

```python
AWSRequires.enable_route53(self)
```

Request that Route53 integration be enabled for this instance.

<h2 id="requires.AWSRequires.request_instance_tags">request_instance_tags</h2>

```python
AWSRequires.request_instance_tags(self, tags)
```

Request that the given tags be applied to this instance.

__Parameters__

- __tags (dict)__: Mapping of tag names to values (or `None`).

<h2 id="requires.AWSRequires.enable_s3_write">enable_s3_write</h2>

```python
AWSRequires.enable_s3_write(self)
```

Request that S3 read/write integration be enabled for this instance.

<h2 id="requires.AWSRequires.enable_s3_read">enable_s3_read</h2>

```python
AWSRequires.enable_s3_read(self)
```

Request that S3 read-only integration be enabled for this instance.

<h2 id="requires.AWSRequires.enable_elb">enable_elb</h2>

```python
AWSRequires.enable_elb(self)
```

Request that ELB integration be enabled for this instance.

<h2 id="requires.AWSRequires.enable_ebs">enable_ebs</h2>

```python
AWSRequires.enable_ebs(self)
```

Request that EBS integration be enabled for this instance.

<h2 id="requires.AWSRequires.request_security_group_tags">request_security_group_tags</h2>

```python
AWSRequires.request_security_group_tags(self, tags)
```

Request that the given tags be applied to all of this instance's
security groups.

__Parameters__

- __tags (dict)__: Mapping of tag names to values (or `None`).

<h2 id="requires.AWSRequires.request_subnet_tags">request_subnet_tags</h2>

```python
AWSRequires.request_subnet_tags(self, tags)
```

Request that the given tags be applied to all of this instance's
subnets.

__Parameters__

- __tags (dict)__: Mapping of tag names to values (or `None`).

