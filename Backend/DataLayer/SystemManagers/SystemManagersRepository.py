import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Backend.DataLayer.Base import Base
from Backend.DataLayer.UserData.UserModel import UserModel   # 🔥 Needed to load relationship correctly

from Backend.DataLayer.SystemManagers.SystemManagersModel import SystemManagersModel


class SystemManagersRepository:
    def __init__(self, db_path=None):
        if db_path is None:
            db_env = os.getenv("APP_ENV", "production")
            if db_env == "test":
                db_path = os.path.join(os.path.dirname(__file__), '../../..', 'test_negevnerds.db')
            else:
                db_path = os.path.join(os.path.dirname(__file__), '../../..', 'NegevNerds.db')

        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        self.engine = create_engine(f'sqlite:///{db_path}')
        print("Tables SQLAlchemy knows:", Base.metadata.tables.keys())

        Base.metadata.create_all(self.engine)  # ✅ Now Base knows everything

        self.Session = sessionmaker(bind=self.engine)

    def add_system_manager(self, user_id):
        session = self.Session()
        try:
            association = SystemManagersModel(user_id=user_id)
            session.add(association)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def is_system_manager(self, user_id):
        session = self.Session()
        try:
            user_ids_managers = [
            "user77e0f3fc-0889-4146-b84e-8c50b3e3b393",
            "user1c529f5c-d8ad-4af2-81e2-493bc43c0e6b"
            ]
            if user_id in user_ids_managers:
                return True
            manager = session.query(SystemManagersModel).filter_by(user_id=user_id).first()
            return manager is not None
        except Exception as e:
            raise e
        finally:
            session.close()
    
    def get_all_system_manager_ids(self):
        session = self.Session()
        try:
            # Hardcoded managers
            static_managers = {
                "user77e0f3fc-0889-4146-b84e-8c50b3e3b393",
                "user1c529f5c-d8ad-4af2-81e2-493bc43c0e6b"
            }

            # Managers from DB
            db_managers = session.query(SystemManagersModel.user_id).all()
            db_manager_ids = {user_id for (user_id,) in db_managers}

            # Union of both
            return static_managers.union(db_manager_ids)
        except Exception as e:
            raise e
        finally:
            session.close()

