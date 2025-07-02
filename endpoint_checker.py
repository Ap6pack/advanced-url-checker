#!/usr/bin/env python3
"""
"Advanced URL Availability Checker
Checks URLs for availability with comprehensive error handling, retry logic, and progress tracking."
"""

import subprocess
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
import re

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
        
    def setup_logging(self):
        """Configure logging based on verbosity level."""
        log_level = logging.DEBUG if self.config.verbose else logging.INFO
        if self.config.quiet:
            log_level = logging.WARNING
            
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"{self.config.output_file}.log"),
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
        
    def validate_url(self, url):
        """Validate URL format."""
        try:
            # Add http:// if no scheme provided
            if not url.startswith(('http://', 'https://')):
                url = f"http://{url}"
            parsed = urlparse(url)
            return bool(parsed.netloc)
        except:
            return False
            
    def normalize_url(self, url):
        """Normalize URL by adding http:// if no scheme provided."""
        if not url.startswith(('http://', 'https://')):
            return f"http://{url}"
        return url
        
    def classify_error(self, stderr, returncode):
        """Classify curl errors based on stderr output and return codes."""
        stderr_lower = stderr.lower()
        
        # DNS resolution errors
        if any(phrase in stderr_lower for phrase in [
            'could not resolve host', 'name or service not known', 
            'nodename nor servname provided', 'temporary failure in name resolution'
        ]):
            return 'DNS_ERROR'
            
        # Connection errors
        elif any(phrase in stderr_lower for phrase in [
            'connection refused', 'connection timed out', 'no route to host',
            'network is unreachable', 'connection reset by peer'
        ]):
            return 'CONNECTION_ERROR'
            
        # SSL/TLS errors
        elif any(phrase in stderr_lower for phrase in [
            'ssl', 'tls', 'certificate', 'handshake', 'peer certificate'
        ]):
            return 'SSL_ERROR'
            
        # Timeout errors
        elif 'timeout' in stderr_lower or returncode == 28:
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
                    
    def test_url_single(self, url, attempt_num):
        """Test a single URL using curl."""
        start_time = time.time()
        
        # Build curl command
        command = [
            "curl", "-s", "-o", "/dev/null", "-L",
            "-H", f"User-Agent: {self.config.user_agent}",
            "-w", "HTTP_CODE:%{http_code}|TIME:%{time_total}|SIZE:%{size_download}",
            "--connect-timeout", str(self.config.connect_timeout),
            "--max-time", str(self.config.timeout)
        ]
        
        # Add method-specific options
        if self.config.method == 'HEAD':
            command.append("-I")
        elif self.config.method == 'POST':
            command.extend(["-X", "POST"])
            
        # Add custom headers
        for header in self.config.headers:
            command.extend(["-H", header])
            
        # Add authentication if provided
        if self.config.auth:
            command.extend(["-u", self.config.auth])
            
        command.append(url)
        
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=self.config.timeout + 5  # Give subprocess extra time
            )
            
            response_time = time.time() - start_time
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            
            # Parse curl output
            http_code = 'N/A'
            curl_time = 'N/A'
            size = 'N/A'
            
            if 'HTTP_CODE:' in stdout:
                parts = stdout.split('|')
                for part in parts:
                    if part.startswith('HTTP_CODE:'):
                        http_code = part.split(':')[1]
                    elif part.startswith('TIME:'):
                        curl_time = part.split(':')[1]
                    elif part.startswith('SIZE:'):
                        size = part.split(':')[1]
            
            # Determine status
            if result.returncode == 0 and http_code.isdigit():
                status = 'ACTIVE' if int(http_code) < 400 else 'INACTIVE'
                error_type = None
                error_message = None
            else:
                status = 'ERROR'
                error_type = self.classify_error(stderr, result.returncode)
                error_message = stderr or f"Process returned code {result.returncode}"
                
            return {
                'url': url,
                'status': status,
                'http_code': http_code,
                'response_time': curl_time,
                'actual_time': f"{response_time:.2f}s",
                'size': size,
                'error_type': error_type,
                'error_message': error_message,
                'attempt': attempt_num,
                'timestamp': datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
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
                    
    def show_progress(self):
        """Display progress information."""
        if self.config.quiet:
            return
            
        processed = self.stats['processed']
        total = self.stats['total']
        
        if processed == 0:
            return
            
        elapsed = time.time() - self.stats['start_time']
        rate = processed / elapsed if elapsed > 0 else 0
        eta = (total - processed) / rate if rate > 0 else 0
        
        progress = f"Progress: {processed}/{total} ({processed/total*100:.1f}%) "
        progress += f"| Active: {self.stats['active']} "
        progress += f"| Rate: {rate:.1f}/s "
        progress += f"| ETA: {eta/60:.1f}m"
        
        print(f"\r{progress}", end='', flush=True)
        
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
        
        # Process URLs with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.config.threads) as executor:
            # Submit all tasks
            future_to_url = {executor.submit(self.test_url_with_retry, url): url for url in urls}
            
            # Process completed tasks
            for future in as_completed(future_to_url):
                result = future.result()
                self.update_stats(result)
                self.write_result(result)
                
                # Show progress every 10 completed requests
                if self.stats['processed'] % 10 == 0:
                    self.show_progress()
                    
                # Log individual results in verbose mode
                if self.config.verbose:
                    status_msg = f"{result['url']}: {result['status']}"
                    if result['http_code'] != 'N/A':
                        status_msg += f" (HTTP {result['http_code']})"
                    self.logger.debug(status_msg)
                    
        # Final progress update and summary
        self.show_progress()
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