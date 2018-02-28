<h1 id="provides">provides</h1>


This is the provides side of the interface layer, for use only by the AWS
integration charm itself.

The flags that are set by the provides side of this interface are:

* **`endpoint.{endpoint_name}.requested`** This flag is set when there is
  a new or updated request by a remote unit for AWS integration features.
  The AWS integration charm should then iterate over each request, perform
  whatever actions are necessary to satisfy those requests, and then mark
  them as complete.

<h1 id="provides.AWSProvides">AWSProvides</h1>

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

<h2 id="provides.AWSProvides.requests">requests</h2>


A list of the new or updated `IntegrationRequests` that
have been made.

<h1 id="provides.IntegrationRequest">IntegrationRequest</h1>

```python
IntegrationRequest(self, unit)
```

A request for integration from a single remote unit.

<h2 id="provides.IntegrationRequest.hash">hash</h2>


SHA hash of the data for this request.

<h2 id="provides.IntegrationRequest.instance_id">instance_id</h2>


The instance ID reported for this request.

<h2 id="provides.IntegrationRequest.requested_ebs">requested_ebs</h2>


Flag indicating whether EBS integration was requested.

<h2 id="provides.IntegrationRequest.requested_s3_read">requested_s3_read</h2>


Flag indicating whether S3 read-only integration was requested.

<h2 id="provides.IntegrationRequest.instance_tags">instance_tags</h2>


Mapping of tag names to values (or `None`) to apply to this instance.

<h2 id="provides.IntegrationRequest.requested_route53">requested_route53</h2>


Flag indicating whether Route53 integration was requested.

<h2 id="provides.IntegrationRequest.subnet_tags">subnet_tags</h2>


Mapping of tag names to values (or `None`) to apply to all of this
instance's subnets.

<h2 id="provides.IntegrationRequest.requested_s3_write">requested_s3_write</h2>


Flag indicating whether S3 read/write integration was requested.

<h2 id="provides.IntegrationRequest.mark_completed">mark_completed</h2>

```python
IntegrationRequest.mark_completed(self)
```

Mark this request as having been completed.

<h2 id="provides.IntegrationRequest.requested_elb">requested_elb</h2>


Flag indicating whether ELB integration was requested.

<h2 id="provides.IntegrationRequest.changed">changed</h2>


Whether this request has changed since the last time it was
marked completed.

<h2 id="provides.IntegrationRequest.security_group_tags">security_group_tags</h2>


Mapping of tag names to values (or `None`) to apply to all of this
instance's security groups.

