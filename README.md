# Advanced URL Availability Checker

**Checks URLs for availability with comprehensive error handling, retry logic, and progress tracking.**

A high-performance, multi-threaded Python tool for validating URL availability with intelligent error classification, retry mechanisms, and detailed reporting. Perfect for web reconnaissance, link validation, monitoring, and quality assurance workflows.

## Features

### 🛡️ **Security-First Design**
- Built with secure `requests` library (no subprocess/curl vulnerabilities)
- Comprehensive input validation to prevent SSRF attacks
- Blocks private/local IP addresses (10.x.x.x, 192.168.x.x, 127.x.x.x, etc.)
- Path traversal protection for output files
- SSL/TLS certificate verification enforced
- Safe redirect handling with validation

### 🚀 **High Performance**
- Multi-threaded processing with configurable concurrency
- Connection pooling for optimal performance
- Real-time progress tracking with colored output (tqdm)
- Processing rate monitoring

### 🔄 **Intelligent Retry Logic**
- Exponential backoff retry mechanism (0.5s, 1s, 2s)
- Smart retry logic (skips DNS errors that won't resolve quickly)
- Configurable retry attempts per URL

### 📊 **Comprehensive Error Classification**
- **DNS Errors**: Host resolution failures
- **Connection Errors**: Network connectivity issues
- **SSL/TLS Errors**: Certificate and handshake problems
- **Timeout Errors**: Request timeouts
- **HTTP Errors**: 4xx/5xx response codes

### 📈 **Detailed Reporting**
- Multiple output formats (text, JSON)
- Separate files for active/inactive URLs
- Response time tracking
- Comprehensive statistics and summaries
- Detailed logging with configurable verbosity

### ⚙️ **Flexible Configuration**
- Multiple HTTP methods (GET, HEAD, POST)
- Custom headers and authentication
- Configurable timeouts and user agents
- Dry-run mode for validation
- Append mode for incremental checking
- Environment variable support via .env files

## Installation

### Prerequisites
- Python 3.9+
- pip (Python package manager)

### Setup
```bash
# Clone the repository
git clone https://github.com/Ap6pack/advanced-url-checker.git
cd advanced-url-checker

# Install required dependencies
pip install -r requirements.txt

# Make executable (optional)
chmod +x endpoint_checker.py
```

### Required Dependencies
- `requests` - Secure HTTP library for making requests
- `validators` - URL validation and security checks
- `python-dotenv` - Environment variable support
- `colorama` - Cross-platform colored terminal output
- `tqdm` - Progress bar functionality

## Quick Start

### Basic Usage
```bash
# Check URLs from a file
python endpoint_checker.py urls.txt

# Use 20 threads for faster processing
python endpoint_checker.py urls.txt -t 20

# JSON output with custom filename
python endpoint_checker.py urls.txt -o results/results.json --json
```

### Input File Format
Create a text file with one URL per line:
```
https://example.com
http://test.com/path
subdomain.example.org
192.168.1.1:8080
```

URLs without schemes will automatically get `http://` prepended.

## Command Line Options

### Input/Output
```bash
-o, --output FILE       Output file for results (default: results/url_check_results.txt)
--json                  Output results in JSON format
--append                Append to existing output files instead of overwriting
```

### Request Configuration
```bash
--timeout SECONDS       Request timeout (default: 10)
--connect-timeout SEC   Connection timeout (default: 5)
-r, --retries NUM       Maximum retries for failed requests (default: 2)
-m, --method METHOD     HTTP method: GET, HEAD, POST (default: GET)
--user-agent STRING     Custom user agent
--auth USER:PASS        HTTP authentication
--header HEADER         Additional headers (repeatable)
```

### Performance
```bash
-t, --threads NUM       Number of concurrent threads (default: 10)
```

### Output Control
```bash
-v, --verbose           Detailed output and logging
-q, --quiet             Minimal output (warnings/errors only)
--dry-run              Validate configuration without testing URLs
```

## Usage Examples

### Web Reconnaissance
```bash
# Check URLs from waymore output
python endpoint_checker.py waymore_results.txt -t 15 -r 3 --quiet

# Fast connectivity check with HEAD requests
python endpoint_checker.py targets.txt --method HEAD -t 25 -o results/connectivity.txt
```

### Link Validation
```bash
# Comprehensive check with detailed logging
python endpoint_checker.py website_links.txt --verbose -o results/validation_report.json --json

# Quick validation with custom timeout
python endpoint_checker.py links.txt --timeout 5 --connect-timeout 2
```

### API Endpoint Testing
```bash
# Test API endpoints with authentication
python endpoint_checker.py api_endpoints.txt --auth "user:pass" --header "Content-Type: application/json"

# POST requests to API endpoints
python endpoint_checker.py api_urls.txt --method POST --header "Authorization: Bearer token123"
```

### Monitoring
```bash
# Regular uptime monitoring
python endpoint_checker.py production_urls.txt --append -q -o results/uptime_$(date +%Y%m%d).txt
```

## Output Files

The tool generates several output files organized in dedicated directories:

| File | Description |
|------|-------------|
| `results/url_check_results.txt` | Main results with status, HTTP codes, and timing |
| `results/url_check_results_active.txt` | Only active/reachable URLs |
| `results/url_check_results_inactive.txt` | Only inactive/unreachable URLs |
| `log/url_check_results.txt.log` | Detailed execution log |

**Note**: The tool automatically creates `log/` and `results/` directories if they don't exist.

### Sample Output
```
https://example.com: ACTIVE (HTTP 200) [0.234s]
http://unreachable.test: CONNECTION_ERROR - Connection refused
https://slow-site.com: TIMEOUT - Request timed out
http://bad-dns.invalid: DNS_ERROR - Could not resolve host
```

### JSON Output Format
```json
{
  "url": "https://example.com",
  "status": "ACTIVE",
  "http_code": "200",
  "response_time": "0.234",
  "size": "1024",
  "timestamp": "2025-07-02T10:30:45.123456"
}
```

## Statistics Report

After completion, you'll see a comprehensive summary:

```
=============================================================
SUMMARY
=============================================================

Total URLs processed: 1000
Active URLs: 847 (84.7%)
Inactive URLs: 95 (9.5%)
Timeouts: 23
DNS Errors: 15
Connection Errors: 12
SSL Errors: 5
Other Errors: 3

Processing Time: 45.2s
Processing Rate: 22.1 URLs/s

Output Files:
- Main results: results/url_check_results.txt
- Active URLs: results/url_check_results_active.txt
- Inactive URLs: results/url_check_results_inactive.txt
- Log file: log/url_check_results.txt.log
```

## Integration Examples

### Use with Other Tools

**Waymore Integration:**
```bash
# Generate URLs with waymore, then validate
waymore -i target.com -oU urls.txt
python endpoint_checker.py urls.txt -t 20 --quiet -o results/live_urls.txt
```

**Filter Active URLs:**
```bash
# Get only active URLs for further processing
python endpoint_checker.py input.txt --quiet
cat results/url_check_results_active.txt | other-security-tool
```

**Continuous Monitoring:**
```bash
# Monitor URLs and alert on changes
python endpoint_checker.py critical_urls.txt --append -q
# Process results with monitoring system
```

## Advanced Usage

### Custom Headers for Specific Applications
```bash
# Bypass basic protections
python endpoint_checker.py urls.txt \
  --header "X-Forwarded-For: 127.0.0.1" \
  --header "X-Real-IP: 127.0.0.1" \
  --user-agent "Mozilla/5.0 (compatible; SecurityScanner)"
```

### High-Performance Batch Processing
```bash
# Maximum performance for large URL lists
python endpoint_checker.py huge_list.txt -t 50 --method HEAD --timeout 3 --connect-timeout 1
```

### Detailed Analysis Mode
```bash
# Full analysis with maximum information
python endpoint_checker.py urls.txt --verbose --json -o results/detailed_analysis.json -r 3
```

## Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'requests'"**
- Install dependencies: `pip install -r requirements.txt`

**Private IP addresses being blocked**
- This is a security feature to prevent SSRF attacks
- Only public IP addresses and domains are allowed

**High memory usage**
- Reduce thread count: `-t 5`
- Use HEAD requests instead of GET: `--method HEAD`

**Many timeout errors**
- Increase timeout values: `--timeout 15 --connect-timeout 5`
- Reduce concurrent threads: `-t 5`

**Permission denied on output files**
- Check directory permissions
- Ensure `log/` and `results/` directories exist and are writable
- Use different output location: `-o /tmp/results.txt`

**SSL certificate verification errors**
- The tool enforces SSL verification for security
- For testing only, you can modify the code to disable verification (not recommended)

### Performance Tuning

| Scenario | Recommended Settings |
|----------|---------------------|
| **Fast connectivity check** | `--method HEAD -t 20 --timeout 5` |
| **Thorough validation** | `-t 10 --timeout 15 -r 3 --verbose` |
| **Large lists (1000+ URLs)** | `-t 25 --method HEAD --timeout 3 -q` |
| **Slow/unreliable network** | `-t 5 --timeout 30 -r 5` |

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

### Development Setup
```bash
git clone https://github.com/Ap6pack/advanced-url-checker.git
cd advanced-url-checker
# Make your changes
# Test thoroughly
# Submit pull request
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for web reconnaissance and security testing workflows
- Optimized for use with tools like waymore, hakrawler, and other URL discovery tools
- Inspired by the need for reliable, high-performance URL validation in security assessments

---

**⭐ If you find this tool useful, please consider giving it a star on GitHub!**
