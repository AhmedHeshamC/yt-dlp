#!/usr/bin/env python3

# Allow direct execution
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yt_dlp import YoutubeDL
from yt_dlp.options import parseOpts
from yt_dlp import validate_options


class TestRetryBackoffDefaults(unittest.TestCase):
    """Test that exponential backoff defaults are applied correctly"""

    def test_youtube_dl_defaults(self):
        """Test YoutubeDL constructor applies defaults"""
        ydl = YoutubeDL({})
        retry_funcs = ydl.params.get('retry_sleep_functions', {})
        
        # Should have defaults for http and extractor
        self.assertIn('http', retry_funcs)
        self.assertIn('extractor', retry_funcs)
        
        # Test http function (exp=0.5:10:2)
        http_func = retry_funcs['http']
        self.assertEqual(http_func(0), 0.5)  # 0.5 * (2^0) = 0.5
        self.assertEqual(http_func(1), 1.0)  # 0.5 * (2^1) = 1.0
        self.assertEqual(http_func(2), 2.0)  # 0.5 * (2^2) = 2.0
        self.assertEqual(http_func(3), 4.0)  # 0.5 * (2^3) = 4.0
        self.assertEqual(http_func(4), 8.0)  # 0.5 * (2^4) = 8.0
        self.assertEqual(http_func(5), 10.0) # capped at 10.0
        
        # Test extractor function (exp=1:16:2)
        extractor_func = retry_funcs['extractor']
        self.assertEqual(extractor_func(0), 1.0)  # 1 * (2^0) = 1.0
        self.assertEqual(extractor_func(1), 2.0)  # 1 * (2^1) = 2.0
        self.assertEqual(extractor_func(2), 4.0)  # 1 * (2^2) = 4.0
        self.assertEqual(extractor_func(3), 8.0)  # 1 * (2^3) = 8.0
        self.assertEqual(extractor_func(4), 16.0) # 1 * (2^4) = 16.0, capped
        self.assertEqual(extractor_func(5), 16.0) # still capped at 16.0

    def test_user_override_works(self):
        """Test that user-specified retry_sleep_functions override defaults"""
        custom_funcs = {
            'http': lambda n: 5.0,  # Constant delay
            'custom': lambda n: n,  # Custom type
        }
        
        ydl = YoutubeDL({'retry_sleep_functions': custom_funcs})
        retry_funcs = ydl.params.get('retry_sleep_functions', {})
        
        # Should use user-specified functions
        self.assertEqual(retry_funcs['http'](0), 5.0)
        self.assertEqual(retry_funcs['http'](10), 5.0)
        self.assertEqual(retry_funcs['custom'](3), 3)
        
        # Should not have default extractor if not specified by user
        self.assertNotIn('extractor', retry_funcs)

    def test_empty_dict_gets_defaults(self):
        """Test that empty retry_sleep_functions dict gets defaults"""
        ydl = YoutubeDL({'retry_sleep_functions': {}})
        retry_funcs = ydl.params.get('retry_sleep_functions', {})
        
        # Should still get defaults
        self.assertIn('http', retry_funcs)
        self.assertIn('extractor', retry_funcs)

    def test_cli_defaults(self):
        """Test that CLI parsing applies defaults"""
        parser, opts, urls = parseOpts([])
        self.assertEqual(opts.retry_sleep, {})  # Empty before validation
        
        # After validation should have defaults
        warnings, dep_warnings = validate_options(opts)
        self.assertIn('http', opts.retry_sleep)
        self.assertIn('extractor', opts.retry_sleep)
        
        # Test the functions work
        http_func = opts.retry_sleep['http']
        self.assertEqual(http_func(0), 0.5)

    def test_cli_user_override(self):
        """Test that CLI user-specified values override defaults"""
        parser, opts, urls = parseOpts(['--retry-sleep', 'http:linear=3'])
        
        warnings, dep_warnings = validate_options(opts)
        
        # Should have user's http but NOT default extractor (user only specified http)
        self.assertIn('http', opts.retry_sleep)
        self.assertNotIn('extractor', opts.retry_sleep)  # User didn't specify, so no default
        
        # HTTP should be linear function: 3 + 3*n (when only start is specified for linear)
        http_func = opts.retry_sleep['http']
        self.assertEqual(http_func(0), 3.0)  # 3 + 3*0 = 3
        self.assertEqual(http_func(1), 6.0)  # 3 + 3*1 = 6
        self.assertEqual(http_func(2), 9.0)  # 3 + 3*2 = 9


if __name__ == '__main__':
    unittest.main()