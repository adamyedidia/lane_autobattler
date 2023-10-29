from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, func
from database import Base

from sqlalchemy.orm import relationship


class DraftChoice(Base):
    __tablename__ = "draft_choices"

    id = Column(Integer, primary_key=True)

    draft_pick_id = Column(Integer, ForeignKey("draft_picks.id"))
    draft_pick = relationship("DraftPick", backref="draft_choices")

    card = Column(String)

    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    picked = Column(Boolean, nullable=False, default=False, server_default='f')

    __table_args__ = (
        Index("draft_choices_idx_draft_pick_id_created_at", draft_pick_id, created_at),
        Index("draft_choices_idx_card_picked_created_at", card, picked, created_at),
        Index("draft_choices_idx_picked_created_at", picked, created_at),
    )
