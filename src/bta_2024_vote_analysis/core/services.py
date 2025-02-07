"""核心业务服务"""
import logging
from dataclasses import dataclass
from typing import Dict, Any, List
import numpy as np

from .models import Vote, School, Award, AnalysisResults
from .ports import (
    IVoteRepository,
    ISchoolRepository,
    IAwardRepository,
    IWorkRepository,
    IReportGenerator,
    IVoteDataLoader
)

log = logging.getLogger(__name__)

@dataclass
class VotingService:
    """投票服务"""
    vote_repo: IVoteRepository
    school_repo: ISchoolRepository
    award_repo: IAwardRepository
    work_repo: IWorkRepository

    def add_vote(self, vote: Vote) -> None:
        """添加投票"""
        log.debug(f"正在添加来自学校 {vote.school.name} 的投票")
        self.vote_repo.add_vote(vote)
        log.debug(f"成功添加来自学校 {vote.school.name} 的投票")

    def get_school_statistics(self, school: School) -> Dict[str, Any]:
        """获取学校统计信息"""
        log.debug(f"正在获取学校 {school.name} 的统计信息")
        votes = self.vote_repo.get_votes_by_school(school)
        stats = {
            "vote_count": len(votes),
            "votes": votes
        }
        log.debug(f"学校 {school.name} 的统计信息：投票数量={len(votes)}")
        return stats

@dataclass
class AnalysisService:
    """分析服务"""
    vote_repo: IVoteRepository
    school_repo: ISchoolRepository
    award_repo: IAwardRepository
    work_repo: IWorkRepository
    report_generators: List[IReportGenerator]

    def analyze(self) -> AnalysisResults:
        """执行分析"""
        log.debug("开始执行投票分析")
        
        votes = self.vote_repo.get_all_votes()
        schools = self.school_repo.get_all_schools()
        awards = self.award_repo.get_all_awards()
        
        log.debug(f"获取到总投票数：{len(votes)}，学校数：{len(schools)}，奖项数：{len(awards)}")

        # 初始化结果矩阵
        matrix_size = self._get_matrix_size(awards)
        log.debug(f"初始化结果矩阵，大小：{matrix_size}")
        
        total_sum = np.zeros(matrix_size)
        total_nonzero_count = np.zeros(matrix_size)
        school_sum = {school.name: np.zeros(matrix_size) for school in schools}
        school_nonzero_count = {school.name: np.zeros(matrix_size) for school in schools}

        # 计算总和和非零计数
        log.debug("开始计算总和和非零计数")
        for vote in votes:
            total_sum += vote.matrix
            total_nonzero_count += np.where(vote.matrix != 0, 1, 0)
            school_sum[vote.school.name] += vote.matrix
            school_nonzero_count[vote.school.name] += np.where(vote.matrix != 0, 1, 0)

        # 计算平均值
        log.debug("开始计算总体平均值")
        total_avg = total_sum / len(votes)
        total_nonzero_avg = np.divide(
            total_sum,
            total_nonzero_count,
            out=np.zeros_like(total_sum),
            where=total_nonzero_count > 0
        )

        # 计算学校平均值
        log.debug("开始计算各学校平均值")
        school_avg = {}
        school_nonzero_avg = {}
        for school in schools:
            vote_count = self.vote_repo.get_vote_count_by_school(school)
            if vote_count > 0:
                log.debug(f"计算学校 {school.name} 的平均值，投票数：{vote_count}")
                school_avg[school.name] = school_sum[school.name] / vote_count
                school_nonzero_avg[school.name] = np.divide(
                    school_sum[school.name],
                    school_nonzero_count[school.name],
                    out=np.zeros_like(school_sum[school.name]),
                    where=school_nonzero_count[school.name] > 0
                )

        # 计算学校总平均值
        log.debug("开始计算所有学校的总平均值")
        school_avg_matrices = np.stack(list(school_avg.values()))
        school_nonzero_avg_matrices = np.stack(list(school_nonzero_avg.values()))
        total_school_avg = np.mean(school_avg_matrices, axis=0)
        total_school_nonzero_avg = np.mean(school_nonzero_avg_matrices, axis=0)

        log.debug("分析完成，返回结果")
        return AnalysisResults(
            total_avg=total_avg,
            total_nonzero_avg=total_nonzero_avg,
            school_avg=school_avg,
            school_nonzero_avg=school_nonzero_avg,
            total_school_avg=total_school_avg,
            total_school_nonzero_avg=total_school_nonzero_avg
        )

    def generate_report(self, results: AnalysisResults) -> None:
        """生成分析报告"""
        log.debug("开始生成分析报告")
        
        # 准备报告数据
        schools = [
            school for school in self.school_repo.get_all_schools()
            if school.name in results.school_avg
        ]
        awards = self.award_repo.get_all_awards()
        
        log.debug(f"报告数据准备：有效学校数量={len(schools)}，奖项数量={len(awards)}")

        report_data = {
            "stats": {
                "total_school_count": len(schools),
                "total_vote_count": len(self.vote_repo.get_all_votes()),
            },
            "schools": [
                {
                    "name": school.name,
                    "location": school.location,
                    "vote_count": self.vote_repo.get_vote_count_by_school(school)
                }
                for school in schools
            ],
            "awards": [
                {
                    "name": award.name,
                    "works": [
                        {
                            "title": work.title,
                            "total_avg": {
                                "avg": float(results.total_avg[i][work.award_indexes[award.name]]),
                                "nonzero_avg": float(results.total_nonzero_avg[i][work.award_indexes[award.name]])
                            },
                            "total_school_avg": {
                                "avg": float(results.total_school_avg[i][work.award_indexes[award.name]]),
                                "nonzero_avg": float(results.total_school_nonzero_avg[i][work.award_indexes[award.name]])
                            },
                            "school_avg": [
                                {
                                    "school_name": school.name,
                                    "avg": float(results.school_avg[school.name][i][work.award_indexes[award.name]]),
                                    "nonzero_avg": float(results.school_nonzero_avg[school.name][i][work.award_indexes[award.name]])
                                }
                                for school in schools
                                if school.name in results.school_avg
                            ]
                        }
                        for work in self.work_repo.get_works_by_award(award)
                    ]
                }
                for i, award in enumerate(awards)
            ]
        }

        # 使用所有报告生成器生成报告
        for generator in self.report_generators:
            log.debug(f"使用报告生成器 {generator.__class__.__name__} 生成报告")
            generator.generate_report(report_data)
        
        log.debug("报告生成完成")

    def _get_matrix_size(self, awards: List[Award]) -> tuple[int, int]:
        """获取投票矩阵大小"""
        max_works = max(len(award.works) for award in awards)
        size = (len(awards), max_works)
        log.debug(f"计算投票矩阵大小：{size}")
        return size 

@dataclass
class VoteImportService:
    """投票导入服务"""
    vote_repo: IVoteRepository
    voting_service: 'VotingService'

    def import_votes_from_loader(self, loader: IVoteDataLoader) -> None:
        """从加载器导入投票数据"""
        log.debug("开始从加载器导入投票数据")
        for vote in loader.load_votes():
            self.voting_service.add_vote(vote)
        log.debug("投票数据导入完成") 