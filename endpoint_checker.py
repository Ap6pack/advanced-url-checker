#!/usr/bin/env python3
"""
Advanced URL Availability Checker
Checks URLs for availability with comprehensive error handling, retry logic, and progress tracking.
"""

import argparse
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from threading import Lock
from urllib.parse import urlparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from ipaddress import ip_address, ip_network, AddressValueError

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import validators
from dotenv import load_dotenv
from colorama import init, Fore, Style
from tqdm import tqdm

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Load environment variables
load_dotenv()

# Security constants
BLOCKED_NETWORKS = [
    ip_network('10.0.0.0/8'),
    ip_network('172.16.0.0/12'),
    ip_network('192.168.0.0/16'),
    ip_network('127.0.0.0/8'),
    ip_network('169.254.0.0/16'),  # Link-local
    ip_network('::1/128'),  # IPv6 localhost
    ip_network('fc00::/7'),  # IPv6 private
]

MAX_URL_LENGTH = 2048
MAX_REDIRECTS = 10


class URLChecker:
    """Main class for checking URL availability with comprehensive error handling."""
    
    def __init__(self, config):
        self.config = config
        self.stats = {
            'total': 0,
            'active': 0,
            'inactive': 0,
            'timeouts': 0,
            'dns_errors': 0,
            'connection_errors': 0,
            'ssl_errors': 0,
            'other_errors': 0,
            'start_time': None,
            'processed': 0
        }
        self.file_lock = Lock()
        self.setup_logging()
        self.session = self._create_session()
        self.progress_bar = None
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with security features and connection pooling."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=0,  # We handle retries manually
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        
        # Configure adapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=min(self.config.threads * 2, 100),
            pool_maxsize=min(self.config.threads * 2, 100),
            pool_block=False
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Add custom headers
        for header in self.config.headers:
            if ':' in header:
                key, value = header.split(':', 1)
                session.headers[key.strip()] = value.strip()
        
        # Configure authentication
        if self.config.auth:
            username, password = self.config.auth.split(':', 1)
            session.auth = (username, password)
        
        # Security: Don't follow redirects automatically (we'll handle it)
        # Note: Setting max_redirects doesn't affect allow_redirects=False in requests
        
        # Always verify SSL certificates for security
        session.verify = True
        
        return session
    
    def setup_logging(self):
        """Configure logging based on verbosity level."""
        log_level = logging.DEBUG if self.config.verbose else logging.INFO
        if self.config.quiet:
            log_level = logging.WARNING
            
        # Sanitize output file path
        safe_output_file = Path(self.config.output_file).name
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"{safe_output_file}.log"),
                logging.StreamHandler(sys.stdout) if not self.config.quiet else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_urls(self):
        """Load URLs from input file with validation."""
        if not os.path.exists(self.config.input_file):
            self.logger.error(f"Input file '{self.config.input_file}' not found")
            sys.exit(1)
            
        urls = []
        try:
            with open(self.config.input_file, 'r') as file:
                for line_num, line in enumerate(file, 1):
                    url = line.strip()
                    if url and not url.startswith('#'):
                        if self.validate_url(url):
                            urls.append(url)
                        else:
                            self.logger.warning(f"Invalid URL on line {line_num}: {url}")
        except Exception as e:
            self.logger.error(f"Error reading input file: {e}")
            sys.exit(1)
            
        if not urls:
            self.logger.error("No valid URLs found in input file")
            sys.exit(1)
            
        self.logger.info(f"Loaded {len(urls)} URLs to test")
        return urls
        
    def validate_url(self, url: str) -> bool:
        """Validate URL format with security checks."""
        try:
            # Add http:// if no scheme provided
            if not url.startswith(('http://', 'https://')):
                url = f"http://{url}"
            
            # Check URL length
            if len(url) > MAX_URL_LENGTH:
                self.logger.warning(f"URL too long: {url[:50]}...")
                return False
            
            # Use validators library for proper validation
            if not validators.url(url):
                return False
            
            # Parse and check for private IPs
            parsed = urlparse(url)
            
            # Check if hostname is an IP address
            try:
                ip = ip_address(parsed.hostname)
                # Block private/local IP addresses
                for network in BLOCKED_NETWORKS:
                    if ip in network:
                        self.logger.warning(f"Blocked private IP: {url}")
                        return False
            except (ValueError, AddressValueError, TypeError):
                # Not an IP address, continue with domain validation
                pass
            
            return True
            
        except Exception as e:
            self.logger.debug(f"URL validation error: {e}")
            return False
            
    def normalize_url(self, url):
        """Normalize URL by adding http:// if no scheme provided."""
        if not url.startswith(('http://', 'https://')):
            return f"http://{url}"
        return url
        
    def classify_error(self, exception: Exception) -> str:
        """Classify errors based on exception type."""
        error_str = str(exception).lower()
        exception_type = type(exception).__name__
        
        # DNS resolution errors
        if 'nodename nor servname provided' in error_str or \
           'name or service not known' in error_str or \
           'getaddrinfo failed' in error_str or \
           'Failed to resolve' in error_str:
            return 'DNS_ERROR'
            
        # Connection errors
        elif 'connection refused' in error_str or \
             'connection reset' in error_str or \
             'connection aborted' in error_str or \
             isinstance(exception, requests.exceptions.ConnectionError):
            return 'CONNECTION_ERROR'
            
        # SSL/TLS errors
        elif 'ssl' in error_str or \
             'certificate' in error_str or \
             isinstance(exception, requests.exceptions.SSLError):
            return 'SSL_ERROR'
            
        # Timeout errors
        elif isinstance(exception, requests.exceptions.Timeout) or \
             'timeout' in error_str:
            return 'TIMEOUT'
            
        # Other errors
        else:
            return 'OTHER_ERROR'
            
    def test_url_with_retry(self, url):
        """Test URL with retry logic and exponential backoff."""
        normalized_url = self.normalize_url(url)
        
        for attempt in range(self.config.max_retries + 1):
            try:
                result = self.test_url_single(normalized_url, attempt + 1)
                
                # Don't retry on DNS errors or successful responses
                if result['error_type'] == 'DNS_ERROR' or result['status'] == 'ACTIVE':
                    return result
                    
                # Retry on network errors
                if attempt < self.config.max_retries:
                    delay = (2 ** attempt) * 0.5  # Exponential backoff: 0.5s, 1s, 2s
                    self.logger.debug(f"Retrying {url} in {delay}s (attempt {attempt + 2})")
                    time.sleep(delay)
                else:
                    return result
                    
            except Exception as e:
                if attempt < self.config.max_retries:
                    delay = (2 ** attempt) * 0.5
                    time.sleep(delay)
                else:
                    return {
                        'url': url,
                        'status': 'ERROR',
                        'http_code': 'N/A',
                        'response_time': 'N/A',
                        'error_type': 'OTHER_ERROR',
                        'error_message': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                    
    def test_url_single(self, url: str, attempt_num: int) -> Dict[str, Any]:
        """Test a single URL using requests library with security features."""
        start_time = time.time()
        
        try:
            # Prepare request parameters
            request_params = {
                'timeout': (self.config.connect_timeout, self.config.timeout),
                'allow_redirects': False,  # Handle redirects manually for security
                'stream': True,  # Don't download entire body for HEAD requests
                'verify': True,  # Always verify SSL certificates
            }
            
            # Make the request based on method
            if self.config.method == 'HEAD':
                response = self.session.head(url, **request_params)
            elif self.config.method == 'POST':
                response = self.session.post(url, **request_params)
            else:  # GET
                response = self.session.get(url, **request_params)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Handle redirects manually with security checks
            redirect_count = 0
            final_url = url
            
            while response.is_redirect and redirect_count < MAX_REDIRECTS:
                redirect_url = response.headers.get('Location')
                if not redirect_url:
                    break
                    
                # Make redirect URL absolute
                redirect_url = requests.compat.urljoin(url, redirect_url)
                
                # Validate redirect URL for security
                if not self.validate_url(redirect_url):
                    self.logger.warning(f"Blocked redirect to invalid URL: {redirect_url}")
                    break
                
                # Follow redirect
                if self.config.method == 'HEAD':
                    response = self.session.head(redirect_url, **request_params)
                else:
                    response = self.session.get(redirect_url, **request_params)
                
                final_url = redirect_url
                redirect_count += 1
            
            # Get response size (for GET requests)
            size = '0'
            if self.config.method == 'GET' and response.headers.get('content-length'):
                size = response.headers.get('content-length', '0')
            
            # Determine status
            http_code = str(response.status_code)
            if response.status_code < 400:
                status = 'ACTIVE'
            else:
                status = 'INACTIVE'
            
            return {
                'url': url,
                'final_url': final_url,
                'status': status,
                'http_code': http_code,
                'response_time': f"{response_time:.3f}",
                'size': size,
                'error_type': None,
                'error_message': None,
                'attempt': attempt_num,
                'timestamp': datetime.now().isoformat(),
                'redirects': redirect_count
            }
            
        except requests.exceptions.Timeout:
            return {
                'url': url,
                'status': 'TIMEOUT',
                'http_code': 'N/A',
                'response_time': f">{self.config.timeout}s",
                'error_type': 'TIMEOUT',
                'error_message': 'Request timed out',
                'attempt': attempt_num,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_type = self.classify_error(e)
            return {
                'url': url,
                'status': 'ERROR',
                'http_code': 'N/A',
                'response_time': f"{time.time() - start_time:.3f}",
                'error_type': error_type,
                'error_message': str(e),
                'attempt': attempt_num,
                'timestamp': datetime.now().isoformat()
            }
            
    def update_stats(self, result):
        """Update statistics based on result."""
        self.stats['processed'] += 1
        
        if result['status'] == 'ACTIVE':
            self.stats['active'] += 1
        elif result['status'] == 'INACTIVE':
            self.stats['inactive'] += 1
        elif result['error_type'] == 'TIMEOUT':
            self.stats['timeouts'] += 1
        elif result['error_type'] == 'DNS_ERROR':
            self.stats['dns_errors'] += 1
        elif result['error_type'] == 'CONNECTION_ERROR':
            self.stats['connection_errors'] += 1
        elif result['error_type'] == 'SSL_ERROR':
            self.stats['ssl_errors'] += 1
        else:
            self.stats['other_errors'] += 1
            
    def write_result(self, result):
        """Write result to appropriate output files."""
        with self.file_lock:
            # Write to main output file
            if self.config.output_format == 'json':
                with open(self.config.output_file, 'a') as f:
                    f.write(json.dumps(result) + '\n')
            else:
                with open(self.config.output_file, 'a') as f:
                    status_str = f"{result['url']}: {result['status']}"
                    if result['http_code'] != 'N/A':
                        status_str += f" (HTTP {result['http_code']})"
                    if result['response_time'] != 'N/A':
                        status_str += f" [{result['response_time']}]"
                    if result['error_message']:
                        status_str += f" - {result['error_message']}"
                    f.write(status_str + '\n')
                    
            # Write to separate files for active/inactive URLs
            if result['status'] == 'ACTIVE':
                with open(f"{self.config.output_file}_active.txt", 'a') as f:
                    f.write(f"{result['url']}\n")
            elif result['status'] in ['INACTIVE', 'ERROR', 'TIMEOUT']:
                with open(f"{self.config.output_file}_inactive.txt", 'a') as f:
                    f.write(f"{result['url']}\n")
                    
    def update_progress_bar(self):
        """Update the progress bar with current stats."""
        if self.progress_bar and not self.config.quiet:
            # Update progress bar
            self.progress_bar.update(1)
            
            # Update description with colored stats
            active_color = Fore.GREEN if self.stats['active'] > 0 else Fore.WHITE
            error_color = Fore.RED if (self.stats['timeouts'] + self.stats['dns_errors'] + 
                                      self.stats['connection_errors'] + self.stats['ssl_errors'] + 
                                      self.stats['other_errors']) > 0 else Fore.WHITE
            
            total_errors = (self.stats['timeouts'] + self.stats['dns_errors'] + 
                           self.stats['connection_errors'] + self.stats['ssl_errors'] + 
                           self.stats['other_errors'])
            
            desc = (f"{active_color}Active: {self.stats['active']}{Style.RESET_ALL} | "
                   f"Inactive: {self.stats['inactive']} | "
                   f"{error_color}Errors: {total_errors}{Style.RESET_ALL}")
            
            self.progress_bar.set_description(desc)
        
    def print_summary(self):
        """Print final summary statistics."""
        if not self.config.quiet:
            print("\n" + "="*60)
            print("SUMMARY")
            print("="*60)
            
        elapsed = time.time() - self.stats['start_time']
        rate = self.stats['total'] / elapsed if elapsed > 0 else 0
        
        summary = f"""
Total URLs processed: {self.stats['total']}
Active URLs: {self.stats['active']} ({self.stats['active']/self.stats['total']*100:.1f}%)
Inactive URLs: {self.stats['inactive']} ({self.stats['inactive']/self.stats['total']*100:.1f}%)
Timeouts: {self.stats['timeouts']}
DNS Errors: {self.stats['dns_errors']}
Connection Errors: {self.stats['connection_errors']}
SSL Errors: {self.stats['ssl_errors']}
Other Errors: {self.stats['other_errors']}

Processing Time: {elapsed:.1f}s
Processing Rate: {rate:.1f} URLs/s

Output Files:
- Main results: {self.config.output_file}
- Active URLs: {self.config.output_file}_active.txt
- Inactive URLs: {self.config.output_file}_inactive.txt
- Log file: {self.config.output_file}.log
        """
        
        if not self.config.quiet:
            print(summary)
            
        # Write summary to log
        self.logger.info("Processing completed" + summary)
        
    def clear_output_files(self):
        """Clear previous output files."""
        files_to_clear = [
            self.config.output_file,
            f"{self.config.output_file}_active.txt",
            f"{self.config.output_file}_inactive.txt",
            f"{self.config.output_file}.log"
        ]
        
        for file_path in files_to_clear:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    self.logger.warning(f"Could not remove {file_path}: {e}")
                    
    def dry_run(self, urls):
        """Perform a dry run to validate URLs without testing them."""
        print(f"DRY RUN: Would test {len(urls)} URLs")
        print(f"Configuration:")
        print(f"  Threads: {self.config.threads}")
        print(f"  Timeout: {self.config.timeout}s")
        print(f"  Retries: {self.config.max_retries}")
        print(f"  Method: {self.config.method}")
        print(f"  User Agent: {self.config.user_agent}")
        
        print(f"\nFirst 10 URLs to test:")
        for i, url in enumerate(urls[:10]):
            print(f"  {i+1}. {url}")
            
        if len(urls) > 10:
            print(f"  ... and {len(urls) - 10} more")
            
    def run(self):
        """Main execution method."""
        # Load URLs
        urls = self.load_urls()
        self.stats['total'] = len(urls)
        
        # Dry run mode
        if self.config.dry_run:
            self.dry_run(urls)
            return
            
        # Clear previous results
        if not self.config.append:
            self.clear_output_files()
            
        self.logger.info(f"Starting URL check with {self.config.threads} threads")
        self.stats['start_time'] = time.time()
        
        # Create progress bar if not in quiet mode
        if not self.config.quiet:
            self.progress_bar = tqdm(
                total=len(urls),
                desc="Processing URLs",
                unit="url",
                ncols=100,
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
            )
        
        # Process URLs with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.config.threads) as executor:
            # Submit all tasks
            future_to_url = {executor.submit(self.test_url_with_retry, url): url for url in urls}
            
            # Process completed tasks
            for future in as_completed(future_to_url):
                result = future.result()
                self.update_stats(result)
                self.write_result(result)
                
                # Update progress bar
                self.update_progress_bar()
                    
                # Log individual results in verbose mode
                if self.config.verbose:
                    status_msg = f"{result['url']}: {result['status']}"
                    if result['http_code'] != 'N/A':
                        status_msg += f" (HTTP {result['http_code']})"
                    self.logger.debug(status_msg)
        
        # Close progress bar
        if self.progress_bar:
            self.progress_bar.close()
            
        # Final summary
        self.print_summary()


def create_config_from_args():
    """Create configuration from command line arguments."""
    parser = argparse.ArgumentParser(
        description="Enhanced URL checker for waymore output with retry logic and detailed error handling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s urls.txt                          # Basic usage
  %(prog)s urls.txt -t 20 -r 3              # 20 threads, 3 retries
  %(prog)s urls.txt -o results.json --json  # JSON output
  %(prog)s urls.txt --method HEAD --quiet   # HEAD requests, quiet mode
  %(prog)s urls.txt --dry-run               # Validate without testing
        """
    )
    
    # Input/Output options
    parser.add_argument('input_file', help='Input file containing URLs (one per line)')
    parser.add_argument('-o', '--output', dest='output_file', default='url_check_results.txt',
                       help='Output file for results (default: url_check_results.txt)')
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    parser.add_argument('--append', action='store_true', help='Append to existing output files')
    
    # Request options
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds (default: 10)')
    parser.add_argument('--connect-timeout', type=int, default=5, help='Connection timeout in seconds (default: 5)')
    parser.add_argument('-r', '--retries', dest='max_retries', type=int, default=2,
                       help='Maximum number of retries for failed requests (default: 2)')
    parser.add_argument('-m', '--method', choices=['GET', 'HEAD', 'POST'], default='GET',
                       help='HTTP method to use (default: GET)')
    parser.add_argument('--user-agent', default='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                       help='User agent string')
    parser.add_argument('--auth', help='Authentication in format username:password')
    parser.add_argument('--header', dest='headers', action='append', default=[],
                       help='Additional headers (can be used multiple times)')
    
    # Performance options
    parser.add_argument('-t', '--threads', type=int, default=10, help='Number of concurrent threads (default: 10)')
    
    # Output options
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode (minimal output)')
    parser.add_argument('--dry-run', action='store_true', help='Validate configuration without testing URLs')
    
    args = parser.parse_args()
    
    # Validation
    if args.quiet and args.verbose:
        parser.error("Cannot use both --quiet and --verbose")
        
    if args.threads < 1 or args.threads > 100:
        parser.error("Threads must be between 1 and 100")
        
    if args.timeout < 1 or args.timeout > 300:
        parser.error("Timeout must be between 1 and 300 seconds")
        
    # Set output format
    args.output_format = 'json' if args.json else 'text'
    
    return args


def main():
    """Main entry point."""
    try:
        config = create_config_from_args()
        checker = URLChecker(config)
        checker.run()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
