import numpy as np
from typing import Dict
from .managers import VoteManager
import logging

log = logging.getLogger(__name__)

class VoteAnalyzer:
    """投票数据分析器"""
    
    def __init__(self, vote_manager: VoteManager):
        self.vote_manager = vote_manager
        self.school_manager = vote_manager.school_manager
        self.matrix_size = vote_manager.vote_matrix_size
        
        # 初始化计算结果存储
        self.total_sum: np.ndarray = np.zeros(self.matrix_size)
        self.total_nonzero_count: np.ndarray = np.zeros(self.matrix_size)
        self.total_avg: np.ndarray = np.zeros(self.matrix_size)
        self.total_nonzero_avg: np.ndarray = np.zeros(self.matrix_size)
        
        self.school_sum: Dict[str, np.ndarray] = {}
        self.school_nonzero_count: Dict[str, np.ndarray] = {}
        self.school_avg: Dict[str, np.ndarray] = {}
        self.school_nonzero_avg: Dict[str, np.ndarray] = {}
        
        self.total_school_avg_sum: np.ndarray = np.zeros(self.matrix_size)
        self.total_school_nonzero_avg_sum: np.ndarray = np.zeros(self.matrix_size)
        self.total_school_avg: np.ndarray = np.zeros(self.matrix_size)
        self.total_school_nonzero_avg: np.ndarray = np.zeros(self.matrix_size)
    
    def analyze(self) -> None:
        """执行分析计算"""
        self._calculate_school_statistics()
        self._calculate_total_statistics()
        self._calculate_school_averages()
    
    def _calculate_school_statistics(self) -> None:
        """计算各学校的统计数据"""
        for school in self.school_manager.schools.values():
            log.info(f"Calculating average for school: {school.name}")
            self.school_sum[school.name] = np.zeros(self.matrix_size)
            self.school_nonzero_count[school.name] = np.zeros(self.matrix_size)
            
            for vote in self.vote_manager.get_votes_by_school(school):
                self.school_sum[school.name] += vote.matrix
                self.total_sum += vote.matrix
                self.school_nonzero_count[school.name] += np.where(vote.matrix != 0, 1, 0)
                self.total_nonzero_count += np.where(vote.matrix != 0, 1, 0)
    
    def _calculate_total_statistics(self) -> None:
        """计算总体统计数据"""
        self.total_avg = self.total_sum / len(self.vote_manager)
        self.total_nonzero_avg = np.divide(
            self.total_sum,
            self.total_nonzero_count,
            out=np.zeros_like(self.total_sum, dtype=float),
            where=self.total_nonzero_count > 0
        )
    
    def _calculate_school_averages(self) -> None:
        """计算学校平均值"""
        for school in self.school_manager.schools.values():
            vote_count = self.vote_manager.get_vote_count_by_school(school)
            self.school_avg[school.name] = self.school_sum[school.name] / vote_count
            self.school_nonzero_avg[school.name] = np.divide(
                self.school_sum[school.name],
                self.school_nonzero_count[school.name],
                out=np.zeros_like(self.school_sum[school.name], dtype=float),
                where=self.school_nonzero_count[school.name] > 0
            )
            self.total_school_avg_sum += self.school_avg[school.name]
            self.total_school_nonzero_avg_sum += self.school_nonzero_avg[school.name]
        
        self.total_school_avg = self.total_school_avg_sum / len(self.school_manager)
        self.total_school_nonzero_avg = self.total_school_nonzero_avg_sum / len(self.school_manager) 