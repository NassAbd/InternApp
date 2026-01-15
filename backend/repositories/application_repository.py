from sqlalchemy.orm import Session
from models import UserApplication, Job
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import hashlib

class ApplicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def generate_id(self, link: str) -> str:
        return hashlib.md5(link.encode('utf-8')).hexdigest()

    def get_application(self, app_id: str) -> Optional[UserApplication]:
        return self.db.query(UserApplication).filter(UserApplication.id == app_id).first()

    def get_all_applications(self) -> List[UserApplication]:
        return self.db.query(UserApplication).order_by(UserApplication.last_update.desc()).all()

    def add_application(self, job_db_obj: Job, status: str = "Interested") -> UserApplication:
        app_id = self.generate_id(job_db_obj.link)
        
        existing_app = self.get_application(app_id)
        if existing_app:
            return existing_app

        current_time = datetime.now()
        
        new_app = UserApplication(
            id=app_id,
            job_id=job_db_obj.id,
            status=status,
            date_added=current_time,
            last_update=current_time
        )
        self.db.add(new_app)
        self.db.commit()
        self.db.refresh(new_app)
        return new_app

    def update_application(self, app_id: str, updates: Dict[str, Any]) -> Optional[UserApplication]:
        app = self.get_application(app_id)
        if not app:
            return None
            
        if "status" in updates:
            app.status = updates["status"]
            
        if "notes" in updates:
            app.notes = updates["notes"]
            
        app.last_update = datetime.now()
        self.db.commit()
        self.db.refresh(app)
        return app

    def delete_application(self, app_id: str) -> bool:
        app = self.get_application(app_id)
        if not app:
            return False
        
        self.db.delete(app)
        self.db.commit()
        return True
    
    def is_job_tracked(self, link: str) -> bool:
         app_id = self.generate_id(link)
         return self.get_application(app_id) is not None
