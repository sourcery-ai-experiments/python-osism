# Copyright OSISM GmbH, 2022
# LICENSE: CC BY-NC 4.0

import glob
import logging
import os
import re
import sys

import pynetbox
from oslo_config import cfg
import yaml

import settings

PROJECT_NAME = 'connect'
CONF = cfg.CONF
opts = [
    cfg.BoolOpt('debug', help='Enable debug logging', default=False),
    cfg.BoolOpt('enforce', help='Enforce', default=False),
    cfg.StrOpt('state', help='State', default='a', required=False),
    cfg.StrOpt('collection', help='Collection', default=None, required=False),
    cfg.StrOpt('device', help='device', default=None, required=False)
]
CONF.register_cli_opts(opts)
CONF(sys.argv[1:], project=PROJECT_NAME)

if CONF.debug:
    level = logging.DEBUG
else:
    level = logging.INFO
logging.basicConfig(format='%(asctime)s - %(message)s', level=level, datefmt='%Y-%m-%d %H:%M:%S')

if not CONF.device:
    logging.info(f"Processing collection {CONF.collection}")

    data = {}

    if os.path.isfile("/netbox/{CONF.collection}/{CONF.state}.yaml"):
        with open(f"/netbox/{CONF.collection}/{CONF.state}.yaml") as fp:
            data = yaml.load(fp, Loader=yaml.SafeLoader)

    for directory in glob.glob(f"/netbox/{CONF.collection}/*/"):
        with open(f"{directory}{CONF.state}.yaml") as fp:
            data_a = yaml.load(fp, Loader=yaml.SafeLoader)
        # data = data | data_a
        data = {**data_a, **data}
elif CONF.device and CONF.collection:
    if not os.path.isfile("/netbox/{CONF.collection}/{CONF.device}/{CONF.state}.yaml"):
        logging.error(f"State {CONF.state} for device {CONF.device} in collection {CONF.collection} is not available")
        sys.exit(1)

    logging.info(f"Processing device {CONF.device} in collection {CONF.collection}")

    with open(f"/netbox/{CONF.collection}/{CONF.device}/{CONF.state}.yaml") as fp:
        data = yaml.load(fp, Loader=yaml.SafeLoader)
elif CONF.device:
    # Try to find the collection of the specified device
    # A device can be in exactly one collection
    result = [x[0] for x in os.walk("/netbox") if CONF.device in x[0]]
    if result:
        logging.info(f"Processing device {CONF.device}")

        try:
            with open(f"{result[0]}/{CONF.state}.yaml") as fp:
                data = yaml.load(fp, Loader=yaml.SafeLoader)
        except:
            logging.error(f"State {CONF.state} for device {CONF.device} is not available")
            sys.exit(1)
    else:
        logging.error(f"Device {CONF.device} is not defined in any collection")

else:
    logging.error("Specify at least a collection or a device")
    sys.exit(1)

nb = pynetbox.api(
    settings.NETBOX_URL,
    token=settings.NETBOX_TOKEN
)

if settings.IGNORE_SSL_ERRORS:
    import requests
    requests.packages.urllib3.disable_warnings()
    session = requests.Session()
    session.verify = False
    nb.http_session = session

# Get current device state
logging.info("Get current device state")
current_state = {}
for device in data:
    device_a = nb.dcim.devices.get(name=device)
    current_state[device] = device_a.custom_fields["device_state"]

# Mark interfaces that are part of a LAG
logging.info("Mark interfaces that are part of a LAG")
lag_interfaces = {}
for device in data:
    lag_interfaces[device] = []
    for interface in data[device]:
        if data[device][interface]["type"] == "port-channel":
            for interface in data[device][interface]["interfaces"]:
                if interface not in lag_interfaces[device]:
                    lag_interfaces[device].append(interface)

# Manage interfaces
logging.info("Manage interfaces")
for device in data:
    logging.info(f"Checking {device} for state {CONF.state}")

    if not CONF.enforce and current_state[device] == CONF.state:
        logging.info(f"Device {device} is already in state {CONF.state}")
        continue

    primary_address = None
    for interface in data[device]:

        if data[device][interface]["type"] in ["virtual", "port-channel", "mlag"]:
            continue

        device_a = nb.dcim.devices.get(name=device)
        device_target = data[device][interface]["device"]
        device_b = nb.dcim.devices.get(name=device_target)

        interface_a = nb.dcim.interfaces.get(name=interface, device=device)
        interface_b = nb.dcim.interfaces.get(name=data[device][interface]["interface"], device=data[device][interface]["device"])

        if "mac_address" in data[device][interface]:
            interface_a.mac_address = data[device][interface]["mac_address"]
            interface_a.save()
        elif interface_a.mac_address:
            interface_a.mac_address = None
            interface_a.save()

        # Add all addresses to the interface
        if "addresses" in data[device][interface]:
            for address in data[device][interface]["addresses"]:
                address_a = nb.ipam.ip_addresses.get(address=address)
                if type(address) == str:
                    address_a = nb.ipam.ip_addresses.get(address=address)
                    logging.info(f"Address {address} -> {interface}")
                    if not address_a:
                        nb.ipam.ip_addresses.create(
                            address=address,
                            assigned_object_type="dcim.interface",
                            assigned_object_id=interface_a.id
                        )
                else:
                    address_a = nb.ipam.ip_addresses.get(address=address["address"])
                    logging.info(f"Address {address['address']} -> {interface}")
                    if not address_a:
                        address_a = nb.ipam.ip_addresses.create(
                            assigned_object_type="dcim.interface",
                            assigned_object_id=interface_a.id,
                            **address
                        )
                    if "primary" in address and bool(address["primary"]):
                        primary_address = address_a.id
                        device_a.primary_ip4 = address_a.id
                        device_a.save()

        # Remove addresses from the interface that have been removed
        for address in nb.ipam.ip_addresses.filter(device=device, interface=interface):
            delete = True
            if "addresses" in data[device][interface]:
                for address_a in data[device][interface]["addresses"]:
                    if type(address_a) == str and address_a == str(address):
                        delete = False
                    elif "address" in address_a and address_a["address"] == str(address):
                        delete = False

            if delete:
                address.delete()

        logging.info(f"{interface_a} -> {device_target} # {interface_b}")

        # EthernetXX/Y
        if "Ethernet" in interface_a.name:
            port_a = interface_a.name[8:].split("/")[0]
        # etherXX
        elif "ether" in interface_a.name:
            port_a = interface_a.name[5:]
        else:
            port_a = interface_a.name

        # EthernetXX/Y
        if "Ethernet" in interface_b.name:
            port_b = interface_b.name[8:].split("/")[0]
        # etherXX
        elif "ether" in interface_b.name:
            port_b = interface_b.name[5:]
        else:
            port_b = interface_b.name

        near_end_a = f"{device_a.position}:{port_a}"
        if device_a.rack.name == device_b.rack.name:
            far_end_a = f"{device_b.position}:{port_b}"
        else:
            far_end_a = f"{device_b.rack.name}-{device_b.position}:{port_b}"
        label_a = f"{near_end_a} / {far_end_a}"

        near_end_b = f"{device_b.position}:{port_b}"
        if device_b.rack.name == device_a.rack.name:
            far_end_b = f"{device_a.position}:{port_a}"
        else:
            far_end_b = f"{device_a.rack.name}-{device_a.position}:{port_a}"
        label_b = f"{near_end_b} / {far_end_b}"

        interface_a.update({"label": label_a})
        interface_b.update({"label": label_b})

        connection = nb.dcim.cables.get(
            termination_a_type="dcim.interface",
            termination_b_type="dcim.interface",
            termination_a_id=interface_a.id,
            termination_b_id=interface_b.id
        )

        # NOTE: also check the other direction
        if not connection:
            connection = nb.dcim.cables.get(
                termination_a_type="dcim.interface",
                termination_b_type="dcim.interface",
                termination_a_id=interface_b.id,
                termination_b_id=interface_a.id
            )

        if not connection:
            try:
                connection = nb.dcim.cables.create(
                    termination_a_type="dcim.interface",
                    termination_b_type="dcim.interface",
                    termination_a_id=interface_a.id,
                    termination_b_id=interface_b.id,
                    type=data[device][interface]["type"]
                )
            except pynetbox.core.query.RequestError as e:
                logging.error(f"ERROR --> {e}")

        # ensure that all interfaces are enabled
        if not interface_a.enabled:
            interface_a.enabled = True
            interface_a.save()
            logging.info(f"{device_a} # {interface_a} --> enabled")

        if not interface_b.enabled:
            interface_b.enabled = True
            interface_b.save()
            logging.info(f"{device_b} # {interface_b} --> enabled")

        if "vlans" in data[device][interface]:
            tagged = False
            interface_a.untagged_vlan = None
            interface_a.tagged_vlans = []
            for vlan in data[device][interface]["vlans"]:
                vlan_a = nb.ipam.vlans.get(vid=vlan)
                if not vlan_a:
                    try:
                        vlan_a = nb.ipam.vlans.create(name=f"VLAN {vlan}", vid=vlan)
                    except pynetbox.core.query.RequestError as e:
                        logging.error(f"ERROR --> {e}")

                if data[device][interface]["vlans"][vlan] == "untagged":
                    logging.info(f"Untagged VLAN {vlan_a.vid} -> {interface_a.name}")
                    interface_a.untagged_vlan = vlan_a.id

                    if interface_a.name not in lag_interfaces[device]:
                        logging.info(f"Tagged VLAN {vlan_a.vid} -> {interface_b.name}")
                        interface_b.untagged_vlan = vlan_a.id

                elif vlan_a.id not in interface_a.tagged_vlans:
                    logging.info(f"Tagged VLAN {vlan_a.vid} -> {interface_a.name}")
                    interface_a.tagged_vlans.append(vlan_a.id)

                    if interface_a.name not in lag_interfaces[device]:
                        logging.info(f"Tagged VLAN {vlan_a.vid} -> {interface_b.name}")
                        interface_b.tagged_vlans.append(vlan_a.id)

                    tagged = True

            if tagged:
                interface_a.mode = 'tagged'

                if interface_a.name not in lag_interfaces[device]:
                    interface_b.mode = 'tagged'
            else:
                interface_a.mode = 'access'

                if interface_a.name not in lag_interfaces[device]:
                    interface_b.mode = 'access'

            interface_a.save()

            if interface_a.name not in lag_interfaces[device]:
                interface_b.save()

    # Remove the primary IP address if it is no longer set
    if not primary_address:
        device_a.primary_ip4 = None
        device_a.save()


# Manage port channels (not MLAGs)
logging.info("Manage port channels (not MLAGs)")
for device in data:

    if not CONF.enforce and current_state[device] == CONF.state:
        logging.info(f"Device {device} is already in state {CONF.state}")
        continue

    for interface in data[device]:
        if data[device][interface]["type"] == "port-channel":
            logging.info(f"Local port channel {device} # {interface} -> {data[device][interface]['interfaces']}")
            device_a = nb.dcim.devices.get(name=device)

            # Create the local port channel
            port_channel_a = nb.dcim.interfaces.get(name=interface, device=device)
            if not port_channel_a:
                try:
                    port_channel_a = nb.dcim.interfaces.create(name=interface, device=device_a.id, type="lag")
                except pynetbox.core.query.RequestError as e:
                    logging.error(f"ERROR --> {e}")

            # Create the remote port channels and add the local interfaces to the local port channel
            remote_port_channels = []
            for interface_x in data[device][interface]["interfaces"]:
                interface_a = nb.dcim.interfaces.get(name=interface_x, device=device)

                # NOTE: The VLANs on the Ethernet interfaces on the local devices are preserved for
                #       visibility in the Netbox.
                # interface_a.untagged_vlan = None
                # interface_a.tagged_vlans = []

                interface_a.lag = port_channel_a
                interface_a.save()

                port_channel_b_name = f"Port-Channel{data[device][interface]['channel']}"
                interface_b = nb.dcim.interfaces.get(name=interface_a.connected_endpoint.name, device=interface_a.connected_endpoint.device)

                interface_b.untagged_vlan = None
                interface_b.tagged_vlans = []

                logging.info(f"Remote port channel {interface_b.device.name} # {port_channel_b_name} -> {interface_b.device.name} # {interface_b.name} ({interface_a.name})")

                port_channel_b = nb.dcim.interfaces.get(name=port_channel_b_name, device=interface_b.device)
                if not port_channel_b:
                    try:
                        port_channel_b = nb.dcim.interfaces.create(name=port_channel_b_name, device=interface_b.device.id, type="lag")
                    except pynetbox.core.query.RequestError as e:
                        logging.error(f"ERROR --> {e}")

                interface_b.lag = port_channel_b
                interface_b.save()

                remote_port_channels.append(port_channel_b)

            # Assign IP addresses to the local port channel
            if "addresses" in data[device][interface]:
                for address in data[device][interface]["addresses"]:
                    address_a = nb.ipam.ip_addresses.get(address=address)
                    if type(address) == str:
                        address_a = nb.ipam.ip_addresses.get(address=address)
                        logging.info(f"Address {address} -> {interface}")
                        if not address_a:
                            nb.ipam.ip_addresses.create(
                                address=address,
                                assigned_object_type="dcim.interface",
                                assigned_object_id=port_channel_a.id
                            )
                    else:
                        address_a = nb.ipam.ip_addresses.get(address=address["address"])
                        logging.info(f"Address {address['address']} -> {interface}")
                        if not address_a:
                            address_a = nb.ipam.ip_addresses.create(
                                assigned_object_type="dcim.interface",
                                assigned_object_id=port_channel_a.id,
                                **address
                            )
                        if "primary" in address and bool(address["primary"]):
                            device_a.primary_ip4 = address_a.id
                            device_a.save()

            # Remove addresses from the local port channel that have been removed
            for address in nb.ipam.ip_addresses.filter(device=device, interface=interface):
                delete = True
                if "addresses" in data[device][interface]:
                    for address_a in data[device][interface]["addresses"]:
                        if type(address_a) == str and address_a == str(address):
                            delete = False
                        elif "address" in address_a and address_a["address"] == str(address):
                            delete = False

                if delete:
                    address.delete()

            # Assign VLANs to the local port channel as well as the remote port channels
            port_channel_a.untagged_vlan = None
            port_channel_a.tagged_vlans = []
            port_channel_b.untagged_vlan = None
            port_channel_b.tagged_vlans = []

            if "vlans" in data[device][interface]:
                tagged = False
                for vlan in data[device][interface]["vlans"]:
                    vlan_a = nb.ipam.vlans.get(vid=vlan)
                    if not vlan_a:
                        try:
                            vlan_a = nb.ipam.vlans.create(name=f"VLAN {vlan}", vid=vlan)
                        except pynetbox.core.query.RequestError as e:
                            logging.error(f"ERROR --> {e}")

                    if data[device][interface]["vlans"][vlan] == "untagged":
                        logging.info(f"Untagged VLAN {vlan_a.vid} -> {port_channel_a.name}")
                        port_channel_a.untagged_vlan = vlan_a.id

                        for port_channel_b in remote_port_channels:
                            logging.info(f"Untagged VLAN {vlan_a.vid} -> {port_channel_b.name}")
                            port_channel_b.untagged_vlan = vlan_a.id
                    elif vlan_a.id not in port_channel_a.tagged_vlans:
                        logging.info(f"Tagged VLAN {vlan_a.vid} -> {port_channel_a.name}")
                        port_channel_a.tagged_vlans.append(vlan_a.id)
                        tagged = True

                        for port_channel_b in remote_port_channels:
                            logging.info(f"Tagged VLAN {vlan_a.vid} -> {port_channel_b.name}")
                            port_channel_b.tagged_vlans.append(vlan_a.id)

                if tagged:
                    port_channel_a.mode = 'tagged'

                    for port_channel_b in remote_port_channels:
                        port_channel_b.mode = 'tagged'
                else:
                    port_channel_a.mode = 'access'

                    for port_channel_b in remote_port_channels:
                        port_channel_b.mode = 'access'

            port_channel_a.save()
            port_channel_b.save()

# Remove local and remote port channels that no longer exist
logging.info("Remove local and remote port channels that no longer exist")
for device in data:

    if not CONF.enforce and current_state[device] == CONF.state:
        logging.info(f"Device {device} is already in state {CONF.state}")
        continue

    for interface in nb.dcim.interfaces.filter(device=device, type="lag"):
        delete = True
        for interface_a in data[device]:
            if data[device][interface_a]["type"] == "port-channel" and str(interface) == interface_a:
                delete = False

        if delete and "Port-Channel" not in interface.name:
            members = nb.dcim.interfaces.filter(lag_id=interface.id)
            for member in members:
                member.connected_endpoint.lag.delete()
            interface.delete()


# Manage virtual interfaces
logging.info("Manage virtual interfaces")
for device in data:

    if not CONF.enforce and current_state[device] == CONF.state:
        logging.info(f"Device {device} is already in state {CONF.state}")
        continue

    for interface in data[device]:
        if data[device][interface]["type"] == "virtual":
            logging.info(f"Virtual interface {interface} for {device}")

            device_a = nb.dcim.devices.get(name=device)

            interface_a = nb.dcim.interfaces.get(name=interface, device=device)
            if not interface_a:
                try:
                    interface_a = nb.dcim.interfaces.create(name=interface, device=device_a.id, type="virtual", **data[device][interface]["data"])
                except pynetbox.core.query.RequestError as e:
                    logging.error(f"ERROR --> {e}")

            if "addresses" in data[device][interface]:
                for address in data[device][interface]["addresses"]:
                    address_a = nb.ipam.ip_addresses.get(address=address)
                    if type(address) == str:
                        address_a = nb.ipam.ip_addresses.get(address=address)
                        logging.info(f"Address {address} -> {interface}")
                        if not address_a:
                            nb.ipam.ip_addresses.create(
                                address=address,
                                assigned_object_type="dcim.interface",
                                assigned_object_id=interface_a.id
                            )
                    else:
                        address_a = nb.ipam.ip_addresses.get(address=address["address"])
                        logging.info(f"Address {address['address']} -> {interface}")
                        if not address_a:
                            address_a = nb.ipam.ip_addresses.create(
                                assigned_object_type="dcim.interface",
                                assigned_object_id=interface_a.id,
                                **address
                            )
                        if "primary" in address and bool(address["primary"]):
                            device_a.primary_ip4 = address_a.id
                            device_a.save()

            # Remove addresses from the interface that have been removed
            for address in nb.ipam.ip_addresses.filter(device=device, interface=interface):
                delete = True
                if "addresses" in data[device][interface]:
                    for address_a in data[device][interface]["addresses"]:
                        if type(address_a) == str and address_a == str(address):
                            delete = False
                        elif "address" in address_a and address_a["address"] == str(address):
                            delete = False

                if delete:
                    address.delete()

            if "vlans" in data[device][interface]:
                tagged = False
                interface_a.untagged_vlan = None
                interface_a.tagged_vlans = []
                for vlan in data[device][interface]["vlans"]:
                    vlan_a = nb.ipam.vlans.get(vid=vlan)
                    if not vlan_a:
                        try:
                            vlan_a = nb.ipam.vlans.create(name=f"VLAN {vlan}", vid=vlan)
                        except pynetbox.core.query.RequestError as e:
                            logging.error(f"ERROR --> {e}")

                    if data[device][interface]["vlans"][vlan] == "untagged":
                        interface_a.untagged_vlan = vlan_a.id
                    elif vlan_a.id not in interface_a.tagged_vlans:
                        interface_a.tagged_vlans.append(vlan_a.id)
                        tagged = True

                if tagged:
                    interface_a.mode = 'tagged'
                else:
                    interface_a.mode = 'access'
                interface_a.save()

# Remove virtual interfaces that no longer exist
logging.info("Remove virtual interfaces that no longer exist")
for device in data:

    if not CONF.enforce and current_state[device] == CONF.state:
        logging.info(f"Device {device} is already in state {CONF.state}")
        continue

    for interface in nb.dcim.interfaces.filter(device=device, type="virtual"):
        delete = True
        for interface_a in data[device]:
            if data[device][interface_a]["type"] == "virtual" and str(interface) == interface_a:
                delete = False

        if delete:
            interface.delete()


# Manage MLAG devices (not port channels)
logging.info("Manage MLAG devices (not port channels)")
for device in data:

    if not CONF.enforce and current_state[device] == CONF.state:
        logging.info(f"Device {device} is already in state {CONF.state}")
        continue

    for interface in data[device]:
        if data[device][interface]["type"] == "mlag":
            data_a = data[device][interface]["data"]
            device_a = nb.dcim.devices.get(name=device)

            logging.info(f"Local port channel {device} # Port-Channel{data_a['channel']}")

            port_channel_a = nb.dcim.interfaces.get(name=f"Port-Channel{data_a['channel']}", device=device)
            if not port_channel_a:
                try:
                    port_channel_a = nb.dcim.interfaces.create(name=f"Port-Channel{data_a['channel']}", device=device_a.id, type="lag")
                except pynetbox.core.query.RequestError as e:
                    logging.error(f"ERROR --> {e}")

            for interface_x in data[device][interface]["interfaces"]:
                interface_a = nb.dcim.interfaces.get(name=interface_x, device=device)
                interface_a.lag = port_channel_a
                interface_a.save()

            logging.info(f"Virtual interface {data_a['vlan']} for {device}")
            interface_a = nb.dcim.interfaces.get(name=f"Vlan{data_a['vlan']}", device=device)
            if not interface_a:
                try:
                    interface_a = nb.dcim.interfaces.create(name=f"Vlan{data_a['vlan']}", device=device_a.id, type="virtual")
                except pynetbox.core.query.RequestError as e:
                    logging.error(f"ERROR --> {e}")

            vlan_a = nb.ipam.vlans.get(vid=data_a['vlan'])
            interface_a.untagged_vlan = vlan_a
            interface_a.parent = port_channel_a
            interface_a.save()

            logging.info(f"Address {data_a['address']} -> {interface_a.name}")
            address_a = nb.ipam.ip_addresses.get(address=data_a["address"])
            if not address_a:
                nb.ipam.ip_addresses.create(
                    address=data_a["address"],
                    assigned_object_type="dcim.interface",
                    assigned_object_id=interface_a.id
                )


# Manage device states
logging.info("Manage device states")
for device in data:

    if not CONF.enforce and current_state[device] == CONF.state:
        logging.info(f"Device {device} is already in state {CONF.state}")
        continue

    logging.info(f"State of device {device} = {CONF.state}")
    device_a = nb.dcim.devices.get(name=device)

    device_a.custom_fields = {
        "device_state": CONF.state
    }
    device_a.save()
