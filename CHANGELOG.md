# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2025-07-02

### Added
- Comprehensive error classification system (DNS, Connection, SSL, Timeout, Other)
- Exponential backoff retry mechanism with configurable attempts
- Multi-threaded processing with ThreadPoolExecutor
- Real-time progress tracking with ETA calculations
- Processing rate monitoring and statistics
- Separate output files for active/inactive URLs
- Detailed logging with configurable verbosity levels
- JSON output format support
- Custom header support for requests
- HTTP authentication support (username:password)
- Multiple HTTP methods support (GET, HEAD, POST)
- Dry-run mode for configuration validation
- Append mode for incremental checking
- Comprehensive statistics and summary reporting
- Response time tracking and size reporting
- Session timeout and connection timeout controls
- Custom User-Agent string support

### Changed
- Improved URL validation and normalization
- Enhanced curl command construction with better error handling
- Better subprocess management with timeout controls
- Optimized file I/O operations with thread-safe writing
- Improved command-line argument parsing and validation

### Fixed
- Thread safety issues in file writing operations
- Memory usage optimization for large URL lists
- Proper handling of subprocess timeouts
- Accurate progress reporting calculations
- Error classification edge cases

### Security
- Input validation for all user-provided parameters
- Safe subprocess execution with proper timeout handling
- Secure handling of authentication credentials
- Protection against command injection in curl parameters

## [1.1.0] - 2025-06-15

### Added
- Basic retry logic for failed requests
- Error classification for common failure types
- Progress tracking functionality
- Configurable timeout settings
- Multiple output file generation
- Basic logging system

### Changed
- Improved error handling and reporting
- Enhanced URL processing logic
- Better command-line interface

### Fixed
- URL normalization issues
- Timeout handling problems
- Output file formatting inconsistencies

## [1.0.0] - 2025-06-01

### Added
- Initial release of Advanced URL Availability Checker
- Multi-threaded URL checking capability
- Basic error classification system
- Retry logic with exponential backoff
- Multiple output formats (text, JSON)
- Progress tracking and statistics
- Comprehensive command-line interface
- Support for various HTTP methods
- Custom headers and authentication
- Configurable timeouts and concurrency
- Detailed logging and reporting

### Security
- Basic input validation
- Safe subprocess execution
- Secure credential handling

---

## Release Notes

### Version 1.2.0 Highlights
This release represents a major enhancement to the URL checker with comprehensive error handling, advanced retry mechanisms, and professional-grade reporting capabilities. The tool now provides enterprise-level reliability and detailed insights for security testing workflows.

### Version 1.1.0 Highlights
Added essential retry logic and error classification to improve reliability and provide better insights into URL availability issues.

### Version 1.0.0 Highlights
Initial release providing a solid foundation for URL availability checking with multi-threading support and basic error handling.

## Contributing

Please read [CONTRIBUTORS.md](CONTRIBUTORS.md) for details on our code of conduct and the process for submitting pull requests.

## Security

For security-related issues, please see our [Security Policy](SECURITY.md).
