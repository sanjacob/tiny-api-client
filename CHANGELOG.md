# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.2] - 2024-01-11

### Changed
- mypy plugin now treats most route params as required
- mypy route parsing slightly improved

## [1.2.1] - 2024-01-06

### Added
- New mypy plugin for route parameter type checking support

## [1.2.0] - 2024-01-04

### Changed
- Improved type checking support
- Refactored module to divide work in functions

## [1.1.0] - 2023-11-23

### Added
- Support for connection pooling within the same client instance

### Changed
- Member `_session` has been renamed `_cookies` to avoid confusion

## [1.0.0] - 2023-11-23

### Added
- Initial release
