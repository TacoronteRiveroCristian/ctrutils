from dataclasses import dataclass
from typing import Dict, List


@dataclass
class MeasurementSchema:
    """Schema definition for a measurement"""
    name: str
    fields: Dict[str, str]  # field_name -> field_type
    tags: Dict[str, List[str]]  # tag_name -> possible_values
    frequency: str  # pandas frequency string


@dataclass
class DatabaseSchema:
    """Schema definition for a database"""
    name: str
    description: str
    measurements: List[MeasurementSchema]
