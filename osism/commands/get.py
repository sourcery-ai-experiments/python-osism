from datetime import datetime
import pprint
import subprocess

from celery import Celery
from cliff.command import Command
import docker
import json
from loguru import logger
from tabulate import tabulate

from osism.tasks import Config
from osism.utils import redis


class VersionsManager(Command):
    def get_parser(self, prog_name):
        parser = super(VersionsManager, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        client = docker.from_env()

        data = []

        for cname in ["osism-ansible", "ceph-ansible", "kolla-ansible"]:
            try:
                container = client.containers.get(cname)
                version = container.labels["org.opencontainers.image.version"]

                if cname == "ceph-ansible":
                    mrelease = container.labels["de.osism.release.ceph"]
                elif cname == "kolla-ansible":
                    mrelease = container.labels["de.osism.release.openstack"]
                else:
                    mrelease = ""

                data.append([cname, version, mrelease])
            except docker.errors.NotFound:
                pass

        result = tabulate(
            data, headers=["Module", "OSISM version", "Module release"], tablefmt="psql"
        )
        print(result)


class Tasks(Command):
    def get_parser(self, prog_name):
        parser = super(Tasks, self).get_parser(prog_name)
        parser.add_argument(
            "--status", default="all", help="Status of the tasks to list"
        )
        return parser

    def take_action(self, parsed_args):
        status = parsed_args.status

        app = Celery("task")
        app.config_from_object(Config)

        i = app.control.inspect()

        table = []

        task_status = "ACTIVE"
        for worker, tasks in i.active().items():
            for task in tasks:
                time_start = datetime.fromtimestamp(task["time_start"])
                table.append(
                    [
                        worker,
                        task["id"],
                        task["name"],
                        task_status,
                        time_start,
                        task["args"],
                    ]
                )

        task_status = "SCHEDULED"
        for worker, tasks in i.scheduled().items():
            for task in tasks:
                time_start = datetime.fromtimestamp(task["time_start"])
                table.append(
                    [
                        worker,
                        task["id"],
                        task["name"],
                        task_status,
                        time_start,
                        task["args"],
                    ]
                )

        print(
            tabulate(
                table,
                headers=["Worker", "ID", "Name", "Status", "Start time", "Arguments"],
                tablefmt="psql",
            )
        )


class Hostvars(Command):
    def get_parser(self, prog_name):
        parser = super(Hostvars, self).get_parser(prog_name)
        parser.add_argument(
            "host",
            nargs=1,
            type=str,
            help="Hostname (as the host is known in Ansible inventory)",
        )
        parser.add_argument(
            "variable",
            nargs="?",
            type=str,
            help="Name of a variable to show",
        )
        return parser

    def take_action(self, parsed_args):
        host = parsed_args.host[0]
        variable = parsed_args.variable

        try:
            result = subprocess.check_output(
                f"ansible-inventory -i /ansible/inventory/hosts.yml --host {host}",
                shell=True,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            logger.error(f"Host {host} not found in inventory.")
            return

        data = json.loads(result)
        table = []

        if variable:
            if variable in data:
                row = pprint.pformat(data[variable], indent=2, width=60, compact=True)
                table.append([host, variable, row])
            else:
                logger.error(f"Variable {variable} not found in inventory for {host}.")
        else:
            for variable in data:
                row = pprint.pformat(data[variable], indent=2, width=60, compact=True)
                table.append([host, variable, row])

        if table:
            print(
                tabulate(table, headers=["Host", "Variable", "Value"], tablefmt="grid")
            )

        return


class Facts(Command):
    def get_parser(self, prog_name):
        parser = super(Facts, self).get_parser(prog_name)
        parser.add_argument(
            "host",
            nargs=1,
            type=str,
            help="Hostname (as the host is known in Ansible inventory)",
        )
        parser.add_argument(
            "fact",
            nargs="?",
            type=str,
            help="Name of a fact to show",
        )
        parser.add_argument(
            "--no-cache",
            default=False,
            help="Do not use facts from the cache",
            action="store_true",
        )
        return parser

    def take_action(self, parsed_args):
        host = parsed_args.host[0]
        fact = parsed_args.fact
        cache = not parsed_args.no_cache

        data = redis.get(f"ansible_facts{host}")
        if data:
            data = json.loads(data)
            table = []

            if fact:
                if fact in data:
                    row = pprint.pformat(data[fact], indent=2, width=60, compact=True)
                    table.append([host, fact, row])
                else:
                    logger.error(f"Fact {fact} not found in cache for {host}.")
            else:
                for fact in data:
                    row = pprint.pformat(data[fact], indent=2, width=60, compact=True)
                    if fact in [
                        "ansible_ssh_host_key_dsa_public",
                        "ansible_ssh_host_key_ecdsa_public",
                        "ansible_ssh_host_key_ed25519_public",
                        "ansible_ssh_host_key_rsa_public",
                    ]:
                        row = f"{row[0:40]}..."
                    table.append([host, fact, row])

            if table:
                print(
                    tabulate(table, headers=["Host", "Fact", "Value"], tablefmt="grid")
                )
        else:
            logger.error(f"No facts found in cache for {host}.")

        return


class Hosts(Command):
    def get_parser(self, prog_name):
        parser = super(Hosts, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        try:
            result = subprocess.check_output(
                f"ansible-inventory -i /ansible/inventory/hosts.yml --list",
                shell=True,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            logger.error(f"Error loading inventory.")
            return

        data = json.loads(result)
        table = []

        for host in data["_meta"]["hostvars"]:
            table.append([host])

        if table:
            print(
                tabulate(table, headers=["Host"], tablefmt="psql")
            )

        return