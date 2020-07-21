# github_archive
Small utility for archiving github repositories and development information.

Current support is for archiving repositories under an Organization.  

# Usage
Simply create a configuration file, an example is provided in [config.yaml.example](config.yaml.example) and pass it to the module.

```python -m github_scrape --config-yaml config.yaml```

If `--config-yaml ` is not passed, will look for `config.yaml` in the current working directory.  
# Output
The module will read the organization presented in the config, iterate over all repositories that are accessible via the provided `token`, and create a `tar.gz` archive containing the code (with full version history), as well as json formatted documents containing meta data such as:
- issues
- comments
- pull requests
- code review comments

If the repository has an initialized wiki, the wiki repository is also cloned and included in the archive.

Wiki support has a bug where the GitHub API returns `True` for all calls to `has_wiki`, workaround in progress.

Support for archiving GitHub Project meta data is in development.
