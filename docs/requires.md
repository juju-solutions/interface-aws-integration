<a id="requires"></a>

# requires

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

<a id="requires.AWSIntegrationRequires"></a>

## AWSIntegrationRequires Objects

```python
class AWSIntegrationRequires(Endpoint)
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
    aws.request_load_balancer_management()
    # ...

@when('endpoint.aws.ready')
def aws_integration_ready():
    update_config_enable_aws()
```

<a id="requires.AWSIntegrationRequires.instance_id"></a>

#### instance\_id

```python
@property
def instance_id()
```

This unit's instance-id.

<a id="requires.AWSIntegrationRequires.region"></a>

#### region

```python
@property
def region()
```

The region this unit is in.

<a id="requires.AWSIntegrationRequires.tag_instance"></a>

#### tag\_instance

```python
def tag_instance(tags)
```

Request that the given tags be applied to this instance.

__Parameters__

- __`tags` (dict)__: Mapping of tag names to values (or `None`).

<a id="requires.AWSIntegrationRequires.tag_instance_security_group"></a>

#### tag\_instance\_security\_group

```python
def tag_instance_security_group(tags)
```

Request that the given tags be applied to this instance's
machine-specific security group (firewall) created by Juju.

__Parameters__

- __`tags` (dict)__: Mapping of tag names to values (or `None`).

<a id="requires.AWSIntegrationRequires.tag_instance_subnet"></a>

#### tag\_instance\_subnet

```python
def tag_instance_subnet(tags)
```

Request that the given tags be applied to this instance's subnet.

__Parameters__

- __`tags` (dict)__: Mapping of tag names to values (or `None`).

<a id="requires.AWSIntegrationRequires.enable_acm_readonly"></a>

#### enable\_acm\_readonly

```python
def enable_acm_readonly()
```

Request readonly for ACM.

<a id="requires.AWSIntegrationRequires.enable_acm_fullaccess"></a>

#### enable\_acm\_fullaccess

```python
def enable_acm_fullaccess()
```

Request fullaccess for ACM.

<a id="requires.AWSIntegrationRequires.enable_instance_inspection"></a>

#### enable\_instance\_inspection

```python
def enable_instance_inspection()
```

Request the ability to inspect instances.

<a id="requires.AWSIntegrationRequires.enable_network_management"></a>

#### enable\_network\_management

```python
def enable_network_management()
```

Request the ability to manage networking (firewalls, subnets, etc).

<a id="requires.AWSIntegrationRequires.enable_load_balancer_management"></a>

#### enable\_load\_balancer\_management

```python
def enable_load_balancer_management()
```

Request the ability to manage load balancers.

<a id="requires.AWSIntegrationRequires.enable_block_storage_management"></a>

#### enable\_block\_storage\_management

```python
def enable_block_storage_management()
```

Request the ability to manage block storage.

<a id="requires.AWSIntegrationRequires.enable_dns_management"></a>

#### enable\_dns\_management

```python
def enable_dns_management()
```

Request the ability to manage DNS.

<a id="requires.AWSIntegrationRequires.enable_object_storage_access"></a>

#### enable\_object\_storage\_access

```python
def enable_object_storage_access(patterns=None)
```

Request the ability to access object storage.

__Parameters__

- __`patterns` (list)__: If given, restrict access to the resources matching
    the patterns. If patterns do not start with the S3 ARN prefix
- __(`arn__:aws:s3:::`), it will be prepended.

<a id="requires.AWSIntegrationRequires.enable_object_storage_management"></a>

#### enable\_object\_storage\_management

```python
def enable_object_storage_management(patterns=None)
```

Request the ability to manage object storage.

__Parameters__

- __`patterns` (list)__: If given, restrict management to the resources
    matching the patterns. If patterns do not start with the S3 ARN
- __prefix (`arn__:aws:s3:::`), it will be prepended.

