"""
WiFi management module - handles AP and Station modes.
"""
import subprocess
import time
import threading
import re
from typing import Dict, Any, Optional
import logging

from models import SetupConfig, WpaCredentials, WpaConnection
from commands import NetworkCommands
from utils import parse_key_value_output


class WiFiManager:
    """Main WiFi management class that handles AP and Station modes."""
    
    def __init__(self, setup_cfg: SetupConfig, logger: logging.Logger):
        self.setup_cfg = setup_cfg
        self.logger = logger
        self.commands = NetworkCommands(setup_cfg, logger)
        
        # Process handles
        self.hostapd_process: Optional[subprocess.Popen] = None
        self.wpa_supplicant_process: Optional[subprocess.Popen] = None
        self.dnsmasq_process: Optional[subprocess.Popen] = None
        
        # State management
        self._running = False
    
    def start_services(self) -> None:
        """Start all WiFi services."""
        self.logger.info("Starting WiFi services...")
        self._running = True
        
        # Start AP mode
        self._start_ap_mode()
        
        # Wait for AP to stabilize
        time.sleep(10)
        
        # Start Station mode (wpa_supplicant)
        self._start_station_mode()
        
        # Wait for wpa_supplicant to initialize
        time.sleep(5)
        
        # Start DHCP/DNS service
        self._start_dnsmasq()
        
        self.logger.info("All WiFi services started")
    
    def _start_ap_mode(self) -> None:
        """Start hostapd for AP mode."""
        self.logger.info("Starting Access Point mode")
        
        # Setup AP interface
        self.commands.setup_ap_interface()
        
        # Create hostapd configuration
        hostapd_config = self._generate_hostapd_config()
        
        # Start hostapd process with stdin configuration
        self.hostapd_process = subprocess.Popen(
            ['hostapd', '-d', '/dev/stdin'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send configuration to hostapd
        self.hostapd_process.stdin.write(hostapd_config)
        self.hostapd_process.stdin.close()
        
        # Monitor hostapd output in background thread
        threading.Thread(
            target=self._monitor_hostapd,
            daemon=True
        ).start()
        
        self.logger.info("Access Point started")
    
    def _generate_hostapd_config(self) -> str:
        """Generate hostapd configuration string."""
        cfg = self.setup_cfg.host_apd_cfg
        
        config = f"""interface=uap0
ssid={cfg.ssid}
hw_mode=g
channel={cfg.channel}
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=1
wpa=2
wpa_passphrase={cfg.wpa_passphrase}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""
        
        self.logger.info(f"Hostapd configuration: {config}")
        return config
    
    def _monitor_hostapd(self) -> None:
        """Monitor hostapd process output."""
        if not self.hostapd_process:
            return
        
        try:
            for line in iter(self.hostapd_process.stdout.readline, ''):
                if not line:
                    break
                
                line = line.strip()
                self.logger.info(f"HOSTAPD: {line}")
                
                if "uap0: AP-DISABLED" in line:
                    self.logger.warning("Hostapd disabled")
                    break
                elif "uap0: AP-ENABLED" in line:
                    self.logger.info("Hostapd enabled successfully")
                    
        except Exception as e:
            self.logger.error(f"Error monitoring hostapd: {e}")
    
    def _start_station_mode(self) -> None:
        """Start wpa_supplicant for Station mode."""
        self.logger.info("Starting Station mode (wpa_supplicant)")
        
        self.wpa_supplicant_process = self.commands.start_wpa_supplicant()
        
        # Monitor wpa_supplicant output in background thread
        threading.Thread(
            target=self._monitor_wpa_supplicant,
            daemon=True
        ).start()
    
    def _monitor_wpa_supplicant(self) -> None:
        """Monitor wpa_supplicant process output."""
        if not self.wpa_supplicant_process:
            return
            
        try:
            for line in iter(self.wpa_supplicant_process.stdout.readline, ''):
                if not line:
                    break
                
                line = line.strip()
                self.logger.debug(f"WPA_SUPPLICANT: {line}")
                
        except Exception as e:
            self.logger.error(f"Error monitoring wpa_supplicant: {e}")
    
    def _start_dnsmasq(self) -> None:
        """Start dnsmasq for DHCP/DNS services."""
        self.logger.info("Starting DHCP/DNS services (dnsmasq)")
        
        self.dnsmasq_process = self.commands.start_dnsmasq()
        
        # Monitor dnsmasq output in background thread
        threading.Thread(
            target=self._monitor_dnsmasq,
            daemon=True
        ).start()
    
    def _monitor_dnsmasq(self) -> None:
        """Monitor dnsmasq process output."""
        if not self.dnsmasq_process:
            return
            
        try:
            for line in iter(self.dnsmasq_process.stdout.readline, ''):
                if not line:
                    break
                
                line = line.strip()
                self.logger.debug(f"DNSMASQ: {line}")
                
        except Exception as e:
            self.logger.error(f"Error monitoring dnsmasq: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current WiFi status."""
        try:
            result = subprocess.run(
                ['wpa_cli', '-i', 'wlan0', 'status'],
                capture_output=True,
                text=True,
                check=True
            )
            
            status = parse_key_value_output(result.stdout)
            self.logger.debug(f"WiFi status: {status}")
            
            return status
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get WiFi status: {e}")
            raise Exception(f"Failed to get WiFi status: {e}")
    
    def connect_network(self, credentials: WpaCredentials) -> WpaConnection:
        """Connect to a WiFi network."""
        self.logger.info(f"Connecting to network: {credentials.ssid}")
        
        try:
            # Add network
            result = subprocess.run(
                ['wpa_cli', '-i', 'wlan0', 'add_network'],
                capture_output=True,
                text=True,
                check=True
            )
            network_id = result.stdout.strip()
            self.logger.info(f"Added network with ID: {network_id}")
            
            # Set SSID
            subprocess.run(
                ['wpa_cli', '-i', 'wlan0', 'set_network', network_id, 'ssid', f'"{credentials.ssid}"'],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Set PSK
            subprocess.run(
                ['wpa_cli', '-i', 'wlan0', 'set_network', network_id, 'psk', f'"{credentials.psk}"'],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Enable network
            subprocess.run(
                ['wpa_cli', '-i', 'wlan0', 'enable_network', network_id],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Wait for connection and check status
            for attempt in range(5):
                self.logger.info(f"Checking connection status (attempt {attempt + 1}/5)")
                
                status_result = subprocess.run(
                    ['wpa_cli', '-i', 'wlan0', 'status'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                status = parse_key_value_output(status_result.stdout)
                wpa_state = status.get('wpa_state', 'UNKNOWN')
                
                self.logger.info(f"WPA state: {wpa_state}")
                
                if wpa_state == 'COMPLETED':
                    # Save configuration
                    subprocess.run(
                        ['wpa_cli', '-i', 'wlan0', 'save_config'],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    # Get IP address if available
                    ip_address = status.get('ip_address', '')
                    
                    connection = WpaConnection(
                        ssid=credentials.ssid,
                        state=wpa_state,
                        ip=ip_address,
                        message="Connected successfully"
                    )
                    
                    self.logger.info(f"Successfully connected to {credentials.ssid}")
                    return connection
                
                time.sleep(3)
            
            # Connection failed
            connection = WpaConnection(
                ssid=credentials.ssid,
                state="FAIL",
                ip="",
                message=f"Unable to connect to {credentials.ssid}"
            )
            
            return connection
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Connection failed: {e}")
            raise Exception(f"Connection failed: {e}")
    
    def cleanup(self) -> None:
        """Cleanup processes and resources."""
        self.logger.info("Cleaning up WiFi manager...")
        self._running = False
        
        # Terminate processes
        for process_name, process in [
            ('hostapd', self.hostapd_process),
            ('wpa_supplicant', self.wpa_supplicant_process),
            ('dnsmasq', self.dnsmasq_process)
        ]:
            if process and process.poll() is None:
                self.logger.info(f"Terminating {process_name}")
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.logger.warning(f"Force killing {process_name}")
                    process.kill()
                except Exception as e:
                    self.logger.error(f"Error stopping {process_name}: {e}")
        
        self.logger.info("WiFi manager cleanup completed")
