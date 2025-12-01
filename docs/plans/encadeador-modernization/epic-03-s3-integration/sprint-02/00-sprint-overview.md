# Sprint 02: S3 Integration

> **Epic**: [Epic 03: S3 Integration](../00-epic-overview.md)  
> **Duration**: 2 days  
> **Goal**: Complete S3 integration with UnitOfWork  
> **Status**: 🔄 In Progress

## Sprint Goals

1. Update Settings with S3 configuration
2. Create S3-aware UnitOfWork classes
3. Comprehensive S3 testing with moto

## Tickets

| ID | Title | Points | Status | Assignee |
|----|-------|--------|--------|----------|
| [S3-005](./ticket-005-update-settings-s3.md) | Update Settings with S3 config | 2 | ✅ | - |
| [S3-006](./ticket-006-create-s3-unitofwork.md) | Create S3UnitOfWork classes | 5 | ⬜ | - |
| [S3-007](./ticket-007-s3-repository-tests.md) | Write S3Repository tests | 3 | ⬜ | - |

**Total Points**: 10

## Ticket Dependencies

```
S3-005 (settings) ──► S3-006 (S3UnitOfWork)
                              │
Sprint 01 artifacts ──────────┤
                              │
                              └──► S3-007 (tests)
```

## Definition of Done

- [ ] All tickets completed
- [ ] Settings has S3 configuration
- [ ] S3DecompUnitOfWork downloads/uploads artifacts
- [ ] S3NewaveUnitOfWork downloads/uploads artifacts  
- [ ] All S3 operations tested with moto
- [ ] Integration test with mock S3 buckets
- [ ] Test coverage ≥80% for Epic 03 code

## Key Files Created/Modified This Sprint

```
app/
├── internal/
│   └── settings.py           # MODIFIED - S3 config
└── services/
    └── s3_unitofwork.py      # NEW

tests/
└── unit/
    └── test_s3_repository.py # NEW/EXPANDED
```

## Integration Test Scenario

```python
# End-to-end test flow
async def test_s3_decomp_chaining():
    # 1. Setup mock S3 with artifacts
    # 2. Create S3DecompUnitOfWork
    # 3. Download source relato
    # 4. Download destination deck
    # 5. Apply chaining (mock)
    # 6. Upload result
    # 7. Verify output in S3
```

## Notes

- All S3 operations must be tested with moto (no real AWS)
- UnitOfWork must handle both DECOMP and NEWAVE programs
- Settings must support custom endpoint_url for LocalStack
