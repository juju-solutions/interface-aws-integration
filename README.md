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

<h2 id="requires.AWSRequires">AWSRequires</h2>

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

<h3 id="requires.AWSRequires.enable_route53">enable_route53</h3>

```python
AWSRequires.enable_route53(self)
```

Request that Route53 integration be enabled for this instance.

<h3 id="requires.AWSRequires.enable_ebs">enable_ebs</h3>

```python
AWSRequires.enable_ebs(self)
```

Request that EBS integration be enabled for this instance.

<h3 id="requires.AWSRequires.request_security_group_tags">request_security_group_tags</h3>

```python
AWSRequires.request_security_group_tags(self, tags)
```

Request that the given tags be applied to all of this instance's
security groups.

__Parameters__

- __tags (dict)__: Mapping of tag names to values (or `None`).

<h3 id="requires.AWSRequires.enable_s3_write">enable_s3_write</h3>

```python
AWSRequires.enable_s3_write(self)
```

Request that S3 read/write integration be enabled for this instance.

<h3 id="requires.AWSRequires.request_subnet_tags">request_subnet_tags</h3>

```python
AWSRequires.request_subnet_tags(self, tags)
```

Request that the given tags be applied to all of this instance's
subnets.

__Parameters__

- __tags (dict)__: Mapping of tag names to values (or `None`).

<h3 id="requires.AWSRequires.request_instance_tags">request_instance_tags</h3>

```python
AWSRequires.request_instance_tags(self, tags)
```

Request that the given tags be applied to this instance.

__Parameters__

- __tags (dict)__: Mapping of tag names to values (or `None`).

<h3 id="requires.AWSRequires.enable_elb">enable_elb</h3>

```python
AWSRequires.enable_elb(self)
```

Request that ELB integration be enabled for this instance.

<h3 id="requires.AWSRequires.enable_s3_read">enable_s3_read</h3>

```python
AWSRequires.enable_s3_read(self)
```

Request that S3 read-only integration be enabled for this instance.

<h1 id="provides">provides</h1>


This is the provides side of the interface layer, for use only by the AWS
integration charm itself.

The flags that are set by the provides side of this interface are:

* **`endpoint.{endpoint_name}.requested`** This flag is set when there is
  a new or updated request by a remote unit for AWS integration features.
  The AWS integration charm should then iterate over each request, perform
  whatever actions are necessary to satisfy those requests, and then mark
  them as complete.

<h2 id="provides.AWSProvides">AWSProvides</h2>

```python
AWSProvides(self, endpoint_name, relation_ids=None)
```

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

<h3 id="provides.AWSProvides.requests">requests</h3>


A list of the new or updated `IntegrationRequests` that
have been made.

<h2 id="provides.IntegrationRequest">IntegrationRequest</h2>

```python
IntegrationRequest(self, unit)
```

A request for integration from a single remote unit.

<h3 id="provides.IntegrationRequest.mark_completed">mark_completed</h3>

```python
IntegrationRequest.mark_completed(self)
```

Mark this request as having been completed.

<h3 id="provides.IntegrationRequest.instance_id">instance_id</h3>


The instance ID reported for this request.

<h3 id="provides.IntegrationRequest.requested_route53">requested_route53</h3>


Flag indicating whether Route53 integration was requested.

<h3 id="provides.IntegrationRequest.requested_ebs">requested_ebs</h3>


Flag indicating whether EBS integration was requested.

<h3 id="provides.IntegrationRequest.requested_elb">requested_elb</h3>


Flag indicating whether ELB integration was requested.

<h3 id="provides.IntegrationRequest.changed">changed</h3>


Whether this request has changed since the last time it was
marked completed.

<h3 id="provides.IntegrationRequest.security_group_tags">security_group_tags</h3>


Mapping of tag names to values (or `None`) to apply to all of this
instance's security groups.

<h3 id="provides.IntegrationRequest.hash">hash</h3>


SHA hash of the data for this request.

<h3 id="provides.IntegrationRequest.requested_s3_read">requested_s3_read</h3>


Flag indicating whether S3 read-only integration was requested.

<h3 id="provides.IntegrationRequest.requested_s3_write">requested_s3_write</h3>


Flag indicating whether S3 read/write integration was requested.

<h3 id="provides.IntegrationRequest.instance_tags">instance_tags</h3>


Mapping of tag names to values (or `None`) to apply to this instance.

<h3 id="provides.IntegrationRequest.subnet_tags">subnet_tags</h3>


Mapping of tag names to values (or `None`) to apply to all of this
instance's subnets.

