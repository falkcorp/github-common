### Fixed

- reusable-ci: Playwright browsers are now installed as the runner user (only the system dependencies use sudo), so the E2E step finds them in the runner cache instead of failing with "Executable doesn't exist".
