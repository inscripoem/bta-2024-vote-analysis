import logging
import json
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import msgpack

from .analyzers import VoteAnalyzer
from .models import Work

log = logging.getLogger(__name__)

class BaseReporter(ABC):
    """报告生成器基类"""
    
    def __init__(self, analyzer: VoteAnalyzer, output_path: Optional[str | Path] = None):
        self.analyzer = analyzer
        self.vote_manager = analyzer.vote_manager
        self.output_path = Path(output_path) if output_path else None
    
    def _ensure_output_directory(self) -> None:
        """确保输出目录存在"""
        if self.output_path:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def generate_report(self) -> None:
        """生成报告的抽象方法"""
        pass
    
    def _get_sorted_works_by_award(self, award_idx: int) -> List[Tuple[Work, float, float]]:
        """获取某个奖项下按分数排序的作品列表"""
        works = self.vote_manager.award_manager.works_by_award[
            self.vote_manager.award_manager.awards_by_index[award_idx].name
        ]
        work_scores = []
        for work_idx, work in enumerate(works):
            avg = self.analyzer.total_avg[award_idx][work_idx]
            nonzero_avg = self.analyzer.total_nonzero_avg[award_idx][work_idx]
            if avg != 0:
                work_scores.append((work, avg, nonzero_avg))
        return work_scores

class MarkdownReporter(BaseReporter):
    """Markdown格式报告生成器"""
    
    def generate_report(self) -> None:
        """生成Markdown格式的报告"""
        output_path = self.output_path or Path("vote_analysis_report.md")
        self._ensure_output_directory()
        with open(output_path, "w", encoding="utf-8") as f:
            self._write_header(f)
            self._write_total_ranking_per_person(f)
            self._write_total_ranking_per_school(f)
            self._write_school_details(f)
        
        log.info(f"Analysis report has been saved to {output_path}")
    
    def _write_header(self, f) -> None:
        """写入报告头部"""
        f.write("# BTA 2024 投票分析报告\n\n")
    
    def _write_total_ranking_per_person(self, f) -> None:
        """写入人均排名部分"""
        f.write("## 总体排名（人均）\n\n")
        for award_idx, award in self.vote_manager.award_manager.awards_by_index.items():
            f.write(f"### {award.name}\n\n")
            work_scores = self._get_sorted_works_by_award(award_idx)
            
            avg_sorted = sorted(work_scores, key=lambda x: -x[1])
            nonzero_sorted = sorted(work_scores, key=lambda x: -x[2])
            
            self._write_ranking_table(f, avg_sorted, nonzero_sorted)
    
    def _write_total_ranking_per_school(self, f) -> None:
        """写入校均排名部分"""
        f.write("## 总体排名（校均）\n\n")
        for award_idx, award in self.vote_manager.award_manager.awards_by_index.items():
            f.write(f"### {award.name}\n\n")
            works = self.vote_manager.award_manager.works_by_award[award.name]
            
            work_scores = []
            for work_idx, work in enumerate(works):
                avg = self.analyzer.total_school_avg[award_idx][work_idx]
                nonzero_avg = self.analyzer.total_school_nonzero_avg[award_idx][work_idx]
                if avg != 0:
                    work_scores.append((work, avg, nonzero_avg))
            
            avg_sorted = sorted(work_scores, key=lambda x: -x[1])
            nonzero_sorted = sorted(work_scores, key=lambda x: -x[2])
            
            self._write_ranking_table(f, avg_sorted, nonzero_sorted)
    
    def _write_school_details(self, f) -> None:
        """写入各校详细统计部分"""
        f.write("## 各校详细统计\n\n")
        for school_name in self.analyzer.school_manager.schools.keys():
            f.write(f"### {school_name}\n\n")
            
            for award_idx, award in self.vote_manager.award_manager.awards_by_index.items():
                if not any(self.analyzer.school_avg[school_name][award_idx] != 0):
                    continue
                    
                f.write(f"#### {award.name}\n\n")
                works = self.vote_manager.award_manager.works_by_award[award.name]
                work_scores = []
                
                for work_idx, work in enumerate(works):
                    avg = self.analyzer.school_avg[school_name][award_idx][work_idx]
                    nonzero_avg = self.analyzer.school_nonzero_avg[school_name][award_idx][work_idx]
                    if avg != 0:
                        work_scores.append((work, avg, nonzero_avg))
                
                avg_sorted = sorted(work_scores, key=lambda x: -x[1])
                nonzero_sorted = sorted(work_scores, key=lambda x: -x[2])
                
                self._write_ranking_table(f, avg_sorted, nonzero_sorted)
    
    def _write_ranking_table(self, f, avg_sorted: List[Tuple[Work, float, float]], 
                           nonzero_sorted: List[Tuple[Work, float, float]]) -> None:
        """写入排名表格"""
        f.write("| 排名 | 作品 (普通均分) | 分数 | 作品 (非零均分) | 分数 |\n")
        f.write("|------|----------------|------|----------------|------|\n")
        
        max_len = max(len(avg_sorted), len(nonzero_sorted))
        for i in range(max_len):
            avg_title = avg_sorted[i][0].title if i < len(avg_sorted) else ""
            avg_score = f"{avg_sorted[i][1]:.4f}" if i < len(avg_sorted) else ""
            nonzero_title = nonzero_sorted[i][0].title if i < len(nonzero_sorted) else ""
            nonzero_score = f"{nonzero_sorted[i][2]:.4f}" if i < len(nonzero_sorted) else ""
            f.write(f"| {i+1} | {avg_title} | {avg_score} | {nonzero_title} | {nonzero_score} |\n")
        f.write("\n")

class DataFormatReporter(BaseReporter):
    """数据格式报告生成器（JSON和MessagePack）"""
    
    def generate_report(self) -> None:
        """生成JSON和MessagePack格式的报告"""
        data = self._generate_data_structure()
        
        # 生成JSON文件
        json_path = self.output_path or Path("vote_analysis_report.json")
        self._ensure_output_directory()
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log.info(f"JSON report has been saved to {json_path}")
        
        # 生成MessagePack文件
        msgpack_path = json_path.with_suffix(".msgpack")
        # 对数据进行优化，减小体积
        optimized_data = self._optimize_for_msgpack(data)
        
        # 计算原始JSON和优化后的MessagePack大小
        json_size = len(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        msgpack_size = len(msgpack.packb(
            optimized_data,
            use_bin_type=False,
            strict_types=False,
            use_single_float=True
        ))
        
        # 写入MessagePack文件
        with open(msgpack_path, "wb") as f:
            msgpack.pack(
                optimized_data,
                f,
                use_bin_type=False,  # 减少字符串开销
                strict_types=False,   # 允许更灵活的类型转换
                use_single_float=True # 使用单精度浮点数
            )
        
        log.info(
            f"MessagePack report has been saved to {msgpack_path} "
            f"(size reduced from {json_size:,} to {msgpack_size:,} bytes, "
            f"saved {(1 - msgpack_size/json_size)*100:.1f}%)"
        )
    
    @staticmethod
    def msgpack_to_json(msgpack_path: str | Path, json_path: Optional[str | Path] = None) -> None:
        """将MessagePack文件转换为JSON文件
        
        Args:
            msgpack_path: MessagePack文件路径
            json_path: 输出的JSON文件路径，如果不指定则使用同名的.json文件
        
        Raises:
            FileNotFoundError: 如果MessagePack文件不存在
        """
        msgpack_path = Path(msgpack_path)
        if not msgpack_path.exists():
            raise FileNotFoundError(f"MessagePack file not found: {msgpack_path}")
        
        # 如果未指定json_path，则使用同名的.json文件
        if json_path is None:
            json_path = msgpack_path.with_suffix(".json")
        else:
            json_path = Path(json_path)
        
        # 读取MessagePack文件
        with open(msgpack_path, "rb") as f:
            data = msgpack.unpack(f)
        
        # 确保输出目录存在
        json_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入JSON文件
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log.info(f"Converted MessagePack file to JSON: {json_path}")
    
    def _optimize_for_msgpack(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """优化数据以减小MessagePack文件大小"""
        def _round_float(value: float) -> float:
            """将浮点数四舍五入到4位小数"""
            return round(value, 4)
        
        def _process_value(value: Any) -> Any:
            """处理各种类型的值"""
            if isinstance(value, dict):
                return {k: _process_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_process_value(v) for v in value]
            elif isinstance(value, float):
                return _round_float(value)
            return value
        
        # 深拷贝并优化数据
        optimized = _process_value(data)
        return optimized
    
    def _generate_data_structure(self) -> Dict[str, Any]:
        """生成数据结构"""
        vm = self.vote_manager
        
        # 统计数据
        stats = {
            "total_school_count": len(vm.school_manager),
            "total_vote_count": len(vm),
            "total_view_count": None,
            "total_view_user_count": None
        }
        
        # 学校数据
        schools = []
        for i, school in enumerate(vm.school_manager.schools.values(), 1):
            schools.append({
                "id": f"school_{i}",
                "name": school.name,
                "vote_count": vm.get_vote_count_by_school(school),
                "location": school.location
            })
        
        # 奖项数据
        awards = []
        for award_idx, award in vm.award_manager.awards_by_index.items():
            works_data = []
            works = vm.award_manager.works_by_award[award.name]
            
            for work_idx, work in enumerate(works):
                # 收集每个学校对这个作品的评分
                school_avg_data = []
                for school_idx, school in enumerate(vm.school_manager.schools.values(), 1):
                    if self.analyzer.school_avg[school.name][award_idx][work_idx] != 0:
                        school_avg_data.append({
                            "school_id": f"school_{school_idx}",
                            "avg": float(self.analyzer.school_avg[school.name][award_idx][work_idx]),
                            "nonzero_avg": float(self.analyzer.school_nonzero_avg[school.name][award_idx][work_idx])
                        })
                
                works_data.append({
                    "id": f"work_{award_idx+1}_{work_idx+1}",
                    "name": work.title,
                    "vote_count": int(self.analyzer.total_nonzero_count[award_idx][work_idx]),
                    "nonzero_vote_count": int(self.analyzer.total_nonzero_count[award_idx][work_idx]),
                    "total_avg": {
                        "avg": float(self.analyzer.total_avg[award_idx][work_idx]),
                        "nonzero_avg": float(self.analyzer.total_nonzero_avg[award_idx][work_idx])
                    },
                    "total_school_avg": {
                        "avg": float(self.analyzer.total_school_avg[award_idx][work_idx]),
                        "nonzero_avg": float(self.analyzer.total_school_nonzero_avg[award_idx][work_idx])
                    },
                    "school_avg": school_avg_data
                })
            
            awards.append({
                "id": f"award_{award_idx+1}",
                "name": award.name,
                "works": works_data
            })
        
        return {
            "stats": stats,
            "schools": schools,
            "awards": awards
        } 