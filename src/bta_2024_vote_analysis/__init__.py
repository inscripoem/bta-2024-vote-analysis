"""BTA 2024投票分析主程序"""
import json
import logging

from .core.models import School, Award, Work
from .core.services import VotingService, AnalysisService, VoteImportService
from .adapters.input.excel import ExcelVoteLoader
from .adapters.output.markdown import MarkdownReporter
from .adapters.output.json import JsonReporter
from .infrastructure.persistence import (
    InMemoryVoteRepository,
    InMemorySchoolRepository,
    InMemoryAwardRepository,
    InMemoryWorkRepository
)
from .infrastructure.logging import setup_logging

def main() -> int:
    """主程序入口"""
    # 设置日志
    log_file = "logs/bta_2024_vote_analysis.log"

    log = setup_logging(
        console_level=logging.INFO,
        file_level=logging.DEBUG,
        log_file=log_file
    )

    log.info("日志文件将保存在{}".format(log_file))

    try:
        # 初始化仓库
        vote_repo = InMemoryVoteRepository()
        school_repo = InMemorySchoolRepository()
        award_repo = InMemoryAwardRepository()
        work_repo = InMemoryWorkRepository()

        # 加载学校数据
        with open(".data/schools.json", encoding="utf-8") as f:
            school_locations = json.load(f)
            for school_data in school_locations:
                school_repo.add_school(School(**school_data))

        # 加载奖项和作品数据
        with open(".data/awards.json", encoding="utf-8") as f:
            awards_data = json.load(f)
            for award_data in awards_data:
                award_repo.add_award(Award(**award_data))
                for i, work_title in enumerate(award_data["works"]):
                    work_repo.add_work(Work(
                        title=work_title,
                        award_indexes={award_data["name"]: i}
                    ))

        # 初始化服务
        voting_service = VotingService(
            vote_repo=vote_repo,
            school_repo=school_repo,
            award_repo=award_repo,
            work_repo=work_repo
        )

        # 初始化导入服务
        vote_import_service = VoteImportService(
            vote_repo=vote_repo,
            voting_service=voting_service
        )

        # 加载投票数据
        vote_loader = ExcelVoteLoader(
            file_path=".data/answer_all.xlsx",
            school_repo=school_repo
        )
        
        # 导入投票数据
        vote_import_service.import_votes_from_loader(vote_loader)

        # 分析数据
        analysis_service = AnalysisService(
            vote_repo=vote_repo,
            school_repo=school_repo,
            award_repo=award_repo,
            work_repo=work_repo,
            report_generators=[
                MarkdownReporter(output_path="reports_refactor/vote_analysis_report.md"),
                JsonReporter(output_path="reports_refactor/vote_analysis_report.json")
            ]
        )
        results = analysis_service.analyze()

        # 生成报告
        analysis_service.generate_report(results)

        # 转换MessagePack为JSON
        JsonReporter.msgpack_to_json(
            "reports_refactor/vote_analysis_report.msgpack",
            "reports_refactor/vote_analysis_report_rev.json"
        )

        return 0
        
    except Exception as e:
        log.exception("程序执行出错：%s", e)
        return 1
