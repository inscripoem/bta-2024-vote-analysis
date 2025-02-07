"""日志配置实现"""
import logging
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler

def setup_logging(
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    log_file: str | Path = "bta_2024_vote_analysis.log"
) -> logging.Logger:
    """设置日志配置
    
    Args:
        console_level: 控制台日志级别，默认为INFO
        file_level: 文件日志级别，默认为DEBUG
        log_file: 日志文件路径，默认为"bta_2024_vote_analysis.log"
        
    Returns:
        配置好的Logger实例
    """
    # 创建Logger
    logger = logging.getLogger("bta_2024_vote_analysis")
    logger.setLevel(min(console_level, file_level))  # 使用最低的级别作为logger的级别

    # 清除现有的处理器
    logger.handlers.clear()

    # 创建控制台处理器
    console = Console()
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True
    )
    console_handler.setLevel(console_level)
    logger.addHandler(console_handler)

    # 创建文件处理器
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)  # 确保日志目录存在
    
    file_handler = logging.FileHandler(
        log_path,
        encoding="utf-8",
        mode="w"
    )
    file_handler.setLevel(file_level)
    logger.addHandler(file_handler)

    # 设置格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)

    return logger 