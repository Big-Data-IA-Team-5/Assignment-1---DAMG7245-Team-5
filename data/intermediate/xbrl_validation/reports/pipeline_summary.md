# DVC Pipeline XBRL Validation Report

**Generated**: 2025-09-25 05:59:22
**Pipeline Stage**: xbrl_validation
**Status**: ✅ SUCCESS

## Summary
- **XBRL Facts Parsed**: 389
- **PDF Tables Processed**: 91
- **Revenue Matches Found**: 52
- **Validation Status**: PASSED

## Pipeline Integration
This stage successfully integrates with the Project LANTERN DVC pipeline:

### Dependencies Met:
- ✅ data/raw/xbrl/
- ✅ data/intermediate/tables/
- ✅ src/xbrl/
- ✅ configs/xbrl_config.yaml

### Outputs Generated:
- ✅ data/intermediate/xbrl_validation/data/xbrl_parsed_data.json
- ✅ data/intermediate/xbrl_validation/reports/validation_results.json
- ✅ data/intermediate/xbrl_validation/reports/pipeline_summary.md

## Next Stage
Ready for downstream processing in the DVC pipeline.
