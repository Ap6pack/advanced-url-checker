# Security Policy

## Supported Versions

We actively support the following versions of the Advanced URL Availability Checker with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.3.x   | :white_check_mark: |
| 1.2.x   | :white_check_mark: |
| 1.1.x   | :x:                |
| 1.0.x   | :x:                |
| < 1.0   | :x:                |

## Reporting Security Vulnerabilities

We take security seriously. If you discover a security vulnerability in this project, please report it responsibly.

### How to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please:

1. **Email**: Send details to the project maintainer via GitHub's private vulnerability reporting feature
2. **Include**: 
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact assessment
   - Suggested fix (if you have one)
   - Your contact information

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
- **Initial Assessment**: We will provide an initial assessment within 5 business days
- **Updates**: We will keep you informed of our progress
- **Resolution**: We aim to resolve critical vulnerabilities within 30 days
- **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Considerations for Users

### Safe Usage Guidelines

This tool is designed for legitimate security testing and web reconnaissance. Please use it responsibly:

#### ⚠️ Important Warnings

- **Authorization Required**: Only test URLs you own or have explicit permission to test
- **Rate Limiting**: Use appropriate thread counts to avoid overwhelming target servers
- **Legal Compliance**: Ensure your usage complies with local laws and regulations
- **Responsible Disclosure**: If you discover vulnerabilities in tested systems, report them responsibly

#### 🛡️ Recommended Security Practices

1. **Use VPN/Proxy**: Consider using a VPN or proxy when testing external URLs
2. **Isolated Environment**: Run tests from isolated environments when possible
3. **Log Management**: Be aware that logs may contain sensitive URLs and responses
4. **Credential Security**: Never include real credentials in test files or logs
5. **Network Monitoring**: Monitor your network traffic when testing unknown URLs

### Data Handling and Privacy

#### What Data is Collected
- URLs being tested
- HTTP response codes and headers
- Response times and sizes
- Error messages and classifications
- Timestamps of requests

#### Data Storage
- All data is stored locally on your system
- No data is transmitted to external services (except the URLs being tested)
- Log files may contain sensitive information - handle appropriately
- Output files should be secured and cleaned up after use

#### Sensitive Information
- **Authentication**: Credentials are handled securely by the requests library
- **Headers**: Custom headers may contain sensitive tokens - review logs carefully
- **URLs**: URLs in input files may contain sensitive paths or parameters
- **No Credential Storage**: Authentication data is never written to disk or logs

### Security Features

#### Advanced Input Validation
- Comprehensive URL validation using the `validators` library
- Blocks private and local IP addresses to prevent SSRF attacks
- URL length limits (MAX_URL_LENGTH = 2048) to prevent buffer overflows
- Path traversal protection using `pathlib` for all file operations
- Strict validation of all user inputs

#### Secure HTTP Implementation
- Uses the `requests` library instead of subprocess/curl (eliminates command injection)
- Enforces SSL/TLS certificate verification
- Connection pooling with proper resource limits
- Manual redirect handling with security validation for each redirect
- Protection against redirect loops (MAX_REDIRECTS = 10)

#### SSRF Protection
- Blocks all private IP ranges (10.x.x.x, 192.168.x.x, 127.x.x.x, 172.16.x.x)
- Blocks link-local addresses (169.254.x.x)
- Blocks IPv6 localhost and private ranges
- Validates redirect destinations before following

#### Thread Safety
- Thread-safe file operations with proper locking
- Safe concurrent access to shared data structures
- Resource pooling with connection limits

## Known Security Considerations

### Potential Risks

1. **Information Disclosure**: 
   - Log files may contain sensitive URLs and response data
   - Error messages might reveal system information

2. **Network Exposure**:
   - Testing malicious URLs could expose your system to threats
   - High request rates might trigger security monitoring

3. **Resource Consumption**:
   - Large URL lists with high thread counts could impact system performance
   - Malicious URLs might cause resource exhaustion

### Mitigation Strategies

1. **Log Security**:
   - Regularly clean up log files
   - Use appropriate file permissions (600/640)
   - Consider log rotation for long-running operations

2. **Network Security**:
   - Use firewall rules to restrict outbound connections if needed
   - Monitor network traffic for suspicious activity
   - Consider using dedicated testing networks

3. **Resource Management**:
   - Use appropriate timeout values
   - Limit thread counts based on system capabilities
   - Monitor system resources during large operations

## Security Updates

### Update Process
- Security updates will be released as patch versions (e.g., 1.2.1)
- Critical security issues will be addressed with emergency releases
- Security advisories will be published for all security-related updates

### Notification
- Security updates will be announced in the CHANGELOG.md
- Critical vulnerabilities will be announced via GitHub Security Advisories
- Users are encouraged to subscribe to repository notifications

## Compliance and Legal

### Responsible Use
This tool is intended for:
- Legitimate security testing and assessment
- Web application monitoring and validation
- Quality assurance and testing workflows
- Educational and research purposes

### Prohibited Use
Do not use this tool for:
- Unauthorized testing of systems you don't own
- Denial of service attacks or system disruption
- Circumventing security measures without permission
- Any illegal or malicious activities

### Disclaimer
Users are responsible for ensuring their use of this tool complies with:
- Local and international laws
- Terms of service of tested systems
- Organizational policies and procedures
- Ethical guidelines for security testing

## Contact

For security-related questions or concerns:
- Use GitHub's private vulnerability reporting feature
- Contact the project maintainer through GitHub
- Check existing security advisories and discussions

---

**Remember**: Security is a shared responsibility. Use this tool ethically and responsibly.
