# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
import io
import json
import unittest.mock as mock
from urllib.error import URLError
from urllib.parse import urljoin
from pathlib import Path

import pytest
import yaml
import ops
import ops.testing
from ops.interface_aws.requires import (
    AWSIntegrationError,
    AWSIntegrationRequires,
    _metadata,
    _METADATA_URL,
    _METADATAV2_TOKEN_URL,
    _INSTANCE_ID_URL,
    _AZ_URL,
)


class MyCharm(ops.CharmBase):
    aws_meta = ops.RelationMeta(
        ops.RelationRole.requires, "aws", {"interface": "aws-integration"}
    )

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        self.aws = AWSIntegrationRequires(self)


@pytest.fixture(scope="function")
def harness():
    harness = ops.testing.Harness(MyCharm)
    harness.framework.meta.relations = {
        MyCharm.aws_meta.relation_name: MyCharm.aws_meta
    }
    harness.set_model_name("test/0")
    harness.begin_with_initial_hooks()
    yield harness


@pytest.fixture(autouse=True)
def mock_url():
    with mock.patch("ops.interface_aws.requires.urlopen") as urlopen:

        def urlopener(req):
            if req.full_url == _METADATAV2_TOKEN_URL:
                return io.BytesIO(b"faux-token")
            elif req.full_url == _INSTANCE_ID_URL:
                return io.BytesIO(b"i-abcdefghijklmnopq")
            elif req.full_url == _AZ_URL:
                return io.BytesIO(b"us-east1")
            else:
                raise URLError("Test Framework")

        urlopen.side_effect = urlopener
        yield urlopen


@pytest.fixture()
def sent_data():
    yield yaml.safe_load(Path("tests/data/aws_sent.yaml").open())


@pytest.fixture()
def recv_data():
    yield yaml.safe_load(Path("tests/data/aws_recv.yaml").open())


@pytest.mark.usefixtures("mock_url")
def test_metadata_fail():
    with pytest.raises(AWSIntegrationError):
        _metadata(urljoin(_METADATA_URL, "/invalid/address"))


@pytest.mark.parametrize(
    "event_type", [None, ops.RelationBrokenEvent], ids=["unrelated", "dropped relation"]
)
def test_is_ready_no_relation(harness, event_type):
    event = ops.ConfigChangedEvent(None)
    assert harness.charm.aws.is_ready is False
    assert "Missing" in harness.charm.aws.evaluate_relation(event)

    rel_id = harness.add_relation("aws", "remote")
    assert harness.charm.aws.is_ready is False

    rel = harness.model.get_relation("aws", rel_id)
    harness.add_relation_unit(rel_id, "remote/0")
    event = ops.RelationJoinedEvent(None, rel)
    assert "Waiting" in harness.charm.aws.evaluate_relation(event)

    event = ops.RelationChangedEvent(None, rel)
    harness.update_relation_data(rel_id, "remote/0", {"completed": "{}"})
    assert "Waiting" in harness.charm.aws.evaluate_relation(event)

    if event_type:
        harness.remove_relation(rel_id)
        event = event_type(None, rel)
        assert "Missing" in harness.charm.aws.evaluate_relation(event)


def test_is_ready_success(harness, recv_data):
    harness.add_relation("aws", "remote", unit_data=recv_data)
    assert harness.charm.aws.is_ready is True
    event = ops.ConfigChangedEvent(None)
    assert harness.charm.aws.evaluate_relation(event) is None


@pytest.mark.parametrize(
    "method_name, args",
    [
        (
            "tag_instance",
            'tags={"k8s.io/role/control-plane": "true", "kubernetes.io/cluster/kubernetes-generated-cluster-name": "owned"}',
        ),
        (
            "tag_instance_security_group",
            'tags={"kubernetes.io/cluster/kubernetes-generated-cluster-name": "owned"}',
        ),
        (
            "tag_instance_subnet",
            'tags={"kubernetes.io/cluster/kubernetes-generated-cluster-name": "owned"}',
        ),
        ("enable_acm_readonly", None),
        ("enable_acm_fullaccess", None),
        ("enable_autoscaling_readonly", None),
        ("enable_instance_inspection", None),
        ("enable_instance_modification", None),
        ("enable_network_management", None),
        ("enable_load_balancer_management", None),
        ("enable_block_storage_management", None),
        ("enable_dns_management", None),
        ("enable_region_readonly", None),
    ],
)
def test_request_simple(harness, method_name, args, sent_data):
    rel_id = harness.add_relation("aws", "remote")
    method = getattr(harness.charm.aws, method_name)
    kwargs = {}
    if args:
        kw, val = args.split("=")
        kwargs[kw] = json.loads(val)
    method(**kwargs)
    data = harness.get_relation_data(rel_id, harness.charm.unit.name)
    for each, value in data.items():
        assert sent_data[each] == value


def test_request_object_storage(harness, sent_data):
    rel_id = harness.add_relation("aws", "remote")
    patterns = ["auto-prefixed", "arn:aws:s3:::already-prefixed"]
    harness.charm.aws.enable_object_storage_access(patterns)
    harness.charm.aws.enable_object_storage_management(patterns)
    data = harness.get_relation_data(rel_id, harness.charm.unit.name)
    for each, value in data.items():
        assert sent_data[each] == value
