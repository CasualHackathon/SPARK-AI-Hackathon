# GitHub Actions Workflows for Spoon Core

This directory contains GitHub Actions workflows for automated testing, building, and publishing of the Spoon AI SDK Python package.

## Workflows Overview

### 1. CI Workflow (`ci.yml`)
- **Trigger**: Push to `main`/`develop` branches, Pull Requests
- **Purpose**: Build package and verify compatibility across Python versions
- **Features**:
  - Multi-Python version build verification (3.11, 3.12, 3.13)
  - Package build and validation
  - Artifact upload for releases
  - No testing - focuses on build verification only

### 2. Release Workflow (`release.yml`)
- **Trigger**: Push of version tags (e.g., `v1.2.3`)
- **Purpose**: Automatically publish to PyPI and create GitHub releases
- **Features**:
  - Build package distribution
  - Upload to PyPI using API token
  - Create GitHub release with changelog

### 3. Version Bump Workflow (`version-bump.yml`)
- **Trigger**: Manual workflow dispatch
- **Purpose**: Automated version management and tagging
- **Features**:
  - Support for patch/minor/major version bumps
  - Custom version input option
  - Automatic commit and tag creation
  - Push to repository

## Setup Instructions

### 1. PyPI API Token Setup

1. Go to [PyPI](https://pypi.org/) and log in
2. Go to Account Settings → API tokens
3. Create a new API token with scope for your project
4. In your GitHub repository, go to Settings → Secrets and variables → Actions
5. Add a new repository secret named `PYPI_API_TOKEN` with your token value

### 2. Repository Settings

Ensure your repository has the following settings:

- **Actions permissions**: Allow actions to create and approve pull requests
- **Workflow permissions**: Read and write permissions for GITHUB_TOKEN

### 3. Branch Protection (Recommended)

Set up branch protection for `main` branch:
- Require status checks to pass
- Require branches to be up to date
- Include administrators in restrictions

## Usage

### Automatic Release Process

1. **Version Bump**: Use the Version Bump workflow to increment version
   - Go to Actions → Version Bump and Tag → Run workflow
   - Choose version type (patch/minor/major) or enter custom version

2. **Automatic Publishing**: When a version tag is pushed, the release workflow automatically:
   - Builds the package
   - Publishes to PyPI
   - Creates a GitHub release

### Manual Version Management

If you prefer manual version management:

1. Update version in `pyproject.toml`
2. Commit changes: `git commit -m "Bump version to x.y.z"`
3. Create tag: `git tag vx.y.z`
4. Push: `git push && git push --tags`

## Workflow Details

### CI Workflow
```yaml
# Runs on every push/PR
- Multi-version Python build verification
- Package build and twine check
- Upload build artifacts
- No testing - focuses on build verification only
```

### Release Workflow
```yaml
# Runs on version tags
- Checkout code
- Setup Python 3.11
- Install build tools
- Build package (sdist + wheel)
- Upload to PyPI
- Create GitHub release
```

### Version Bump Workflow
```yaml
# Manual trigger
- Checkout with write permissions
- Install bump2version
- Calculate new version
- Update pyproject.toml
- Commit and tag
- Push changes
```

## Dependencies

The following tools are used in the workflows:

- `build`: Package building
- `twine`: PyPI uploading
- `pytest`: Testing framework
- `pytest-cov`: Coverage reporting
- `pytest-asyncio`: Async test support
- `tox`: Multi-environment testing
- `bump2version`: Version management

## Testing Configuration

The CI workflow uses both pytest and tox for comprehensive testing:

### pytest Configuration
- Located in `tests/pytest.ini`
- Asyncio mode: auto
- Coverage reporting enabled

### tox Configuration
- Located in `tox.ini`
- Supports Python versions: 3.9, 3.10, 3.11, 3.12, 3.13
- Isolated build environments
- Coverage reporting support

## Troubleshooting

### Common Issues

1. **PyPI Upload Fails**
   - Check `PYPI_API_TOKEN` secret is set correctly
   - Verify token has upload permissions for the project

2. **Tests Fail**
   - Check Python version compatibility (requires >=3.10)
   - Ensure all dependencies are in `requirements.txt`
   - Verify test configuration in `pytest.ini`

3. **Build Fails**
   - Check `pyproject.toml` configuration
   - Ensure package structure matches `setuptools` configuration
   - Verify Python version compatibility

### Debug Mode

To debug workflow issues:
1. Go to Actions tab in GitHub
2. Select the failed workflow run
3. Check logs for each step
4. Use `debug` logging level if available

## Contributing

When contributing to the workflows:

1. Test changes on a feature branch first
2. Update this documentation if workflows change
3. Ensure backward compatibility
4. Follow GitHub Actions best practices

## Security Notes

- Never commit secrets to the repository
- Use repository secrets for sensitive data
- Regularly rotate API tokens
- Limit token scopes to minimum required permissions
