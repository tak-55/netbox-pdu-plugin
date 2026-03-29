# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-29

### Release Summary
Feature release that adds automatic metrics collection, PDU metadata synchronization, and improved operational visibility.

### Added
- Periodic "Get Metrics" system job for ManagedPDU synchronization
- PDU name synchronization and display in NetBox
- `metrics_status` and `last_metrics_fetched` tracking for ManagedPDU
- `sync_metrics_enabled` control for metrics polling

### Changed
- Improved ManagedPDU forms, tables, views, and API serializers to expose new sync fields
- Updated backend handling for richer PDU metadata collection

### Fixed
- Job status cleanup now includes PDU metrics jobs on startup

### Deprecated
- N/A

### Removed
- N/A

### Security
- N/A

---

## [0.1.0] - 2026-03-22

### Release Summary
Initial release of NetBox PDU Plugin. This is a **minor** release introducing basic functionality for managing PDU resources in NetBox.

### Added
- Initial plugin structure with Pdu model
- Basic CRUD operations through NetBox UI
- Change logging and journaling support
- Custom fields and tags support
- REST API endpoints for programmatic access
- GraphQL support for flexible queries
- Comprehensive test suite
- Documentation with MkDocs

### Fixed
- N/A (initial release)

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Security
- N/A (initial release)

---

## Release Notes Template for Future Versions

When creating a new release, use this template:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Release Summary
Brief narrative summary describing the release type (major/minor/patch) and key highlights.

### **Breaking Changes**
<!-- Only include this section if there are breaking changes -->
- **[#issue]** Description of breaking change and migration path
- Link to detailed migration guide if needed

### Added
- New features and capabilities

### Fixed
- Bug fixes with issue references

### Changed
- Changes to existing functionality

### Deprecated
- Features marked for future removal

### Removed
- Features that have been removed

### Security
- Security improvements and fixes
```

---

**Best Practice**: For clear release communication, ensure each release includes:
1. Narrative summary characterizing the release type (major/minor/patch)
2. Clear indicators for bugs, features, or enhancements
3. Bold "Breaking Changes" header when applicable with migration guidance
4. Detailed changelog with issue references
