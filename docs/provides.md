<a id="provides"></a>

# provides

This is the provides side of the interface layer, for use only by the AWS
integrator charm itself.

The flags that are set by the provides side of this interface are:

* **`endpoint.{endpoint_name}.requested`** This flag is set when there is
  a new or updated request by a remote unit for AWS integration features.
  The AWS integration charm should then iterate over each request, perform
  whatever actions are necessary to satisfy those requests, and then mark
  them as complete.

<a id="provides.AWSIntegrationProvides"></a>

## AWSIntegrationProvides Objects

```python
class AWSIntegrationProvides(Endpoint)
```

Example usage:

```python
from charms.reactive import when, endpoint_from_flag
from charms import layer

@when('endpoint.aws.requested')
def handle_requests():
    aws = endpoint_from_flag('endpoint.aws.requested')
    for request in aws.requests:
        if request.instance_tags:
            tag_instance(
                request.instance_id,
                request.region,
                request.instance_tags)
        if request.requested_load_balancer_management:
            layer.aws.enable_load_balancer_management(
                request.application_name,
                request.instance_id,
                request.region,
            )
        # ...
        request.mark_completed()
```

<a id="provides.AWSIntegrationProvides.requests"></a>

#### requests

```python
@property
def requests()
```

A list of the new or updated [`IntegrationRequest`](#provides.IntegrationRequest) objects that
have been made.

<a id="provides.AWSIntegrationProvides.all_requests"></a>

#### all\_requests

```python
@property
def all_requests()
```

A list of all the [`IntegrationRequest`](#provides.IntegrationRequest) objects that have been made,
even if unchanged.

<a id="provides.AWSIntegrationProvides.application_names"></a>

#### application\_names

```python
@property
def application_names()
```

Set of names of all applications that are still joined.

<a id="provides.AWSIntegrationProvides.unit_instances"></a>

#### unit\_instances

```python
@property
def unit_instances()
```

Mapping of unit names to instance IDs and regions for all joined units.

<a id="provides.IntegrationRequest"></a>

## IntegrationRequest Objects

```python
class IntegrationRequest()
```

A request for integration from a single remote unit.

<a id="provides.IntegrationRequest.hash"></a>

#### hash

```python
@property
def hash()
```

SHA hash of the data for this request.

<a id="provides.IntegrationRequest.changed"></a>

#### changed

```python
@property
def changed()
```

Whether this request has changed since the last time it was
marked completed.

<a id="provides.IntegrationRequest.mark_completed"></a>

#### mark\_completed

```python
def mark_completed()
```

Mark this request as having been completed.

<a id="provides.IntegrationRequest.clear"></a>

#### clear

```python
def clear()
```

Clear this request's cached data.

<a id="provides.IntegrationRequest.unit_name"></a>

#### unit\_name

```python
@property
def unit_name()
```

The name of the unit making the request.

<a id="provides.IntegrationRequest.application_name"></a>

#### application\_name

```python
@property
def application_name()
```

The name of the application making the request.

<a id="provides.IntegrationRequest.instance_id"></a>

#### instance\_id

```python
@property
def instance_id()
```

The instance ID reported for this request.

<a id="provides.IntegrationRequest.region"></a>

#### region

```python
@property
def region()
```

The region reported for this request.

<a id="provides.IntegrationRequest.instance_tags"></a>

#### instance\_tags

```python
@property
def instance_tags()
```

Mapping of tag names to values (or `None`) to apply to this instance.

<a id="provides.IntegrationRequest.instance_security_group_tags"></a>

#### instance\_security\_group\_tags

```python
@property
def instance_security_group_tags()
```

Mapping of tag names to values (or `None`) to apply to this instance's
machine-specific security group (firewall).

<a id="provides.IntegrationRequest.instance_subnet_tags"></a>

#### instance\_subnet\_tags

```python
@property
def instance_subnet_tags()
```

Mapping of tag names to values (or `None`) to apply to this instance's
subnet.

<a id="provides.IntegrationRequest.requested_instance_inspection"></a>

#### requested\_instance\_inspection

```python
@property
def requested_instance_inspection()
```

Flag indicating whether the ability to inspect instances was requested.

<a id="provides.IntegrationRequest.requested_acm_readonly"></a>

#### requested\_acm\_readonly

```python
@property
def requested_acm_readonly()
```

Flag indicating whether acm readonly was requested.

<a id="provides.IntegrationRequest.requested_acm_fullaccess"></a>

#### requested\_acm\_fullaccess

```python
@property
def requested_acm_fullaccess()
```

Flag indicating whether acm fullaccess was requested.

<a id="provides.IntegrationRequest.requested_network_management"></a>

#### requested\_network\_management

```python
@property
def requested_network_management()
```

Flag indicating whether the ability to manage networking (firewalls,
subnets, etc) was requested.

<a id="provides.IntegrationRequest.requested_load_balancer_management"></a>

#### requested\_load\_balancer\_management

```python
@property
def requested_load_balancer_management()
```

Flag indicating whether load balancer management was requested.

<a id="provides.IntegrationRequest.requested_block_storage_management"></a>

#### requested\_block\_storage\_management

```python
@property
def requested_block_storage_management()
```

Flag indicating whether block storage management was requested.

<a id="provides.IntegrationRequest.requested_dns_management"></a>

#### requested\_dns\_management

```python
@property
def requested_dns_management()
```

Flag indicating whether DNS management was requested.

<a id="provides.IntegrationRequest.requested_object_storage_access"></a>

#### requested\_object\_storage\_access

```python
@property
def requested_object_storage_access()
```

Flag indicating whether object storage access was requested.

<a id="provides.IntegrationRequest.object_storage_access_patterns"></a>

#### object\_storage\_access\_patterns

```python
@property
def object_storage_access_patterns()
```

List of patterns to which to restrict object storage access.

<a id="provides.IntegrationRequest.requested_object_storage_management"></a>

#### requested\_object\_storage\_management

```python
@property
def requested_object_storage_management()
```

Flag indicating whether object storage management was requested.

<a id="provides.IntegrationRequest.object_storage_management_patterns"></a>

#### object\_storage\_management\_patterns

```python
@property
def object_storage_management_patterns()
```

List of patterns to which to restrict object storage management.

