# CVM Fund Data Consolidation System (RCVM175)
from .config import (
    BASE_URL, CSV_ENCODING, CSV_DELIMITER, RCVM175_URL,
    FUNDO_MAPPING, CLASSE_MAPPING, OUTPUT_COLUMNS_PRINCIPAIS, OUTPUT_COLUMNS_CLASSES
)
from .consolidator import consolidate
