"""数据持久化实现"""
import logging
from typing import Dict, List
from pypinyin import lazy_pinyin

from ..core.models import Vote, School, Award, Work
from ..core.ports import IVoteRepository, ISchoolRepository, IAwardRepository, IWorkRepository

log = logging.getLogger(__name__)

class InMemoryVoteRepository(IVoteRepository):
    """内存投票仓库"""

    def __init__(self) -> None:
        log.debug("初始化内存投票仓库")
        self.votes: Dict[str, Vote] = {}
        self.school_votes: Dict[str, List[Vote]] = {}

    def add_vote(self, vote: Vote) -> None:
        """添加投票"""
        log.debug(f"添加投票：ID={vote.id}，学校={vote.school.name}")
        self.votes[str(vote.id)] = vote
        
        school_name = vote.school.name
        if school_name not in self.school_votes:
            log.debug(f"为学校 {school_name} 创建新的投票列表")
            self.school_votes[school_name] = []
        self.school_votes[school_name].append(vote)
        log.debug(f"学校 {school_name} 当前投票数：{len(self.school_votes[school_name])}")

    def get_votes_by_school(self, school: School) -> List[Vote]:
        """获取学校的所有投票"""
        log.debug(f"获取学校 {school.name} 的所有投票")
        votes = self.school_votes.get(school.name, [])
        log.debug(f"找到 {len(votes)} 条投票")
        return votes

    def get_vote_count_by_school(self, school: School) -> int:
        """获取学校的投票数量"""
        count = len(self.school_votes.get(school.name, []))
        log.debug(f"学校 {school.name} 的投票数量：{count}")
        return count

    def get_all_votes(self) -> List[Vote]:
        """获取所有投票"""
        votes = list(self.votes.values())
        log.debug(f"获取所有投票，总数：{len(votes)}")
        return votes

class InMemorySchoolRepository(ISchoolRepository):
    """内存学校仓库"""

    def __init__(self) -> None:
        log.debug("初始化内存学校仓库")
        self.schools: Dict[str, School] = {}

    def add_school(self, school: School) -> None:
        """添加学校"""
        log.debug(f"添加学校：{school.name}")
        if school.name in self.schools:
            log.error(f"学校 {school.name} 已存在")
            raise ValueError("学校已存在")
        self.schools[school.name] = school
        log.debug(f"学校 {school.name} 添加成功")

    def get_school_by_name(self, name: str) -> School:
        """通过名称获取学校"""
        log.debug(f"通过名称获取学校：{name}")
        try:
            school = self.schools[name]
            log.debug(f"找到学校：{school.name}")
            return school
        except KeyError:
            log.error(f"未找到学校：{name}")
            raise

    def get_all_schools(self) -> List[School]:
        """获取所有学校"""
        schools = sorted(self.schools.values(), key=lambda x: lazy_pinyin(x.name))
        log.debug(f"获取所有学校，总数：{len(schools)}")
        return schools

    def update_school_locations(self, locations_data: List[Dict[str, str]]) -> None:
        """更新学校位置信息"""
        log.debug(f"开始更新学校位置信息，数据条数：{len(locations_data)}")
        for data in locations_data:
            if data["name"] in self.schools:
                log.debug(f"更新学校 {data['name']} 的位置信息：{data['location']}")
                self.schools[data["name"]].location = data["location"]
            else:
                log.warning(f"未找到要更新位置的学校：{data['name']}")

class InMemoryAwardRepository(IAwardRepository):
    """内存奖项仓库"""

    def __init__(self) -> None:
        log.debug("初始化内存奖项仓库")
        self.awards: Dict[str, Award] = {}

    def add_award(self, award: Award) -> None:
        """添加奖项"""
        log.debug(f"添加奖项：{award.name}")
        if award.name in self.awards:
            log.error(f"奖项 {award.name} 已存在")
            raise ValueError("奖项已存在")
        self.awards[award.name] = award
        log.debug(f"奖项 {award.name} 添加成功")

    def get_award_by_name(self, name: str) -> Award:
        """通过名称获取奖项"""
        log.debug(f"通过名称获取奖项：{name}")
        try:
            award = self.awards[name]
            log.debug(f"找到奖项：{award.name}")
            return award
        except KeyError:
            log.error(f"未找到奖项：{name}")
            raise

    def get_all_awards(self) -> List[Award]:
        """获取所有奖项"""
        awards = list(self.awards.values())
        log.debug(f"获取所有奖项，总数：{len(awards)}")
        return awards

class InMemoryWorkRepository(IWorkRepository):
    """内存作品仓库"""

    def __init__(self) -> None:
        self.works: Dict[str, Work] = {}
        self.works_by_award: Dict[str, List[Work]] = {}

    def add_work(self, work: Work) -> None:
        """添加作品"""
        if work.title not in self.works:
            self.works[work.title] = work
        else:
            # 更新现有作品的award_indexes
            self.works[work.title].award_indexes.update(work.award_indexes)
            work = self.works[work.title]
        
        # 更新works_by_award
        for award_name in work.award_indexes:
            if award_name not in self.works_by_award:
                self.works_by_award[award_name] = []
            if work not in self.works_by_award[award_name]:
                self.works_by_award[award_name].append(work)

    def get_works_by_award(self, award: Award) -> List[Work]:
        """获取奖项的所有作品"""
        return sorted(
            self.works_by_award.get(award.name, []),
            key=lambda x: x.award_indexes[award.name]
        ) 