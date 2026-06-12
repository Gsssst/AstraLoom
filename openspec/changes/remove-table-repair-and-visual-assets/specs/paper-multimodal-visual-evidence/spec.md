## REMOVED Requirements

### Requirement: PDF Visual Asset Extraction
**Reason**: The current visual asset extraction implementation is being discarded so paper multimodal support can be redesigned from a clean baseline.
**Migration**: Remove user-facing extraction actions, runtime services, and API fields. Future visual evidence support must be proposed as a new OpenSpec change.

### Requirement: Optional Visual Summaries
**Reason**: Visual summaries depend on the discarded visual asset runtime.
**Migration**: Remove summary backfill actions and ignore historical summary metadata in active APIs.

### Requirement: Visual Evidence Retrieval Lane
**Reason**: The current visual evidence lane depends on discarded visual assets.
**Migration**: Paper Q&A returns to text and structured table evidence only until a new visual strategy is designed.

### Requirement: Visual Evidence References
**Reason**: Frontend visual evidence cards and image routes are being removed.
**Migration**: Evidence references no longer include visual asset metadata.

### Requirement: Visual Coverage Transparency
**Reason**: The product will no longer advertise visual analysis coverage in the current baseline.
**Migration**: Do not show visual coverage or visual-missing prompts until the replacement feature exists.
