# 🤝 Contributing to Codebase-to-Animated Video Tutorial Engine

Thank you for your interest in contributing! This document details guidelines and best practices for developing, testing, and submitting improvements to our codebase.

---

## 🛠️ Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/codebase-to-animated-video-tutorial-engine.git
   cd codebase-to-animated-video-tutorial-engine
   ```

2. **Setup Python environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Setup Frontend:**
   ```bash
   cd frontend
   npm install
   ```

---

## 🧪 Testing Guidelines

Before opening a pull request, ensure all test suites pass with zero regressions:

```bash
# Run backend pytest suite
pytest tests/test_auth_and_billing.py -v
pytest tests/test_graph_service.py -v
pytest tests/test_multilingual.py -v
pytest tests/test_fastapi_endpoints.py -v

# Run Python code formatting and linting
black --check app tests
flake8 app tests
```

---

## 🔀 Git Workflow & Pull Requests

1. **Branch Naming**:
   * `feat/feature-name` for new capabilities.
   * `fix/bug-description` for bug fixes.
   * `docs/documentation-update` for markdown or tutorial changes.

2. **Commit Messages**:
   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   * `feat(manim): add custom color palette option`
   * `fix(tts): correct hindi devanagari punctuation cleanup`
   * `docs(readme): add binance pay QR code tutorial`

3. **Submitting PRs**:
   * Ensure a clear summary of changes is provided.
   * Reference any linked issues.
   * Include verification test output.

---

## 📜 Code of Conduct

We are committed to providing a welcoming, inclusive, and harassment-free environment for everyone. Please be respectful and collaborative in all discussions.
