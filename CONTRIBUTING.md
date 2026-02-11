# Contributing to WorkProof

Thank you for your interest in contributing to WorkProof! We welcome contributions from the community and appreciate your help in making this project better.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

## 🤝 Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone. We expect all contributors to:

- Be respectful and considerate
- Welcome newcomers and help them get started
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards other community members

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/WorkProof.git
   cd WorkProof
   ```
3. **Set up the development environment**:
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```
4. **Create a new branch** for your work:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 💡 How to Contribute

There are many ways to contribute to WorkProof:

### 🐛 Bug Fixes
- Find bugs in the [Issues](https://github.com/AshrayVB30/WorkProof/issues) section
- Look for issues labeled `bug` or `good first issue`
- Fix the bug and submit a pull request

### ✨ New Features
- Check the [Issues](https://github.com/AshrayVB30/WorkProof/issues) for feature requests
- Propose new features by creating an issue first
- Implement the feature and submit a pull request

### 📝 Documentation
- Improve README, code comments, or inline documentation
- Add examples and tutorials
- Fix typos or clarify confusing sections

### 🧪 Testing
- Add unit tests for existing functionality
- Improve test coverage
- Report bugs you find while testing

### 🎨 UI/UX Improvements
- Enhance the user interface design
- Improve user experience flows
- Add accessibility features

## 🔧 Development Workflow

1. **Make your changes** in your feature branch
2. **Test your changes** thoroughly:
   ```bash
   python main.py
   # Test the specific functionality you modified
   ```
3. **Run debug tools** to verify components:
   ```bash
   python debug_app_logic.py
   python debug_ocr_raw.py
   python debug_scraper.py
   ```
4. **Commit your changes** with clear messages
5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
6. **Create a Pull Request** on GitHub

## 📏 Coding Standards

### Python Style Guide
- Follow [PEP 8](https://pep8.org/) style guidelines
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters
- Use meaningful variable and function names

### Code Organization
- Keep functions focused and single-purpose
- Add docstrings to all functions and classes
- Use type hints where appropriate
- Keep files under 500 lines when possible

### Example:
```python
def extract_field_value(text: str, field_name: str) -> str:
    """
    Extract a specific field value from OCR text.
    
    Args:
        text: The OCR-extracted text
        field_name: Name of the field to extract
        
    Returns:
        The extracted field value, or empty string if not found
    """
    # Implementation here
    pass
```

### Comments
- Write clear, concise comments
- Explain **why**, not **what** (code should be self-explanatory)
- Update comments when you update code
- Remove commented-out code before committing

## 📝 Commit Guidelines

### Commit Message Format
```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

### Types
- `Add:` - New features or functionality
- `Fix:` - Bug fixes
- `Update:` - Improvements to existing features
- `Refactor:` - Code refactoring without changing functionality
- `Docs:` - Documentation changes
- `Style:` - Code style changes (formatting, missing semicolons, etc.)
- `Test:` - Adding or updating tests
- `Chore:` - Maintenance tasks, dependency updates

### Examples
```bash
# Good commit messages
git commit -m "Add: SSN field validation with format checking"
git commit -m "Fix: OCR extraction failing on low-contrast images"
git commit -m "Update: Improve web scraping error handling"
git commit -m "Docs: Add troubleshooting section to README"

# Bad commit messages (avoid these)
git commit -m "fixed stuff"
git commit -m "updates"
git commit -m "WIP"
```

## 🔄 Pull Request Process

1. **Update documentation** if needed (README, code comments, etc.)
2. **Ensure your code follows** the coding standards
3. **Test your changes** thoroughly
4. **Create a Pull Request** with:
   - Clear title describing the change
   - Detailed description of what was changed and why
   - Reference to related issues (e.g., "Fixes #123")
   - Screenshots for UI changes (if applicable)

### Pull Request Template
```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement

## Related Issues
Fixes #(issue number)

## Testing
Describe how you tested your changes

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] My code follows the project's coding standards
- [ ] I have tested my changes
- [ ] I have updated the documentation
- [ ] My commits have clear messages
```

## 🐛 Reporting Bugs

When reporting bugs, please include:

1. **Clear title** describing the issue
2. **Steps to reproduce** the bug
3. **Expected behavior** vs **actual behavior**
4. **Environment details**:
   - OS (Windows/macOS/Linux)
   - Python version
   - MongoDB version
   - Tesseract version
5. **Error messages** or logs (if any)
6. **Screenshots** (if applicable)

### Bug Report Template
```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g., Windows 11]
- Python: [e.g., 3.10.5]
- MongoDB: [e.g., 6.0]
- Tesseract: [e.g., 5.3.0]

**Additional context**
Any other context about the problem.
```

## 💡 Suggesting Features

We welcome feature suggestions! Please:

1. **Check existing issues** to avoid duplicates
2. **Create a new issue** with the `enhancement` label
3. **Describe the feature** in detail:
   - What problem does it solve?
   - How should it work?
   - Are there any alternatives?
4. **Provide examples** or mockups if applicable

### Feature Request Template
```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Additional context**
Any other context, screenshots, or examples.
```

## 🎯 Priority Areas

We're especially interested in contributions in these areas:

- **OCR Accuracy**: Improving text extraction and preprocessing
- **Web Scraping**: Adding support for more website structures
- **Validation Rules**: Adding new field validation logic
- **Performance**: Optimizing slow operations
- **Error Handling**: Better error messages and recovery
- **Testing**: Increasing test coverage
- **Documentation**: Examples, tutorials, and guides
- **Accessibility**: Making the UI more accessible

## 📞 Getting Help

If you need help or have questions:

- 📫 **GitHub Issues**: [Create an issue](https://github.com/AshrayVB30/WorkProof/issues)
- 💬 **Discussions**: Use GitHub Discussions for general questions
- 📧 **Email**: Contact the maintainers (see GitHub profile)

## 🙏 Thank You!

Thank you for contributing to WorkProof! Your efforts help make this project better for everyone.

---

**Happy Coding! 🚀**
