import ast
import logging
from typing import Iterator

import numpy as np
from pandas import DataFrame, read_excel, read_csv, isna
from pypinyin import lazy_pinyin

from .models import Metadata, Vote
from .managers import SchoolManager


log = logging.getLogger(__name__)

def read_from_file(file_path: str) -> DataFrame:
    if file_path.endswith(".xlsx"):
        return read_excel(file_path)
    elif file_path.endswith(".csv"):
        return read_csv(file_path)
    else:
        raise ValueError("Unsupported file type: {}".format(file_path))

class AllDataAdapter():

    def __init__(self, file_path: str, school_manager: SchoolManager | None = None):
        self.file_path = file_path
        self._school_manager = school_manager

        try:
            log.info("Reading file...", extra={"highlighter": None})
            self.data = read_from_file(self.file_path)
            log.info("File read successfully with {} rows".format(len(self.data)))


        except Exception as e:
            raise ValueError("Failed to read file: {}".format(e))
    
    @property
    def school_manager(self) -> SchoolManager:
        if self._school_manager is None:
            log.info("- No SchoolManager found, creating one from existing data...", extra={"highlighter": None})
            schools = set(self.data["用户所在学校"])
            self._school_manager = SchoolManager.from_iterable(sorted(schools, key=lambda x: lazy_pinyin(x)))
        return self._school_manager



    def status(self) -> None:
        log.info("Data status:")
        log.info("Schools: {}".format(self.school_manager.schools.keys()))
        log.info("Data example:")
        log.info(self.data.head())
        log.info("...with {} rows".format(len(self.data)))



    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self) -> Iterator[Vote]:
        for _, row in self.data.iterrows():
            metadata = Metadata(
                submission_time=row["提交时间"],
                submission_ip=row["提交 IP"],
                username=row["用户名"],
                email=str(row["用户邮箱"]) if not isna(row["用户邮箱"]) else None,
                student_id=str(row["用户学号"]) if not isna(row["用户学号"]) else None,
                is_student=row["是否为在校生"],
            )

            school = self.school_manager.get_school_by_name(row["用户所在学校"])

            matrix = np.array([ast.literal_eval(row.iloc[i]) for i in range(11)])

            yield Vote(metadata=metadata, school=school, matrix=matrix)
        
