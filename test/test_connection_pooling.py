#!/usr/bin/env python3

# Allow direct execution
import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yt_dlp.networking import RequestDirector, Request
from yt_dlp.networking._helper import InstanceStoreMixin
from yt_dlp.networking.common import RequestHandler


class TestInstanceStoreMixin(unittest.TestCase):
    """Test the enhanced InstanceStoreMixin for connection pooling"""

    def setUp(self):
        class MockHandler(RequestHandler, InstanceStoreMixin):
            _SUPPORTED_URL_SCHEMES = ('http', 'https')
            
            def __init__(self, **kwargs):
                super().__init__(logger=Mock(), **kwargs)
                self.created_instances = []
                
            def _create_instance(self, **kwargs):
                instance = Mock()
                instance.kwargs = kwargs
                self.created_instances.append(instance)
                return instance
                
            def _send(self, request):
                pass
                
        self.handler_class = MockHandler

    def test_shared_instance_connection_pooling(self):
        """Test that _get_shared_instance promotes connection reuse"""
        handler = self.handler_class()
        
        # These should reuse the same instance due to simplified pooling key
        instance1 = handler._get_shared_instance(cookiejar=None, other_param='value1')
        instance2 = handler._get_shared_instance(cookiejar=None, other_param='value2')
        
        # Should be the same instance since only essential params are considered
        self.assertIs(instance1, instance2)
        self.assertEqual(len(handler.created_instances), 1)

    def test_different_essential_params_create_new_instances(self):
        """Test that different essential parameters create separate instances"""
        handler = self.handler_class()
        
        instance1 = handler._get_shared_instance(cookiejar=None)
        instance2 = handler._get_shared_instance(cookiejar=Mock())
        
        # Should be different instances due to different cookiejar
        self.assertIsNot(instance1, instance2)
        self.assertEqual(len(handler.created_instances), 2)

    def test_regular_get_instance_behavior_unchanged(self):
        """Test that regular _get_instance behavior is unchanged"""
        handler = self.handler_class()
        
        instance1 = handler._get_instance(param1='value1')
        instance2 = handler._get_instance(param1='value1')  # Same params
        instance3 = handler._get_instance(param1='value2')  # Different params
        
        self.assertIs(instance1, instance2)  # Same params, same instance
        self.assertIsNot(instance1, instance3)  # Different params, different instance
        self.assertEqual(len(handler.created_instances), 2)


class TestRequestDirectorSessionReuse(unittest.TestCase):
    """Test that RequestDirector promotes session reuse across playlist items"""

    def test_director_is_cached_per_youtubedl_instance(self):
        """Test that RequestDirector is properly cached as documented"""
        from yt_dlp import YoutubeDL
        
        ydl = YoutubeDL()
        director1 = ydl._request_director
        director2 = ydl._request_director
        
        # Should be the same instance
        self.assertIs(director1, director2)

    def test_handlers_maintain_connections_across_requests(self):
        """Test that handlers reuse connections for multiple requests"""
        from yt_dlp.networking._urllib import UrllibRH
        
        handler = UrllibRH(logger=Mock())
        
        # Mock requests to same host
        req1 = Request('http://example.com/path1')
        req2 = Request('http://example.com/path2')
        
        # Both requests should use shared instance
        with patch.object(handler, '_get_shared_instance') as mock_get_shared:
            mock_instance = Mock()
            mock_get_shared.return_value = mock_instance
            
            try:
                handler._send(req1)
            except:
                pass  # We expect this to fail since we're mocking
            
            try:
                handler._send(req2)
            except:
                pass
            
            # Should have called _get_shared_instance for connection reuse
            self.assertEqual(mock_get_shared.call_count, 2)


if __name__ == '__main__':
    unittest.main()