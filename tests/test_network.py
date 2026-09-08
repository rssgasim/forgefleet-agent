"""Unit tests for network module."""

import pytest
from forgefleet_agent.network import NetworkInterface, SubnetCalculator


class TestNetworkInterface:
    """Test NetworkInterface class."""

    def test_subnet_calculation(self):
        """Test subnet calculation."""
        interface = NetworkInterface(
            name="Ethernet",
            status="UP",
            ipv4_address="192.168.1.20",
            ipv4_netmask="255.255.255.0",
        )
        assert interface.subnet == "192.168.1.0/24"

    def test_interface_to_dict(self):
        """Test interface to dictionary conversion."""
        interface = NetworkInterface(
            name="Ethernet",
            status="UP",
            ipv4_address="192.168.1.20",
            ipv4_netmask="255.255.255.0",
        )
        data = interface.to_dict()
        assert data["name"] == "Ethernet"
        assert data["ipv4_address"] == "192.168.1.20"
        assert data["subnet"] == "192.168.1.0/24"


class TestSubnetCalculator:
    """Test SubnetCalculator class."""

    def test_parse_network(self):
        """Test network parsing."""
        network = SubnetCalculator.parse_network(
            "192.168.1.20", "255.255.255.0"
        )
        assert network is not None
        assert str(network) == "192.168.1.0/24"

    def test_ip_in_subnet(self):
        """Test IP subnet check."""
        assert SubnetCalculator.ip_in_subnet(
            "192.168.1.50", "192.168.1.0/24"
        )
        assert not SubnetCalculator.ip_in_subnet(
            "192.168.2.50", "192.168.1.0/24"
        )

    def test_generate_ips(self):
        """Test IP generation."""
        network = SubnetCalculator.parse_network(
            "192.168.1.0", "255.255.255.0"
        )
        ips = list(SubnetCalculator.generate_ips(network))
        assert len(ips) > 0
        assert ips[0] == "192.168.1.1"
