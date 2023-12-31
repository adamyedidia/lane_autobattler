from sqlalchemy import Column, DateTime, Index, Integer, String, func
from sqlalchemy.orm import relationship
from database import Base


class DraftPick(Base):
    __tablename__ = "draft_picks"

    id = Column(Integer, primary_key=True)

    username = Column(String, nullable=False)

    unique_draft_identifier = Column(String)

    selected_draft_choice_id = Column(Integer, index=True)
    selected_draft_choice = relationship("DraftChoice")

    pick_num = Column(Integer, nullable=False)

    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    __table_args__ = (
        Index("draft_picks_idx_username_created_at", username, created_at),
        Index("draft_picks_username_unique_draft_identifier_pick_num", username, unique_draft_identifier, pick_num),
    )

    def __repr__(self):
        return f"<DraftPick {self.id}>"