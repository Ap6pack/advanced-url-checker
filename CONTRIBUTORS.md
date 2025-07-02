# Contributors

This document recognizes the people who have contributed to the Advanced URL Availability Checker project and provides guidelines for new contributors.

## Project Maintainer

**Adam Rhys Heaton** - *Creator and Lead Maintainer*
- GitHub: [@Ap6pack](https://github.com/Ap6pack)
- Role: Project founder, primary developer, and maintainer
- Contributions: Initial project creation, core architecture, and ongoing development

## How to Contribute

We welcome contributions from the community! There are many ways to contribute to this project:

### Types of Contributions

#### 🐛 Bug Reports
- Report bugs using GitHub Issues
- Include detailed reproduction steps
- Provide system information and error messages
- Use the bug report template

#### 💡 Feature Requests
- Suggest new features or enhancements
- Explain the use case and expected behavior
- Use the feature request template

#### 📝 Documentation
- Improve README, code comments, or examples
- Fix typos or clarify instructions
- Add usage examples or tutorials

#### 🔧 Code Contributions
- Fix bugs or implement new features
- Improve performance or code quality
- Add tests for new functionality

#### 🧪 Testing
- Test the tool in different environments
- Report compatibility issues
- Contribute test cases

## Getting Started

### Development Setup

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/Ap6pack/advanced-url-checker.git
   cd advanced-url-checker
   ```

2. **Set up your environment**
   ```bash
   # Ensure you have Python 3.9+ installed
   python3 --version
   
   # Ensure curl is installed
   curl --version
   
   # No additional dependencies needed - uses Python standard library only!
   ```

3. **Create a branch for your changes**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

### Development Guidelines

#### Code Style
- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add docstrings to classes and functions
- Keep functions focused and modular
- Use type hints where appropriate

#### Testing
- Test your changes thoroughly before submitting
- Test with various URL types and edge cases
- Verify functionality across different systems
- Include test cases for new features

#### Documentation
- Update README.md if adding new features
- Update CHANGELOG.md following Keep a Changelog format
- Add inline comments for complex logic
- Update help text for new command-line options

### Pull Request Process

1. **Before submitting:**
   - Ensure your code follows the style guidelines
   - Test your changes thoroughly
   - Update documentation as needed
   - Add your changes to CHANGELOG.md under [Unreleased]

2. **Submitting your PR:**
   - Use a clear, descriptive title
   - Fill out the pull request template
   - Reference any related issues
   - Include screenshots for UI changes (if applicable)

3. **Review process:**
   - Maintainers will review your PR
   - Address any feedback or requested changes
   - Once approved, your PR will be merged

### Branch Naming Convention

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test improvements

### Commit Message Guidelines

Use clear, descriptive commit messages:

```
type: brief description

Longer explanation if needed

Fixes #issue-number
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat: add support for custom SSL certificate validation`
- `fix: resolve thread safety issue in file writing`
- `docs: update installation instructions for macOS`

## Code of Conduct

### Our Pledge

We are committed to making participation in this project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- The use of sexualized language or imagery
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project maintainer. All complaints will be reviewed and investigated promptly and fairly.

## Recognition

Contributors will be recognized in the following ways:

- **Code Contributors**: Listed in this file with their contributions
- **Issue Reporters**: Credited in CHANGELOG.md when issues are resolved
- **Documentation Contributors**: Acknowledged in commit messages and releases
- **Community Contributors**: Recognized for helping others and improving the project

## Questions?

If you have questions about contributing:

1. Check existing [Issues](https://github.com/Ap6pack/advanced-url-checker/issues) and [Discussions](https://github.com/Ap6pack/advanced-url-checker/discussions)
2. Create a new issue with the "question" label
3. Contact the maintainer through GitHub

## License

By contributing to this project, you agree that your contributions will be licensed under the same [MIT License](LICENSE) that covers the project.

---

Thank you for your interest in contributing to the Advanced URL Availability Checker! 🚀

*This project follows the [Contributor Covenant](https://www.contributor-covenant.org/) code of conduct.*
