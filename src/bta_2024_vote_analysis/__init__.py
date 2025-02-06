import json
import logging

from .managers import AwardManager, VoteManager
from .adapters import AllDataAdapter
from .utils import get_logger
from .analyzers import VoteAnalyzer
from .reporters import MarkdownReporter, DataFormatReporter
from rich.progress import track

def main() -> int:
    # 设置日志
    log = get_logger("bta_2024_vote_analysis")
    log.setLevel(logging.INFO)

    file_handler = logging.FileHandler("bta_2024_vote_analysis.log", encoding="utf-8", mode="w")
    file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)

    # 加载数据
    all_data = AllDataAdapter(file_path=".data/answer_all.xlsx")
    all_data.status()
    school_manager = all_data.school_manager
    school_manager.update_school_locations_from_json(json.load(open(".data/schools.json", encoding="utf-8")))

    # 初始化管理器
    awards_manager = AwardManager.from_json(json.load(open(".data/awards.json", encoding="utf-8")))
    vote_manager = VoteManager(school_manager=school_manager, award_manager=awards_manager)

    # 添加投票数据
    if log.getEffectiveLevel() == logging.DEBUG:
        for vote in all_data:
            vote_manager.add_vote(vote)
    else:
        for vote in track(all_data, description="Adding votes..."):
            vote_manager.add_vote(vote)
    vote_manager.status()

    # 分析数据
    analyzer = VoteAnalyzer(vote_manager=vote_manager)
    analyzer.analyze()

    # 生成报告
    markdown_reporter = MarkdownReporter(analyzer=analyzer, output_path="reports/vote_analysis_report.md")
    markdown_reporter.generate_report()

    data_reporter = DataFormatReporter(analyzer=analyzer, output_path="reports/vote_analysis_report.json")
    data_reporter.generate_report()

    DataFormatReporter.msgpack_to_json("reports/vote_analysis_report.msgpack", "reports/vote_analysis_report_rev.json")
    
    return 0
