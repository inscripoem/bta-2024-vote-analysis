"""核心领域模型定义"""
import datetime
import uuid
from dataclasses import dataclass, field
from typing import Optional, Dict
import numpy as np

@dataclass
class School:
    """学校实体"""
    name: str
    location: Optional[str] = None

@dataclass
class Award:
    """奖项实体"""
    name: str
    works: list[str]

@dataclass
class VoteMetadata:
    """投票元数据"""
    submission_time: datetime.datetime
    submission_ip: str
    username: str
    email: Optional[str]
    student_id: Optional[str]
    is_student: bool

@dataclass
class Vote:
    """投票实体"""
    metadata: VoteMetadata
    school: School
    matrix: np.ndarray  
    id: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass
class Work:
    """作品实体"""
    title: str
    award_indexes: Dict[str, int]  # 每个奖项中的索引位置 {award_name: index}

@dataclass
class AnalysisResults:
    """分析结果"""
    total_avg: np.ndarray  
    total_nonzero_avg: np.ndarray  
    school_avg: Dict[str, np.ndarray]  
    school_nonzero_avg: Dict[str, np.ndarray]  
    total_school_avg: np.ndarray  
    total_school_nonzero_avg: np.ndarray   