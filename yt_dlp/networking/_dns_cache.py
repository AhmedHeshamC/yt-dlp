"""
Simple DNS cache for improved networking performance.
Provides short-lived in-process DNS caching for repeated hosts within a run.
"""
from __future__ import annotations

import socket
import threading
import time
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Sequence


class DNSCache:
    """Simple thread-safe DNS cache with TTL support"""
    
    def __init__(self, default_ttl: float = 300.0):  # 5 minutes default TTL
        self._cache: dict[str, tuple[Sequence[str], float]] = {}
        self._lock = threading.RLock()
        self._default_ttl = default_ttl
    
    def get(self, hostname: str) -> Sequence[str] | None:
        """Get cached DNS resolution for hostname, returns None if not cached or expired"""
        with self._lock:
            if hostname in self._cache:
                ips, expires_at = self._cache[hostname]
                if time.time() < expires_at:
                    return ips
                else:
                    # Entry expired, remove it
                    del self._cache[hostname]
            return None
    
    def set(self, hostname: str, ips: Sequence[str], ttl: float | None = None) -> None:
        """Cache DNS resolution for hostname with optional TTL"""
        if ttl is None:
            ttl = self._default_ttl
        
        expires_at = time.time() + ttl
        with self._lock:
            self._cache[hostname] = (tuple(ips), expires_at)
    
    def resolve(self, hostname: str) -> Sequence[str]:
        """Resolve hostname with caching"""
        # Check cache first
        cached_ips = self.get(hostname)
        if cached_ips is not None:
            return cached_ips
        
        # Not in cache, resolve and cache
        try:
            # Get all address families for the hostname
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            ips = []
            seen = set()
            for family, sock_type, proto, canonname, sockaddr in addr_info:
                ip = sockaddr[0]
                if ip not in seen:
                    ips.append(ip)
                    seen.add(ip)
            
            if ips:
                self.set(hostname, ips)
                return ips
            else:
                raise socket.gaierror("No addresses found")
                
        except socket.gaierror:
            # Don't cache failed resolutions
            raise
    
    def clear(self) -> None:
        """Clear all cached entries"""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> None:
        """Remove expired entries from cache"""
        current_time = time.time()
        with self._lock:
            expired_keys = [
                hostname for hostname, (_, expires_at) in self._cache.items()
                if current_time >= expires_at
            ]
            for hostname in expired_keys:
                del self._cache[hostname]


# Global DNS cache instance
_global_dns_cache = DNSCache()


def get_dns_cache() -> DNSCache:
    """Get the global DNS cache instance"""
    return _global_dns_cache


def clear_dns_cache() -> None:
    """Clear the global DNS cache"""
    _global_dns_cache.clear()