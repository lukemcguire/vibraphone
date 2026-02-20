# List available recipes
default:
    @just --list

# Install the virtual environment and install the prek hooks
install:
    @echo "🚀 Creating virtual environment using uv"
    @uv sync
    @if git rev-parse --git-dir > /dev/null 2>&1; then \
        echo "🚀 Installing prek hooks"; \
        uv run prek install; \
    else \
        echo "⚠️  Not a git repository - skipping prek hooks"; \
        echo "   Run 'git init' first, then 'just install'"; \
    fi
    @echo "✅ Setup complete! Run 'just --list' to see available commands."

# Run code quality tools
check:
    @echo "🚀 Checking lock file consistency with 'pyproject.toml'"
    @uv lock --locked
    @echo "🚀 Linting code: Running prek"
    @uv run prek run -a
    @echo "🚀 Static type checking: Running ty"
    @uv run ty check

# Test the code with pytest
test:
    @echo "🚀 Testing code: Running pytest"
    @uv run pytest --cov --cov-config=pyproject.toml --cov-report=xml

# Build wheel file
build: clean-build
    @echo "🚀 Creating wheel file"
    @uvx --from build pyproject-build --installer uv

# Clean build artifacts
clean-build:
    @echo "🚀 Removing build artifacts"
    @uv run python -c "import shutil; import os; shutil.rmtree('dist') if os.path.exists('dist') else None"

# Test if documentation can be built without warnings or errors
docs-test:
    @uv run mkdocs build -s

# Build and serve the documentation
docs:
    @uv run mkdocs serve
