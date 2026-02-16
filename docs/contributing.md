# Contributing

Thank you for your interest in contributing to dj-rest-auth!

## Development Setup

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/dj-rest-auth.git
cd dj-rest-auth
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -e .
pip install -r dj_rest_auth/tests/requirements.txt
```

### 4. Run Tests

```bash
python runtests.py
```

---

## Running Tests

### All Tests

```bash
python runtests.py
```

### Single Test

```bash
DJANGO_SETTINGS_MODULE=dj_rest_auth.tests.settings \
  python -m django test dj_rest_auth.tests.test_api.APIBasicTests.test_login
```

### With Coverage

```bash
coverage run ./runtests.py
coverage report
coverage html  # Generate HTML report
```

### Using Tox

Test against all supported Python and Django versions:

```bash
pip install tox
tox                  # All environments
tox -e py312-django50  # Specific environment
tox --parallel       # Run in parallel
```

---

## Code Style

We use flake8 for linting with a max line length of 120 characters.

### Check Style

```bash
flake8 dj_rest_auth/
```

### Run with Tox

```bash
tox -e flake8
```

### Configuration

See `setup.cfg` for flake8 configuration.

---

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clear, documented code
- Follow existing patterns and conventions
- Add tests for new functionality
- Update documentation if needed

### 3. Run Tests and Linting

```bash
python runtests.py
flake8 dj_rest_auth/
```

### 4. Commit Your Changes

Write clear commit messages:

```bash
git commit -m "Add support for custom token claims"
```

### 5. Push and Create a Pull Request

```bash
git push origin feature/your-feature-name
```

Then open a pull request on GitHub.

---

## Pull Request Guidelines

### What We Look For

- [ ] Tests pass on all supported Python/Django versions
- [ ] Code follows existing style (flake8 passes)
- [ ] New features include tests
- [ ] Documentation is updated if needed
- [ ] Commit messages are clear and descriptive

### What to Include

- Clear description of the change
- Link to related issue (if any)
- Screenshots for UI changes
- Migration notes for breaking changes

---

## Documentation

### Local Development

```bash
pip install mkdocs-material
mkdocs serve
```

Then visit `http://localhost:8000`.

### Building

```bash
mkdocs build
```

---

## Reporting Issues

### Bug Reports

Include:
- dj-rest-auth version
- Python version
- Django version
- Steps to reproduce
- Expected vs actual behavior

### Feature Requests

- Describe the use case
- Explain why it can't be done with current features
- Propose a solution if you have one

---

## A Note on Django-Allauth

From the maintainer:

> This project has optional and narrow support for Django-AllAuth. Pull requests that extend or add more support for Django-AllAuth will most likely be declined. The focus is on improving core functionality and potential OIDC support.

---

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

---

## Questions?

Open a [GitHub Discussion](https://github.com/iMerica/dj-rest-auth/discussions) for questions that aren't bugs or feature requests.
