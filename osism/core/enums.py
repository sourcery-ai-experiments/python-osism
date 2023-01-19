LOADBALANCER_PLAYBOOKS = [
    "loadbalancer-aodh",
    "loadbalancer-barbican",
    # "loadbalancer-blazar",
    # "loadbalancer-ceph-rgw",
    "loadbalancer-cinder",
    # "loadbalancer-cloudkitty",
    # "loadbalancer-cyborg",
    "loadbalancer-designate",
    "loadbalancer-elasticsearch",
    # "loadbalancer-freezer",
    "loadbalancer-glance",
    "loadbalancer-gnocchi",
    "loadbalancer-grafana",
    "loadbalancer-heat",
    "loadbalancer-horizon",
    # "loadbalancer-influxdb",
    "loadbalancer-ironic",
    "loadbalancer-keystone",
    "loadbalancer-kibana",
    # "loadbalancer-magnum",
    "loadbalancer-manila",
    "loadbalancer-mariadb",
    # "loadbalancer-masakari",
    "loadbalancer-memcached",
    # "loadbalancer-mistral",
    # "loadbalancer-monasca",
    # "loadbalancer-murano",
    "loadbalancer-neutron",
    "loadbalancer-nova",
    "loadbalancer-octavia",
    "loadbalancer-placement",
    "loadbalancer-prometheus",
    "loadbalancer-rabbitmq",
    # "loadbalancer-sahara",
    # "loadbalancer-senlin",
    "loadbalancer-skydive",
    # "loadbalancer-solum",
    # "loadbalancer-swift",
    # "loadbalancer-tacker",
    # "loadbalancer-trove",
    # "loadbalancer-vitrage",
    # "loadbalancer-watcher",
    # "loadbalancer-zun",
]

VALIDATE_PLAYBOOKS = {
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
    "system-encoding": {"environment": "generic", "runtime": "osism-ansible"},
    "ulimits": {"environment": "generic", "runtime": "osism-ansible"},
}

MAP_ROLE2ROLE = {
    "ceph-basic": [
        "ceph-infra",
        "ceph-mons",
        "ceph-mgrs",
        "ceph-osds",
        "ceph-crash",
    ],
    "infrastructure-basic": [
        "openstackclient",
        "common",
        "loadbalancer",
        "elasticsearch",
        "kibana",
        "openvswitch",
        "memcached",
        "redis",
        "mariadb",
        "rabbitmq",
        "phpmyadmin",
    ],
    "openstack-basic": [
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
    "openstack-extended": ["gnocchi", "ceilometer", "aodh", "senlin"],
}

MAP_ROLE2ENVIRONMENT = {
    # MONITORING
    "netdata": "monitoring",
    "remove-netdata": "monitoring",
    "remove-zabbix-agent": "monitoring",
    "openstack-health-monitor": "monitoring",
    # GENERIC
    "auditd": "generic",
    "backup-mariadb": "generic",
    "bootstrap": "generic",
    "check-reboot": "generic",
    "chrony": "generic",
    "chrony-force-sync": "generic",
    "clamav": "generic",
    "cleanup": "generic",
    "cleanup-backup-mariadb": "generic",
    "cleanup-databases": "generic",
    "cleanup-docker": "generic",
    "cleanup-docker-images": "generic",
    "cleanup-elasticsearch": "generic",
    "cleanup-queues": "generic",
    "cleanup-sosreport": "generic",
    "cockpit": "generic",
    "configfs": "generic",
    "docker": "generic",
    "docker-compose": "generic",
    "docker-login": "generic",
    "dotfiles": "generic",
    "dump-facts": "generic",
    "facts": "generic",
    "fail2ban": "generic",
    "falco": "generic",
    "firewall": "generic",
    "grub": "generic",
    "halt": "generic",
    "hardening": "generic",
    "hddtemp": "generic",
    "hostname": "generic",
    "hosts": "generic",
    "ipmitool": "generic",
    "journald": "generic",
    "kernel-modules": "generic",
    "known-hosts": "generic",
    "kompose": "generic",
    "lldpd": "generic",
    "lynis": "generic",
    "maintenance": "generic",
    "manage-container": "generic",
    "manage-service": "generic",
    "microcode": "generic",
    "motd": "generic",
    "network": "generic",
    "operator": "generic",
    "osquery": "generic",
    "packages": "generic",
    "patchman-client": "generic",
    "ping": "generic",
    "podman": "generic",
    "proxy": "generic",
    "python": "generic",
    "python3": "generic",
    "reboot": "generic",
    "remove-deploy-user": "generic",
    "repository": "generic",
    "resolvconf": "generic",
    "rng": "generic",
    "rsyslog": "generic",
    "services": "generic",
    "smartd": "generic",
    "sosreport": "generic",
    "state": "generic",
    "sysctl": "generic",
    "sysdig": "generic",
    "systohc": "generic",
    "timezone": "generic",
    "trivy": "generic",
    "upgrade-packages": "generic",
    "utilities": "generic",
    "wait-for-connection": "generic",
    "write-facts": "generic",
    # INFRASTRUCTURE
    "adminer": "infrastructure",
    "cephclient": "infrastructure",
    "cgit": "infrastructure",
    "clevis": "infrastructure",
    "dnsdist": "infrastructure",
    "helper": "infrastructure",
    "homer": "infrastructure",
    "jenkins": "infrastructure",
    "keycloak": "infrastructure",
    "kubectl": "infrastructure",
    "minikube": "infrastructure",
    "mirror": "infrastructure",
    "mirror-images": "infrastructure",
    "netbox": "infrastructure",
    "nexus": "infrastructure",
    "openldap": "infrastructure",
    "openstackclient": "infrastructure",
    "patchman": "infrastructure",
    "phpmyadmin": "infrastructure",
    "rundeck": "infrastructure",
    "squid": "infrastructure",
    "sshconfig": "infrastructure",
    "tailscale": "infrastructure",
    "tang": "infrastructure",
    "traefik": "infrastructure",
    "virtualbmc": "infrastructure",
    "wireguard": "infrastructure",
    "zuul": "infrastructure",
    # MANAGER
    "configuration": "manager",
    "copy-ceph-keys": "manager",
    "manager-network": "manager",
    "manager-operator": "manager",
    "vault-import": "manager",
    "vault-init": "manager",
    "vault-seal": "manager",
    "vault-unseal": "manager",
    # CEPH
    "ceph-add-mon": "ceph",
    "ceph-base": "ceph",
    "ceph-bootstrap-dashboard": "ceph",
    "ceph-ceph-keys": "ceph",
    "ceph-cephadm": "ceph",
    "ceph-cephadm-adopt": "ceph",
    "ceph-clients": "ceph",
    "ceph-config": "ceph",
    "ceph-crash": "ceph",
    "ceph-docker-to-podman": "ceph",
    "ceph-facts": "ceph",
    "ceph-fetch-keys": "ceph",
    "ceph-filestore-to-bluestore": "ceph",
    "ceph-gather-ceph-logs": "ceph",
    "ceph-infra": "ceph",
    "ceph-iscsigws": "ceph",
    "ceph-lv-create": "ceph",
    "ceph-lv-teardown": "ceph",
    "ceph-mdss": "ceph",
    "ceph-mgrs": "ceph",
    "ceph-mons": "ceph",
    "ceph-nfss": "ceph",
    "ceph-osds": "ceph",
    "ceph-purge-cluster": "ceph",
    "ceph-purge-storage-node": "ceph",
    "ceph-rbd-mirrors": "ceph",
    "ceph-restapis": "ceph",
    "ceph-rgw-add-users-buckets": "ceph",
    "ceph-rgws": "ceph",
    "ceph-rolling_update": "ceph",
    "ceph-shrink-mds": "ceph",
    "ceph-shrink-mgr": "ceph",
    "ceph-shrink-mon": "ceph",
    "ceph-shrink-osd": "ceph",
    "ceph-shrink-rbdmirror": "ceph",
    "ceph-shrink-rgw": "ceph",
    "ceph-site": "ceph",
    "ceph-storage-inventory": "ceph",
    "ceph-switch-from-non-containerized-to-containerized-ceph-daemons": "ceph",
    "ceph-take-over-existing-cluster": "ceph",
    # KOLLA
    "aodh": "kolla",
    "barbican": "kolla",
    "bifrost": "kolla",
    "bifrost-keypair": "kolla",
    # "blazar": "kolla",
    "ceilometer": "kolla",
    "certificates": "kolla",
    "chrony-cleanup": "kolla",
    "cinder": "kolla",
    "cloudkitty": "kolla",
    "collectd": "kolla",
    "common": "kolla",
    # "cyborg": "kolla",
    "designate": "kolla",
    "elasticsearch": "kolla",
    "etcd": "kolla",
    # "freezer": "kolla",
    "glance": "kolla",
    "gnocchi": "kolla",
    "grafana": "kolla",
    "hacluster": "kolla",
    "haproxy": "kolla",
    "heat": "kolla",
    "horizon": "kolla",
    # "influxdb": "kolla",
    "ironic": "kolla",
    "iscsi": "kolla",
    # "kafka": "kolla",
    "keystone": "kolla",
    "kibana": "kolla",
    "kolla-destroy": "kolla",
    "kolla-facts": "kolla",
    "kolla-gather-facts": "kolla",
    "kolla-prune-images": "kolla",
    "kolla-purge": "kolla",
    "kolla-rgw-endpoint": "kolla",
    "kolla-site": "kolla",
    "kolla-testbed": "kolla",
    "kolla-testbed-identity": "kolla",
    "kuryr": "kolla",
    "loadbalancer": "kolla",
    # "magnum": "kolla",
    "manila": "kolla",
    "mariadb": "kolla",
    "mariadb-dynamic-rows": "kolla",
    "mariadb_backup": "kolla",
    "mariadb_recovery": "kolla",
    # "masakari": "kolla",
    "memcached": "kolla",
    "mistral": "kolla",
    # "monasca": "kolla",
    # "monasca_cleanup": "kolla",
    "multipathd": "kolla",
    # "murano": "kolla",
    "neutron": "kolla",
    "nova": "kolla",
    "nova-compute": "kolla",
    "octavia": "kolla",
    "octavia-certificates": "kolla",
    "opensearch": "kolla",
    "openvswitch": "kolla",
    "ovn": "kolla",
    "ovn-controller": "kolla",
    "ovn-db": "kolla",
    "ovs-dpdk": "kolla",
    # "panko": "kolla",
    "placement": "kolla",
    "prechecks": "kolla",
    "prometheus": "kolla",
    # "qdrouterd": "kolla",
    "rabbitmq": "kolla",
    "rabbitmq-outward": "kolla",
    # "rally": "kolla",
    "redis": "kolla",
    # "sahara": "kolla",
    "senlin": "kolla",
    "skydive": "kolla",
    # "solum": "kolla",
    # "storm": "kolla",
    "swift": "kolla",
    # "tacker": "kolla",
    # "telegraf": "kolla",
    # "tempest": "kolla",
    "trove": "kolla",
    # "vitrage": "kolla",
    # "vmtp": "kolla",
    # "watcher": "kolla",
    # "zookeeper": "kolla",
    "zun": "kolla",
}
