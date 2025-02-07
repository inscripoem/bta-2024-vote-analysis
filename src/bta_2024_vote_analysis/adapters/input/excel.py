"""Excel数据加载适配器"""
import ast
import logging
from typing import List
import numpy as np
from pandas import DataFrame, read_excel, read_csv, isna

from ...core.models import Vote, VoteMetadata
from ...core.ports import IVoteDataLoader, ISchoolRepository

log = logging.getLogger(__name__)

def read_from_file(file_path: str) -> DataFrame:
    """从文件读取数据"""
    log.debug(f"正在读取文件：{file_path}")
    try:
        if file_path.endswith(".xlsx"):
            log.debug("检测到Excel文件格式")
            df = read_excel(file_path)
        elif file_path.endswith(".csv"):
            log.debug("检测到CSV文件格式")
            df = read_csv(file_path)
        else:
            raise ValueError("不支持的文件类型: {}".format(file_path))
        
        log.debug(f"文件读取成功，数据形状：{df.shape}，列名：{list(df.columns)}")
        return df
    except Exception as e:
        log.error(f"文件读取失败：{str(e)}")
        raise

class ExcelVoteLoader(IVoteDataLoader):
    """Excel投票数据加载器"""

    def __init__(self, file_path: str, school_repo: ISchoolRepository):
        log.debug(f"初始化Excel投票数据加载器，文件路径：{file_path}")
        self.file_path = file_path
        self.school_repo = school_repo

        try:
            log.info("正在读取文件...", extra={"highlighter": None})
            self.data = read_from_file(self.file_path)
            log.info("文件读取成功，共 {} 行".format(len(self.data)))
        except Exception as e:
            log.error(f"初始化失败：{str(e)}")
            raise ValueError("文件读取失败: {}".format(e))

    def load_votes(self) -> List[Vote]:
        """加载投票数据"""
        log.debug("开始加载投票数据")
        votes = []
        for idx, (_, row) in enumerate(self.data.iterrows(), 1):
            log.debug(f"正在处理第 {idx} 条投票数据")
            try:
                metadata = VoteMetadata(
                    submission_time=row["提交时间"],
                    submission_ip=row["提交 IP"],
                    username=row["用户名"],
                    email=str(row["用户邮箱"]) if not isna(row["用户邮箱"]) else None,
                    student_id=str(row["用户学号"]) if not isna(row["用户学号"]) else None,
                    is_student=row["是否为在校生"],
                )
                
                school_name = row["用户所在学校"]
                log.debug(f"正在获取学校信息：{school_name}")
                school = self.school_repo.get_school_by_name(school_name)
                
                log.debug("正在解析投票矩阵")
                matrix = np.array([ast.literal_eval(row.iloc[i]) for i in range(11)])
                
                votes.append(Vote(metadata=metadata, school=school, matrix=matrix))
                log.debug(f"第 {idx} 条投票数据处理完成")
            except Exception as e:
                log.error(f"处理第 {idx} 条投票数据时出错：{str(e)}")
                raise

        log.info(f"投票数据加载完成，共加载 {len(votes)} 条投票")
        return votes 