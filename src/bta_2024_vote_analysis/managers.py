import uuid
import logging
from typing import Iterable, Iterator

from .models import School, Award, Work, Vote

log = logging.getLogger(__name__)

class SchoolManager:
    def __init__(self) -> None:
        # 初始化schools字典
        self.schools: dict[str, School] = {}
    
    def add_school(self, school: School):
        if school.name in self.schools:
            raise ValueError("School already exists")
        self.schools[school.name] = school
        log.debug("School added: [cyan]{}[/]".format(school.name), extra={"markup": True})

    def get_school_by_name(self, name: str) -> School:
        return self.schools[name]

    def __len__(self) -> int:
        return len(self.schools)

    @staticmethod
    def from_iterable(iterable: Iterable[str]) -> "SchoolManager":
        manager = SchoolManager()
        for name in iterable:
            manager.add_school(School(name=name))    
        log.info("- SchoolManager created with {} schools".format(len(manager.schools)))
        return manager

    def update_school_locations_from_json(self, json: dict) -> None:
        for school in json:
            if school["name"] in self.schools:
                self.schools[school["name"]].location = school["location"]
                log.debug("School location updated: [cyan]{}[/], [yellow]{}[/]".format(school["name"], school["location"]), extra={"markup": True})

class AwardManager:
    def __init__(self) -> None:
        # 初始化所需的字典
        self.awards: dict[str, Award] = {}
        self.awards_by_index: dict[int, Award] = {}
        self.works: dict[str, Work] = {}
        self.works_by_award: dict[str, list[Work]] = {}

    def add_award(self, award: str, works: list[str]):
        if award in self.awards:
            raise ValueError("Award already exists")
        self.awards[award] = Award(name=award)
        next_index = len(self.awards_by_index)
        self.awards_by_index[next_index] = self.awards[award]
        
        for i, work in enumerate(works):
            if work in self.works:
                self.works[work].award_indexes[award] = i
            else:
                self.works[work] = Work(title=work, award_indexes={award: i})
            if award not in self.works_by_award:
                self.works_by_award[award] = []
            self.works_by_award[award].append(self.works[work])
            log.debug("Work [cyan]{}[/] added to award [yellow]{}[/]".format(work, award), extra={"markup": True})

    def get_award_by_name(self, name: str) -> Award:
        return self.awards[name]
    
    @staticmethod
    def from_json(json: dict) -> "AwardManager":
        manager = AwardManager()
        for award in json:
            manager.add_award(award["name"], award["works"])
        log.info("- AwardManager created with {} awards".format(len(manager.awards)))
        return manager

class VoteManager:
    def __init__(self, school_manager: SchoolManager, award_manager: AwardManager) -> None:
        # 初始化所需的属性
        self.school_manager = school_manager
        self.award_manager = award_manager
        self.votes: dict[uuid.UUID, Vote] = {}
        self.votes_count: int = 0
        self.school_votes: dict[str, list[uuid.UUID]] = {}
        self._vote_matrix_size: tuple[int, int] | None = None

    @property
    def vote_matrix_size(self) -> tuple[int, int]:
        if self._vote_matrix_size is None:
            max_works_count = max(len(self.award_manager.works_by_award[award.name]) for award in self.award_manager.awards.values())
            self._vote_matrix_size = (len(self.award_manager.awards), max_works_count)
        return self._vote_matrix_size
    
    def __len__(self) -> int:
        return len(self.votes)
    
    def __iter__(self) -> Iterator[Vote]:
        return iter(self.votes.values())


    def add_vote(self, vote: Vote):
        if vote.id in self.votes:

            raise ValueError("Vote already exists")
        if vote.matrix.shape != self.vote_matrix_size:
            raise ValueError("Vote matrix size is invalid, expected {} but got {}".format(self.vote_matrix_size, vote.matrix.shape))
        else:
            log.debug("Vote matrix size is valid, expected {} and got {}".format(self.vote_matrix_size, vote.matrix.shape))
        
        self.votes[vote.id] = vote
        self.votes_count += 1
        
        school_name = vote.school.name
        if school_name not in self.school_votes:
            self.school_votes[school_name] = []
        self.school_votes[school_name].append(vote.id)
        
        log.debug("Vote added: {}, current vote count for {}: {}, total votes: {}".format(
            vote.id, school_name, len(self.school_votes[school_name]), self.votes_count))

    def get_votes_by_school(self, school: School) -> list[Vote]:
        vote_ids = self.school_votes.get(school.name, [])
        return [self.votes[vote_id] for vote_id in vote_ids]
    
    def get_vote_count_by_school(self, school: School) -> int:
        return len(self.school_votes.get(school.name, []))
    
    def status(self) -> None:
        log.info("VoteManager status:")
        log.info("Votes count: {}".format(self.votes_count))
        log.info("Votes count by school:")
        for school in self.school_manager.schools.values():
            log.info("- {}: {}".format(school.name, self.get_vote_count_by_school(school))) 