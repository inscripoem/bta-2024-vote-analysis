"""核心接口定义"""
from abc import abstractmethod
from typing import Protocol, List, Dict, Any

from .models import Vote, School, Award, Work

class IVoteRepository(Protocol):
    """投票数据仓库接口"""
    
    @abstractmethod
    def add_vote(self, vote: Vote) -> None:
        """添加投票"""
        pass
    
    @abstractmethod
    def get_votes_by_school(self, school: School) -> List[Vote]:
        """获取学校的所有投票"""
        pass
    
    @abstractmethod
    def get_vote_count_by_school(self, school: School) -> int:
        """获取学校的投票数量"""
        pass
    
    @abstractmethod
    def get_all_votes(self) -> List[Vote]:
        """获取所有投票"""
        pass

class ISchoolRepository(Protocol):
    """学校数据仓库接口"""
    
    @abstractmethod
    def add_school(self, school: School) -> None:
        """添加学校"""
        pass
    
    @abstractmethod
    def get_school_by_name(self, name: str) -> School:
        """通过名称获取学校"""
        pass
    
    @abstractmethod
    def get_all_schools(self) -> List[School]:
        """获取所有学校"""
        pass

class IAwardRepository(Protocol):
    """奖项数据仓库接口"""
    
    @abstractmethod
    def add_award(self, award: Award) -> None:
        """添加奖项"""
        pass
    
    @abstractmethod
    def get_award_by_name(self, name: str) -> Award:
        """通过名称获取奖项"""
        pass
    
    @abstractmethod
    def get_all_awards(self) -> List[Award]:
        """获取所有奖项"""
        pass

class IWorkRepository(Protocol):
    """作品数据仓库接口"""
    
    @abstractmethod
    def add_work(self, work: Work) -> None:
        """添加作品"""
        pass
    
    @abstractmethod
    def get_works_by_award(self, award: Award) -> List[Work]:
        """获取奖项的所有作品"""
        pass

class IReportGenerator(Protocol):
    """报告生成器接口"""
    
    @abstractmethod
    def generate_report(self, analysis_results: Dict[str, Any]) -> None:
        """生成报告"""
        pass

class IVoteDataLoader(Protocol):
    """投票数据加载器接口"""
    
    @abstractmethod
    def load_votes(self) -> List[Vote]:
        """加载投票数据"""
        pass 