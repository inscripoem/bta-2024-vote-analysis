"""Markdown报告生成适配器"""
import logging
from pathlib import Path
from typing import Dict, Any, List

from ...core.ports import IReportGenerator

log = logging.getLogger(__name__)

class MarkdownReporter(IReportGenerator):
    """Markdown报告生成器"""

    def __init__(self, output_path: str | Path):
        self.output_path = Path(output_path)

    def generate_report(self, data: Dict[str, Any]) -> None:
        """生成Markdown格式的报告"""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.output_path, "w", encoding="utf-8") as f:
            self._write_header(f)
            self._write_total_ranking_per_person(f, data)
            self._write_total_ranking_per_school(f, data)
            self._write_school_details(f, data)
        
        log.info(f"分析报告已保存至 {self.output_path}")

    def _write_header(self, f) -> None:
        """写入报告头部"""
        f.write("# BTA 2024 投票分析报告\n\n")

    def _write_total_ranking_per_person(self, f, data: Dict[str, Any]) -> None:
        """写入人均排名部分"""
        f.write("## 总体排名（人均）\n\n")
        for award in data["awards"]:
            f.write(f"### {award['name']}\n\n")
            works = award["works"]
            
            # 按普通均分和非零均分排序
            avg_sorted = sorted(works, key=lambda x: -x["total_avg"]["avg"])
            nonzero_sorted = sorted(works, key=lambda x: -x["total_avg"]["nonzero_avg"])
            
            self._write_ranking_table(f, avg_sorted, nonzero_sorted, "total_avg")

    def _write_total_ranking_per_school(self, f, data: Dict[str, Any]) -> None:
        """写入校均排名部分"""
        f.write("## 总体排名（校均）\n\n")
        for award in data["awards"]:
            f.write(f"### {award['name']}\n\n")
            works = award["works"]
            
            # 按学校均分和非零均分排序
            avg_sorted = sorted(works, key=lambda x: -x["total_school_avg"]["avg"])
            nonzero_sorted = sorted(works, key=lambda x: -x["total_school_avg"]["nonzero_avg"])
            
            self._write_ranking_table(f, avg_sorted, nonzero_sorted, "total_school_avg")

    def _write_school_details(self, f, data: Dict[str, Any]) -> None:
        """写入各校详细统计部分"""
        f.write("## 各校详细统计\n\n")
        for school in data["schools"]:
            f.write(f"### {school['name']}\n\n")
            
            for award in data["awards"]:
                works_with_school_votes = [
                    work for work in award["works"]
                    if any(sa["school_name"] == school["name"] for sa in work["school_avg"])
                ]
                
                if not works_with_school_votes:
                    continue
                    
                f.write(f"#### {award['name']}\n\n")
                
                # 获取该学校的评分
                works_with_scores = []
                for work in works_with_school_votes:
                    school_avg = next(
                        sa for sa in work["school_avg"]
                        if sa["school_name"] == school["name"]
                    )
                    works_with_scores.append({
                        "title": work["title"],
                        "total_avg": {"avg": school_avg["avg"], "nonzero_avg": school_avg["nonzero_avg"]}
                    })
                
                # 按普通均分和非零均分排序
                avg_sorted = sorted(works_with_scores, key=lambda x: -x["total_avg"]["avg"])
                nonzero_sorted = sorted(works_with_scores, key=lambda x: -x["total_avg"]["nonzero_avg"])
                
                self._write_ranking_table(f, avg_sorted, nonzero_sorted, "total_avg")

    def _write_ranking_table(self, f, avg_sorted: List[Dict[str, Any]], 
                           nonzero_sorted: List[Dict[str, Any]], avg_key: str) -> None:
        """写入排名表格"""
        f.write("| 排名 | 作品 (普通均分) | 分数 | 作品 (非零均分) | 分数 |\n")
        f.write("|------|----------------|------|----------------|------|\n")
        
        max_len = max(len(avg_sorted), len(nonzero_sorted))
        for i in range(max_len):
            avg_title = avg_sorted[i]["title"] if i < len(avg_sorted) else ""
            avg_score = f"{avg_sorted[i][avg_key]['avg']:.4f}" if i < len(avg_sorted) else ""
            nonzero_title = nonzero_sorted[i]["title"] if i < len(nonzero_sorted) else ""
            nonzero_score = f"{nonzero_sorted[i][avg_key]['nonzero_avg']:.4f}" if i < len(nonzero_sorted) else ""
            f.write(f"| {i+1} | {avg_title} | {avg_score} | {nonzero_title} | {nonzero_score} |\n")
        f.write("\n") 