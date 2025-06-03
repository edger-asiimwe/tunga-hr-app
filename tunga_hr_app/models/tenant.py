from datetime import datetime, timezone

from sqlalchemy import (
    Integer, 
    String, 
    DateTime
)

from sqlalchemy.orm import ( 
    Mapped, 
    mapped_column
)

from tunga_hr_app import db

class LeaveRequest(db.Model):

    leave_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=True)
    end_date: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=True)
    leave_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='Pending', nullable=False) # Pending, Approved, Rejected, In Progress, Complete
    approved_by: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True, 
                                                 default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, index=True, 
                                                 default=lambda: datetime.now(timezone.utc), 
                                                 onupdate=lambda: datetime.now(timezone.utc))


    def __repr__(self):
        return f'<Leave Request: {self.leave_id} - {self.employee_id} - {self.leave_type} - {self.status}>'
    

class Attendance(db.Model):

    attendance_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(Integer, nullable=False)
    clock_in: Mapped[datetime] = mapped_column(DateTime, index=True, 
                                                 default=lambda: datetime.now(timezone.utc))
    clock_out: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True, 
                                                 default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, index=True, 
                                                 default=lambda: datetime.now(timezone.utc), 
                                                 onupdate=lambda: datetime.now(timezone.utc))
    

    def __repr__(self):
        return f'<Attendance: {self.attendance_id} - {self.employee_id} - {self.clock_in}>'
