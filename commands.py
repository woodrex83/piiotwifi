"""
System command execution for network management.
"""
import subprocess
import logging
import time
from typing import List, Optional, Dict, Any
from models import SetupConfig


class NetworkCommands:
    """Handles network interface and service management commands."""
    
    def __init__(self, setup_cfg: SetupConfig, logger: logging.Logger):
        self.setup_cfg = setup_cfg
        self.logger = logger
    
    def _run_command(self, cmd: List[str], capture_output: bool = True, 
                     check: bool = False, timeout: int = 30) -> subprocess.CompletedProcess:
        """Execute a system command safely."""
        try:
            self.logger.debug(f"Executing command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                check=check,
                timeout=timeout
            )
            
            if result.stdout:
                self.logger.debug(f"Command stdout: {result.stdout}")
            if result.stderr:
                self.logger.debug(f"Command stderr: {result.stderr}")
                
            return result
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out: {' '.join(cmd)}")
            raise
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {' '.join(cmd)}, error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error running command: {' '.join(cmd)}, error: {e}")
            raise
    
    def remove_ap_interface(self) -> None:
        """Remove the AP interface (uap0)."""
        try:
            self._run_command(['iw', 'dev', 'uap0', 'del'])
            self.logger.info("Removed AP interface uap0")
        except subprocess.CalledProcessError:
            # Interface might not exist, that's okay
            self.logger.debug("AP interface uap0 did not exist")
    
    def add_ap_interface(self) -> None:
        """Add the AP interface (uap0)."""
        self._run_command(['iw', 'phy', 'phy0', 'interface', 'add', 'uap0', 'type', '__ap'])
        self.logger.info("Added AP interface uap0")
    
    def configure_ap_interface(self) -> None:
        """Configure the AP interface with IP address."""
        ip_addr = self.setup_cfg.host_apd_cfg.ip
        self._run_command(['ifconfig', 'uap0', ip_addr])
        self.logger.info(f"Configured AP interface with IP: {ip_addr}")
    
    def up_ap_interface(self) -> None:
        """Bring up the AP interface."""
        self._run_command(['ifconfig', 'uap0', 'up'])
        self.logger.info("Brought up AP interface")
    
    def check_ap_interface(self) -> Dict[str, Any]:
        """Check the AP interface status."""
        try:
            result = self._run_command(['ifconfig', 'uap0'])
            return {"status": "up", "output": result.stdout}
        except subprocess.CalledProcessError as e:
            return {"status": "down", "error": str(e)}
    
    def start_wpa_supplicant(self) -> subprocess.Popen:
        """Start wpa_supplicant process."""
        args = [
            'wpa_supplicant',
            '-d',
            '-Dnl80211', 
            '-iwlan0',
            '-c/etc/wpa_supplicant/wpa_supplicant.conf'
        ]
        
        self.logger.info("Starting wpa_supplicant")
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        return process
    
    def start_dnsmasq(self) -> subprocess.Popen:
        """Start dnsmasq process."""
        cfg = self.setup_cfg.dnsmasq_cfg
        
        args = [
            'dnsmasq',
            '--no-hosts',
            '--keep-in-foreground',
            '--log-queries',
            '--no-resolv',
            f'--address={cfg.address}',
            f'--dhcp-range={cfg.dhcp_range}',
            f'--dhcp-vendorclass={cfg.vendor_class}',
            '--dhcp-authoritative',
            '--log-facility=-'
        ]
        
        self.logger.info("Starting dnsmasq")
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        return process
    
    def setup_ap_interface(self) -> None:
        """Complete AP interface setup sequence."""
        self.logger.info("Setting up AP interface")
        self.remove_ap_interface()
        time.sleep(1)  # Wait a moment between operations
        self.add_ap_interface()
        time.sleep(1)
        self.up_ap_interface()
        time.sleep(1)
        self.configure_ap_interface()
        self.logger.info("AP interface setup completed")
