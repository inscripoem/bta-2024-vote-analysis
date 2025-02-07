"""JSON报告生成适配器"""
import json
import logging
import msgpack
from pathlib import Path
from typing import Dict, Any

from ...core.ports import IReportGenerator

log = logging.getLogger(__name__)

class JsonReporter(IReportGenerator):
    """JSON报告生成器"""

    def __init__(self, output_path: str | Path):
        self.output_path = Path(output_path)

    def generate_report(self, data: Dict[str, Any]) -> None:
        """生成JSON格式的报告"""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 生成JSON文件
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log.info(f"JSON报告已保存至 {self.output_path}")
        
        # 生成MessagePack文件
        msgpack_path = self.output_path.with_suffix(".msgpack")
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
                use_bin_type=False,
                strict_types=False,
                use_single_float=True
            )
        
        log.info(
            f"MessagePack报告已保存至 {msgpack_path} "
            f"(大小从 {json_size:,} 减少到 {msgpack_size:,} 字节, "
            f"节省 {(1 - msgpack_size/json_size)*100:.1f}%)"
        )

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
        
        return _process_value(data)

    @staticmethod
    def msgpack_to_json(msgpack_path: str | Path, json_path: str | Path | None = None) -> None:
        """将MessagePack文件转换为JSON文件
        
        Args:
            msgpack_path: MessagePack文件路径
            json_path: 输出的JSON文件路径，如果不指定则使用同名的.json文件
        
        Raises:
            FileNotFoundError: 如果MessagePack文件不存在
        """
        msgpack_path = Path(msgpack_path)
        if not msgpack_path.exists():
            raise FileNotFoundError(f"MessagePack文件未找到: {msgpack_path}")
        
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
        log.info(f"已将MessagePack文件转换为JSON: {json_path}") 