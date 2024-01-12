# SPDX-License-Identifier: Apache-2.0

LOADBALANCER_PLAYBOOKS = [
    "loadbalancer-aodh",
    "loadbalancer-barbican",
    "loadbalancer-cinder",
    "loadbalancer-designate",
    "loadbalancer-elasticsearch",
    "loadbalancer-glance",
    "loadbalancer-gnocchi",
    "loadbalancer-grafana",
    "loadbalancer-heat",
    "loadbalancer-horizon",
    "loadbalancer-ironic",
    "loadbalancer-keystone",
    "loadbalancer-kibana",
    "loadbalancer-manila",
    "loadbalancer-mariadb",
    "loadbalancer-memcached",
    "loadbalancer-neutron",
    "loadbalancer-nova",
    "loadbalancer-octavia",
    "loadbalancer-opensearch",
    "loadbalancer-placement",
    "loadbalancer-prometheus",
    "loadbalancer-rabbitmq",
    "loadbalancer-skydive",
]

VALIDATE_PLAYBOOKS = {
    "barbican-config": {
        "runtime": "kolla-ansible",
        "playbook": "barbican",
    },
    "designate-config": {
        "runtime": "kolla-ansible",
        "playbook": "designate",
    },
    "keystone-config": {
        "runtime": "kolla-ansible",
        "playbook": "keystone",
    },
    "glance-config": {
        "runtime": "kolla-ansible",
        "playbook": "glance",
    },
    "heat-config": {
        "runtime": "kolla-ansible",
        "playbook": "heat",
    },
    "octavia-config": {
        "runtime": "kolla-ansible",
        "playbook": "octavia",
    },
    "nova-config": {
        "runtime": "kolla-ansible",
        "playbook": "nova",
    },
    "neutron-config": {
        "runtime": "kolla-ansible",
        "playbook": "neutron",
    },
    "placement-config": {
        "runtime": "kolla-ansible",
        "playbook": "placement",
    },
    "aodh-config": {
        "runtime": "kolla-ansible",
        "playbook": "aodh",
    },
    "ceilometer-config": {
        "runtime": "kolla-ansible",
        "playbook": "ceilometer",
    },
    "cloudkitty-config": {
        "runtime": "kolla-ansible",
        "playbook": "cloudkitty",
    },
    "ironic-config": {
        "runtime": "kolla-ansible",
        "playbook": "ironic",
    },
    "manila-config": {
        "runtime": "kolla-ansible",
        "playbook": "manila",
    },
    "senlin-config": {
        "runtime": "kolla-ansible",
        "playbook": "senlin",
    },
    # NOTE: The command should be "osism validate ceph-config". However,
    # the corresponding playbook is called ceph-validate because ceph-config
    # deploys the Ceph configuration itself. So this is rewritten from
    # ceph-config to ceph-validate.
    "ceph-config": {
        "runtime": "ceph-ansible",
        "playbook": "validate",
    },
    # NOTE: The playbooks for validating the Ceph deployment are currently
    # in osism/ansible-playbooks. Therefore, they are not executed in
    # ceph-ansible but in osism-ansible.
    "ceph-mgrs": {"environment": "ceph", "runtime": "osism-ansible"},
    "ceph-mons": {"environment": "ceph", "runtime": "osism-ansible"},
    "ceph-osds": {"environment": "ceph", "runtime": "osism-ansible"},
    "container-status": {"environment": "generic", "runtime": "osism-ansible"},
    "kernel-version": {"environment": "generic", "runtime": "osism-ansible"},
    "mysql-open-files-limit": {"environment": "generic", "runtime": "osism-ansible"},
    "refstack": {"environment": "openstack", "runtime": "osism-ansible"},
    "system-encoding": {"environment": "generic", "runtime": "osism-ansible"},
    "ulimits": {"environment": "generic", "runtime": "osism-ansible"},
}

MAP_ROLE2ROLE = {
    "infrastructure": [
        "openstackclient",
        "common",
        "loadbalancer",
        "opensearch",
        "openvswitch",
        "ovn",
        "memcached",
        "redis",
        "mariadb",
        "rabbitmq",
        "phpmyadmin",
    ],
    "kubernetes": [
        "k3s",
        "kubectl",
        "kubeconfig",
    ],
    "openstack": [
        "keystone",
        "horizon",
        "placement",
        "glance",
        "cinder",
        "neutron",
        "nova",
        "barbican",
        "designate",
        "octavia",
    ],
    "ceph": [
        "ceph",
        "copy-ceph-keys",
        "cephclient",
        "ceph-bootstrap-dashboard",
    ],
}
