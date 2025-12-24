# Sequence 11: Attachments

*Parent: [USER_STORIES.md](../USER_STORIES.md)*

File attachment capabilities for items. Users can attach supporting documents, images, and files to RAID items for reference.

**Depends on**: Sequences 3 (Core Data), 8 (Multi-Org)
**Stories**: 3
**Priority**: Post-MVP

**Key Concepts**:
- Files stored in S3, metadata in database
- Signed URLs for secure access
- Per-org storage isolation
- File size limits enforced

---

## S11-001: File Upload

**Story**: As a user, I want to upload files to items, so that I can attach supporting documents.

**Acceptance Criteria**:
- Upload button on item edit dialog
- Support images (jpg, png, gif), documents (pdf, docx), spreadsheets (xlsx)
- File size limit enforced (10MB per file)
- Progress indicator during upload
- Files stored in S3

**Traces**: ENT-005

---

## S11-002: File Display

**Story**: As a user, I want to view attached files, so that I can access item documentation.

**Acceptance Criteria**:
- Attachment list on item detail
- Images display inline with lightbox
- Documents downloadable via signed URL
- File metadata shown (name, size, upload date)

**Traces**: ENT-005

---

## S11-003: File Management

**Story**: As a user, I want to manage attachments, so that I can remove outdated files.

**Acceptance Criteria**:
- Delete attachment option
- Confirmation before delete
- Only uploader or admin can delete
- Audit log entry on delete

**Traces**: ENT-005
