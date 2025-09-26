"""
Comprehensive Metadata Schema Configuration
Defines the complete structure for extracting ALL document elements
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json

@dataclass
class BoundingBox:
    """Bounding box coordinates"""
    x1: float
    y1: float
    x2: float
    y2: float
    
    def to_dict(self) -> Dict[str, float]:
        return {"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2}

@dataclass
class TableInfo:
    """Extended metadata for table content"""
    rows: int
    cols: int
    table_id: int
    extraction_method: str
    file_name: str
    has_headers: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rows": self.rows,
            "cols": self.cols,
            "table_id": self.table_id,
            "extraction_method": self.extraction_method,
            "file_name": self.file_name,
            "has_headers": self.has_headers
        }

@dataclass
class ImageInfo:
    """Extended metadata for image content"""
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    alt_text: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in {
            "width": self.width,
            "height": self.height, 
            "format": self.format,
            "alt_text": self.alt_text
        }.items() if v is not None}

@dataclass
class LayoutInfo:
    """Layout and formatting information"""
    font_size: Optional[float] = None
    font_family: Optional[str] = None
    is_bold: Optional[bool] = None
    is_italic: Optional[bool] = None
    text_color: Optional[str] = None
    background_color: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in {
            "font_size": self.font_size,
            "font_family": self.font_family,
            "is_bold": self.is_bold,
            "is_italic": self.is_italic,
            "text_color": self.text_color,
            "background_color": self.background_color
        }.items() if v is not None}

@dataclass
class SectionInfo:
    """Section hierarchy and structure information"""
    title: Optional[str] = None
    level: Optional[int] = None
    content_length: Optional[int] = None
    section_number: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in {
            "title": self.title,
            "level": self.level,
            "content_length": self.content_length,
            "section_number": self.section_number
        }.items() if v is not None}

@dataclass
class AIAnalysisInfo:
    """AI/ML analysis results and metadata"""
    model_name: Optional[str] = None
    analysis_type: Optional[str] = None
    entities_detected: List[str] = field(default_factory=list)
    sentiment_score: Optional[float] = None
    topics: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.model_name:
            result["model_name"] = self.model_name
        if self.analysis_type:
            result["analysis_type"] = self.analysis_type
        if self.entities_detected:
            result["entities_detected"] = self.entities_detected
        if self.sentiment_score is not None:
            result["sentiment_score"] = self.sentiment_score
        if self.topics:
            result["topics"] = self.topics
        return result

@dataclass
class MetadataRecord:
    """Complete metadata record structure"""
    
    # Core identification fields (REQUIRED)
    doc_id: str
    company: str
    fiscal_year: str
    source_path: str
    extraction_timestamp: str
    
    # Document structure fields (REQUIRED)
    page: int
    section: str
    block_type: str
    text: str
    
    # Processing metadata (REQUIRED)
    extraction_method: str
    
    # Optional fields
    confidence: float = 1.0
    bbox: Optional[BoundingBox] = None
    
    # Extended metadata (optional, specific to content type)
    table_info: Optional[TableInfo] = None
    image_info: Optional[ImageInfo] = None
    layout_info: Optional[LayoutInfo] = None
    section_info: Optional[SectionInfo] = None
    ai_analysis: Optional[AIAnalysisInfo] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "doc_id": self.doc_id,
            "company": self.company,
            "fiscal_year": self.fiscal_year,
            "source_path": self.source_path,
            "extraction_timestamp": self.extraction_timestamp,
            "page": self.page,
            "section": self.section,
            "block_type": self.block_type,
            "text": self.text,
            "extraction_method": self.extraction_method,
            "confidence": self.confidence
        }
        
        # Add bbox if present
        if self.bbox:
            result["bbox"] = self.bbox.to_dict()
        else:
            result["bbox"] = None
            
        # Add extended metadata if present
        if self.table_info:
            result["table_info"] = self.table_info.to_dict()
        if self.image_info:
            result["image_info"] = self.image_info.to_dict()
        if self.layout_info:
            result["layout_info"] = self.layout_info.to_dict()
        if self.section_info:
            result["section_info"] = self.section_info.to_dict()
        if self.ai_analysis:
            result["ai_analysis"] = self.ai_analysis.to_dict()
            
        return result
    
    def to_jsonl(self) -> str:
        """Convert to JSONL format string"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetadataRecord':
        """Create MetadataRecord from dictionary"""
        # Extract extended metadata
        table_info = None
        if "table_info" in data and data["table_info"]:
            ti = data["table_info"]
            table_info = TableInfo(
                rows=ti.get("rows", 0),
                cols=ti.get("cols", 0),
                table_id=ti.get("table_id", 0),
                extraction_method=ti.get("extraction_method", ""),
                file_name=ti.get("file_name", ""),
                has_headers=ti.get("has_headers", False)
            )
            
        bbox = None
        if "bbox" in data and data["bbox"]:
            b = data["bbox"]
            bbox = BoundingBox(
                x1=b.get("x1", 0),
                y1=b.get("y1", 0),
                x2=b.get("x2", 0),
                y2=b.get("y2", 0)
            )
            
        return cls(
            doc_id=data["doc_id"],
            company=data["company"],
            fiscal_year=data["fiscal_year"],
            source_path=data["source_path"],
            extraction_timestamp=data["extraction_timestamp"],
            page=data["page"],
            section=data["section"],
            block_type=data["block_type"],
            text=data["text"],
            extraction_method=data["extraction_method"],
            confidence=data.get("confidence", 1.0),
            bbox=bbox,
            table_info=table_info
        )

class BlockType:
    """Standardized block types for document elements"""
    
    # Text content types
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    SUBHEADING = "subheading"
    HEADER = "header"
    FOOTER = "footer"
    CAPTION = "caption"
    FOOTNOTE = "footnote"
    TEXT_BLOCK = "text_block"
    STRUCTURED_CONTENT = "structured_content"
    
    # Table and data types
    TABLE = "table"
    TABLE_HEADER = "table_header"
    TABLE_CELL = "table_cell"
    LIST = "list"
    LIST_ITEM = "list_item"
    
    # Visual elements
    IMAGE = "image"
    CHART = "chart"
    DIAGRAM = "diagram"
    SIGNATURE = "signature"
    LOGO = "logo"
    
    # Layout elements
    COLUMN = "column"
    TEXT_REGION = "text_region"
    LAYOUT_BLOCK = "layout_block"
    
    # Special content
    FORM_FIELD = "form_field"
    CHECKBOX = "checkbox"
    BARCODE = "barcode"
    QR_CODE = "qr_code"
    
    # Analysis results
    AI_ANALYSIS = "ai_analysis"
    DOCLING_SECTION = "docling_section"
    GOOGLE_AI_ENTITY = "google_ai_entity"
    
    # Fallback
    UNKNOWN = "unknown"
    
    @classmethod
    def get_all_types(cls) -> List[str]:
        """Get all valid block types"""
        return [
            cls.PARAGRAPH, cls.HEADING, cls.SUBHEADING, cls.HEADER, cls.FOOTER,
            cls.CAPTION, cls.FOOTNOTE, cls.TEXT_BLOCK, cls.STRUCTURED_CONTENT,
            cls.TABLE, cls.TABLE_HEADER, cls.TABLE_CELL, cls.LIST, cls.LIST_ITEM,
            cls.IMAGE, cls.CHART, cls.DIAGRAM, cls.SIGNATURE, cls.LOGO,
            cls.COLUMN, cls.TEXT_REGION, cls.LAYOUT_BLOCK,
            cls.FORM_FIELD, cls.CHECKBOX, cls.BARCODE, cls.QR_CODE,
            cls.AI_ANALYSIS, cls.DOCLING_SECTION, cls.GOOGLE_AI_ENTITY,
            cls.UNKNOWN
        ]

class ExtractionMethod:
    """Standardized extraction method names"""
    
    # Text extraction methods
    PDFPLUMBER_TEXT = "pdfplumber_text"
    PYPDF_TEXT = "pypdf_text"
    DOCLING_TEXT = "docling_text"
    GOOGLE_AI_TEXT = "google_ai_text"
    
    # Table extraction methods
    CAMELOT_STREAM = "camelot_stream"
    CAMELOT_LATTICE = "camelot_lattice"
    PDFPLUMBER_TABLE = "pdfplumber_table"
    TABULA = "tabula"
    HYBRID_TABLE_CAMELOT_STREAM = "hybrid_table_extraction_camelot_stream"
    HYBRID_TABLE_PDFPLUMBER = "hybrid_table_extraction_pdfplumber"
    
    # Layout analysis methods
    LAYOUT_DETECTION = "layout_detection"
    GOOGLE_AI_LAYOUT = "google_ai_layout"
    DOCLING_LAYOUT = "docling_layout"
    
    # AI/ML methods
    DOCLING_AI_ANALYSIS = "docling_ai_analysis"
    DOCLING_MARKDOWN_EXTRACTION = "docling_markdown_extraction"
    GOOGLE_DOCUMENT_AI = "google_document_ai"
    OPENAI_ANALYSIS = "openai_analysis"
    
    # Combined methods
    HYBRID_EXTRACTION = "hybrid_extraction"
    UNIFIED_EXTRACTION = "unified_extraction"
    MULTI_METHOD_EXTRACTION = "multi_method_extraction"
    
    # Fallback
    MANUAL_EXTRACTION = "manual_extraction"
    UNKNOWN_METHOD = "unknown_method"

class MetadataValidator:
    """Validates metadata records against schema"""
    
    @staticmethod
    def validate_record(record: Dict[str, Any]) -> List[str]:
        """Validate a metadata record and return list of errors"""
        errors = []
        
        # Check required fields
        required_fields = [
            "doc_id", "company", "fiscal_year", "source_path", 
            "extraction_timestamp", "page", "section", "block_type", 
            "text", "extraction_method"
        ]
        
        for field in required_fields:
            if field not in record or not record[field]:
                errors.append(f"Missing required field: {field}")
                
        # Validate data types
        if "page" in record and not isinstance(record["page"], int):
            errors.append("Page must be an integer")
            
        if "confidence" in record:
            conf = record["confidence"]
            if not isinstance(conf, (int, float)) or conf < 0 or conf > 1:
                errors.append("Confidence must be a number between 0 and 1")
                
        # Validate block type
        if "block_type" in record:
            if record["block_type"] not in BlockType.get_all_types():
                errors.append(f"Invalid block_type: {record['block_type']}")
                
        return errors
    
    @staticmethod
    def validate_completeness(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate completeness of extraction across document"""
        stats = {
            "total_records": len(records),
            "pages_covered": set(),
            "block_types": {},
            "extraction_methods": {},
            "missing_text_pages": [],
            "table_only_pages": [],
            "has_comprehensive_coverage": False
        }
        
        for record in records:
            page = record.get("page", 0)
            block_type = record.get("block_type", "unknown")
            method = record.get("extraction_method", "unknown")
            
            stats["pages_covered"].add(page)
            stats["block_types"][block_type] = stats["block_types"].get(block_type, 0) + 1
            stats["extraction_methods"][method] = stats["extraction_methods"].get(method, 0) + 1
        
        # Convert set to sorted list
        pages_list = sorted(list(stats["pages_covered"]))
        stats["pages_covered"] = pages_list
        
        # Check for comprehensive coverage
        has_text = any("text" in method or block_type in [BlockType.PARAGRAPH, BlockType.HEADING] 
                      for method, block_type in [(r.get("extraction_method", ""), r.get("block_type", "")) 
                                               for r in records])
        has_tables = BlockType.TABLE in stats["block_types"]
        has_structure = any(bt in stats["block_types"] for bt in [BlockType.HEADING, BlockType.SUBHEADING])
        
        stats["has_comprehensive_coverage"] = has_text and has_tables and has_structure
        
        return stats

# Helper functions for creating records
def create_text_record(doc_id: str, company: str, fiscal_year: str, source_path: str,
                      page: int, text: str, section: str = None, 
                      block_type: str = BlockType.PARAGRAPH,
                      method: str = ExtractionMethod.PDFPLUMBER_TEXT,
                      confidence: float = 0.9, bbox: BoundingBox = None) -> MetadataRecord:
    """Helper to create text-based metadata record"""
    return MetadataRecord(
        doc_id=doc_id,
        company=company,
        fiscal_year=fiscal_year,
        source_path=source_path,
        extraction_timestamp=datetime.now().isoformat(),
        page=page,
        section=section or f"Page {page}",
        block_type=block_type,
        text=text,
        extraction_method=method,
        confidence=confidence,
        bbox=bbox
    )

def create_table_record(doc_id: str, company: str, fiscal_year: str, source_path: str,
                       page: int, text: str, table_info: TableInfo,
                       section: str = None, confidence: float = 0.85,
                       bbox: BoundingBox = None) -> MetadataRecord:
    """Helper to create table metadata record"""
    return MetadataRecord(
        doc_id=doc_id,
        company=company,
        fiscal_year=fiscal_year,
        source_path=source_path,
        extraction_timestamp=datetime.now().isoformat(),
        page=page,
        section=section or f"Page {page} - Table {table_info.table_id}",
        block_type=BlockType.TABLE,
        text=text,
        extraction_method=f"hybrid_table_extraction_{table_info.extraction_method}",
        confidence=confidence,
        bbox=bbox,
        table_info=table_info
    )

# Processing guidelines
PROCESSING_GUIDELINES = {
    "text_processing": [
        "Extract ALL text content, not just tables",
        "Preserve paragraph structure and formatting",
        "Identify headings, subheadings, and hierarchical structure", 
        "Capture headers, footers, and page-level metadata",
        "Extract lists, captions, and footnotes"
    ],
    "content_prioritization": [
        "Financial data and tables (highest priority)",
        "Main document text and narratives",
        "Headings and structural elements", 
        "Captions and supplementary text",
        "Headers, footers, and metadata"
    ],
    "quality_standards": [
        "Minimum text length: 10 characters (except for structural elements)",
        "Maximum chunk size: 2000 characters (split longer content)",
        "Preserve meaningful whitespace and formatting",
        "Include confidence scores for all extractions"
    ],
    "coverage_requirements": [
        "Every page must have at least one text record",
        "Tables AND surrounding text must both be extracted",
        "Document structure (TOC, sections) must be preserved", 
        "All visible text content should be captured"
    ]
}