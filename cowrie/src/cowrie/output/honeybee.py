# Copyright (c) 2024 HoneyBee Project
# Custom output plugin for HoneyBee integration
#
# This plugin sends Cowrie events to the HoneyBee Node via a TCP socket.
# The node then forwards these events to the HoneyBee Core manager.

from __future__ import annotations

import json
import socket
import time
from typing import Any, Dict, Optional

import cowrie.core.output
from cowrie.core.config import CowrieConfig
from twisted.python import log


class Output(cowrie.core.output.Output):
    """
    HoneyBee output plugin for Cowrie.
    
    Sends JSON events to the HoneyBee Node's event collector socket.
    The node enriches these events with node/honeypot metadata before
    forwarding to the HoneyBee Core manager.
    
    Configuration in cowrie.cfg:
    
    [output_honeybee]
    enabled = true
    address = 127.0.0.1:9100
    timeout = 5
    honeypot_id = my-cowrie-instance
    retry_count = 3
    retry_delay = 1
    buffer_size = 1000
    """

    def __init__(self) -> None:
        self.sock: Optional[socket.socket] = None
        self.host: str = "127.0.0.1"
        self.port: int = 9100
        self.timeout: int = 5
        self.honeypot_id: str = "cowrie"
        self.retry_count: int = 3
        self.retry_delay: float = 1.0
        self.buffer_size: int = 1000
        self.event_buffer: list = []
        self.connected: bool = False
        cowrie.core.output.Output.__init__(self)

    def start(self) -> None:
        """Initialize the output plugin."""
        # Load configuration
        self.timeout = CowrieConfig.getint(
            "output_honeybee", "timeout", fallback=5
        )
        addr = CowrieConfig.get(
            "output_honeybee", "address", fallback="127.0.0.1:9100"
        )
        self.host = addr.split(":")[0]
        self.port = int(addr.split(":")[1])
        
        self.honeypot_id = CowrieConfig.get(
            "output_honeybee", "honeypot_id", fallback="cowrie"
        )
        self.retry_count = CowrieConfig.getint(
            "output_honeybee", "retry_count", fallback=3
        )
        self.retry_delay = CowrieConfig.getfloat(
            "output_honeybee", "retry_delay", fallback=1.0
        )
        self.buffer_size = CowrieConfig.getint(
            "output_honeybee", "buffer_size", fallback=1000
        )

        log.msg(
            f"HoneyBee output plugin starting, connecting to {self.host}:{self.port}"
        )
        self._connect()

    def stop(self) -> None:
        """Clean up the output plugin."""
        # Flush any remaining buffered events
        self._flush_buffer()
        
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        self.connected = False
        log.msg("HoneyBee output plugin stopped")

    def _connect(self) -> bool:
        """Establish connection to the HoneyBee Node."""
        if self.connected and self.sock:
            return True

        for attempt in range(self.retry_count):
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(self.timeout)
                self.sock.connect((self.host, self.port))
                self.connected = True
                log.msg(f"Connected to HoneyBee Node at {self.host}:{self.port}")
                
                # Flush buffered events after reconnection
                self._flush_buffer()
                return True
                
            except (socket.error, OSError) as ex:
                log.msg(
                    f"HoneyBee connection attempt {attempt + 1}/{self.retry_count} "
                    f"failed: {ex}"
                )
                if self.sock:
                    try:
                        self.sock.close()
                    except Exception:
                        pass
                    self.sock = None
                self.connected = False
                
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)

        return False

    def _flush_buffer(self) -> None:
        """Send all buffered events."""
        if not self.event_buffer:
            return
            
        if not self.connected:
            return
            
        events_to_send = self.event_buffer.copy()
        self.event_buffer.clear()
        
        for event in events_to_send:
            self._send_event(event, buffer_on_fail=False)

    def _send_event(self, event: Dict[str, Any], buffer_on_fail: bool = True) -> bool:
        """Send a single event to the HoneyBee Node."""
        if not self.connected:
            if not self._connect():
                if buffer_on_fail:
                    self._buffer_event(event)
                return False

        message = json.dumps(event) + "\n"
        
        try:
            self.sock.sendall(message.encode("utf-8"))
            return True
            
        except (socket.error, OSError, BrokenPipeError) as ex:
            log.msg(f"HoneyBee send failed: {ex}")
            self.connected = False
            
            # Try to reconnect once
            if self._connect():
                try:
                    self.sock.sendall(message.encode("utf-8"))
                    return True
                except Exception:
                    pass
            
            if buffer_on_fail:
                self._buffer_event(event)
            return False

    def _buffer_event(self, event: Dict[str, Any]) -> None:
        """Buffer an event for later transmission."""
        if len(self.event_buffer) >= self.buffer_size:
            # Remove oldest event to make room
            self.event_buffer.pop(0)
            log.msg("HoneyBee event buffer full, dropping oldest event")
        
        self.event_buffer.append(event)

    def write(self, event: Dict[str, Any]) -> None:
        """
        Write an event to the HoneyBee Node.
        
        This method is called by Cowrie for every event that occurs.
        We enrich the event with HoneyBee-specific metadata before sending.
        """
        # Remove Twisted legacy keys
        for key in list(event.keys()):
            if key.startswith("log_"):
                del event[key]

        # Add HoneyBee-specific enrichment
        enriched_event = self._enrich_event(event)
        
        # Send to HoneyBee Node
        self._send_event(enriched_event)

    def _enrich_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a Cowrie event with HoneyBee-specific metadata.
        
        This helps the HoneyBee Node and Core process events more efficiently.
        """
        enriched = event.copy()
        
        # Add honeypot identification
        enriched["honeybee_honeypot_id"] = self.honeypot_id
        enriched["honeybee_honeypot_type"] = "cowrie"
        
        # Categorize event for easier processing
        eventid = event.get("eventid", "")
        enriched["honeybee_category"] = self._categorize_event(eventid)
        
        # Add severity level
        enriched["honeybee_severity"] = self._get_severity(eventid)
        
        return enriched

    def _categorize_event(self, eventid: str) -> str:
        """Categorize a Cowrie event for HoneyBee processing."""
        if not eventid:
            return "unknown"
            
        categories = {
            "cowrie.session.connect": "connection",
            "cowrie.session.closed": "connection",
            "cowrie.session.params": "connection",
            "cowrie.login.success": "authentication",
            "cowrie.login.failed": "authentication",
            "cowrie.command.input": "command",
            "cowrie.command.success": "command",
            "cowrie.command.failed": "command",
            "cowrie.session.file_download": "file_transfer",
            "cowrie.session.file_upload": "file_transfer",
            "cowrie.client.version": "client_info",
            "cowrie.client.kex": "client_info",
            "cowrie.client.size": "client_info",
            "cowrie.client.var": "client_info",
            "cowrie.direct-tcpip.request": "tunnel",
            "cowrie.direct-tcpip.data": "tunnel",
        }
        
        for prefix, category in categories.items():
            if eventid.startswith(prefix):
                return category
        
        return "other"

    def _get_severity(self, eventid: str) -> str:
        """Determine severity level for an event."""
        if not eventid:
            return "info"
            
        high_severity = [
            "cowrie.login.success",
            "cowrie.command.input",
            "cowrie.session.file_download",
            "cowrie.session.file_upload",
        ]
        
        medium_severity = [
            "cowrie.login.failed",
            "cowrie.direct-tcpip.request",
        ]
        
        if eventid in high_severity:
            return "high"
        elif eventid in medium_severity:
            return "medium"
        else:
            return "low"

