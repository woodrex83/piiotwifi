"""
Pydantic models for IOT WiFi configuration and data structures.
"""
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field


class DnsmasqConfig(BaseModel):
    """Configuration for dnsmasq service."""
    address: str = Field(..., description="DNS address configuration")
    dhcp_range: str = Field(..., description="DHCP IP range")
    vendor_class: str = Field(..., description="DHCP vendor class")


class HostApdConfig(BaseModel):
    """Configuration for hostapd access point."""
    ssid: str = Field(..., description="WiFi network SSID")
    wpa_passphrase: str = Field(..., description="WiFi network password")
    channel: str = Field(..., description="WiFi channel")
    ip: str = Field(..., description="AP interface IP address")


class WpaSupplicantConfig(BaseModel):
    """Configuration for wpa_supplicant."""
    cfg_file: str = Field(..., description="Path to wpa_supplicant configuration file")


class SetupConfig(BaseModel):
    """Main configuration structure."""
    dnsmasq_cfg: DnsmasqConfig
    host_apd_cfg: HostApdConfig
    wpa_supplicant_cfg: WpaSupplicantConfig


class WpaCredentials(BaseModel):
    """WiFi network credentials for connection."""
    ssid: str = Field(..., description="WiFi network SSID")
    psk: str = Field(..., description="WiFi network password")


class WpaConnection(BaseModel):
    """Represents a WiFi connection status."""
    ssid: str = Field(..., description="Connected SSID")
    state: str = Field(..., description="Connection state")
    ip: str = Field(default="", description="Assigned IP address")
    message: str = Field(default="", description="Status message")


class ApiResponse(BaseModel):
    """Standard API response structure."""
    status: str = Field(..., description="Response status (OK/FAIL)")
    message: str = Field(..., description="Response message")
    payload: Optional[Any] = Field(default=None, description="Response data")


class CmdMessage(BaseModel):
    """Command execution message."""
    id: str = Field(..., description="Command identifier")
    command: str = Field(..., description="Command path")
    message: str = Field(..., description="Command output message")
    error: bool = Field(default=False, description="Whether this is an error message")
