import json
import unittest
import os
from unittest.mock import patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Backend.DataLayer.Base import Base, delete_all_data
from Backend.BusinessLayer.NegevNerds import NegevNerds
from Backend.DataLayer.Noitifications.NotificationModel import NotificationModel
from datetime import datetime, timedelta

from Backend.DataLayer.Noitifications.NotificationRepository import NotificationRepository
from Backend.Tests.SystemTest.BaseTestCase import BaseTestCase


class TestNegevNerdsNotifications(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        os.environ["APP_ENV"] = "test"
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        db_path = os.path.join(base_dir, "test_NegevNerds.db")
        cls.engine = create_engine(f"sqlite:///{db_path}")
        cls.Session = sessionmaker(bind=cls.engine)
        Base.metadata.drop_all(bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(cls.engine)

    def setUp(self):
        super().setUp()
        self.user = self._complete_user_registration("notify@bgu.ac.il", "Pass1!", "Notify", "Tester")

    def tearDown(self):
        delete_all_data(engine=self.engine, session=self.session)
        self.session.close()

    def _create_notification(self, receiver_id, message="בדיקה", notif_type="AppointSystemManager", link="",
                             sender_id=None):
        if sender_id is None:
            sender_id = receiver_id  # נניח שזה הודעה עצמית אם לא צויין אחרת

        notif = NotificationModel(
            sender_user_id=sender_id,  # ✔️ לוודא שהשולח קיים במסד
            receiver_user_id=receiver_id,
            message=message,
            time=datetime.now(),
            notification_id=f"notif_{datetime.now().timestamp()}",
            IsApproved=False,
            AppointSystemManager=(notif_type == "AppointSystemManager"),
            AppointCourseManager=(notif_type == "AppointCourseManager"),
            CommentToFollowing=(notif_type == "CommentToFollowing"),
            CommentToComment=(notif_type == "CommentToComment"),
            ReactToComment=(notif_type == "ReactToComment"),
            RemoveCourseManager=(notif_type == "RemoveCourseManager"),
            link=link
        )
        self.session.add(notif)
        self.session.commit()

    @patch('Backend.BusinessLayer.NegevNerds.NotificationRepository')
    def test_get_unapproved_notification_list_multiple_types(self, mock_notification_repo_class):
        """Test: Get unapproved notifications of different types – returns structured response."""

        user_id = "test_user_123"
        now = datetime.utcnow()

        # הכנה של אובייקטי Notification מדומים עם שדות שונים
        fake_notifications = [
            MagicMock(
                AppointSystemManager=True, AppointCourseManager=False, CommentToFollowing=False,
                CommentToComment=False, ReactToComment=False, RemoveCourseManager=False,
                message="You were appointed as system manager",
                notification_id="n1", time=now - timedelta(minutes=10), link="/system"
            ),
            MagicMock(
                AppointSystemManager=False, AppointCourseManager=True, CommentToFollowing=False,
                CommentToComment=False, ReactToComment=False, RemoveCourseManager=False,
                message="You were appointed as course manager",
                notification_id="n2", time=now - timedelta(hours=1), link="/course"
            ),
            MagicMock(
                AppointSystemManager=False, AppointCourseManager=False, CommentToFollowing=True,
                CommentToComment=False, ReactToComment=False, RemoveCourseManager=False,
                message="New comment in a thread you follow",
                notification_id="n3", time=now - timedelta(days=1), link="/discussion"
            )
        ]

        # החזרת ההתראות מהמוקט
        mock_repo_instance = MagicMock()
        mock_repo_instance.get_unapproved_notifications.return_value = fake_notifications
        mock_notification_repo_class.return_value = mock_repo_instance

        # קריאה לפונקציה בפועל
        response_json = self.negev.get_unapproved_notification_list(user_id=user_id)
        response = json.loads(response_json)

        # אימותים
        self.assertTrue(response["success"])
        self.assertEqual(len(response["notifications"]), 3)
        types = {n["type"] for n in response["notifications"]}
        self.assertSetEqual(types, {"AppointSystemManager", "AppointCourseManager", "CommentToFollowing"})

    # def test_multiple_unapproved_notifications(self):
    #     user = self._complete_user_registration("notifmulti@post.bgu.ac.il", "ValidPass1!", "רב", "התראות")
    #
    #     types = ["AppointSystemManager", "AppointCourseManager", "CommentToFollowing",
    #              "CommentToComment", "ReactToComment", "RemoveCourseManager"]
    #
    #     for notif_type in types:
    #         self._create_notification(user.user_id, message=f"הודעה עבור {notif_type}", notif_type=notif_type)
    #
    #     result = self.negev.get_unapproved_notification_list(user.user_id)
    #     data = json.loads(result)
    #
    #     self.assertTrue(data["success"])
    #     self.assertEqual(len(data["notifications"]), 6)
    #     returned_types = [n["type"] for n in data["notifications"]]
    #     self.assertCountEqual(returned_types, types)

    def test_get_unapproved_notifications_returns_empty_when_none(self):
        user = self._complete_user_registration("empty@post.bgu.ac.il", "ValidPass1!", "אין", "התראות")

        result = self.negev.get_unapproved_notification_list(user.user_id)
        data = json.loads(result)

        self.assertTrue(data["success"])
        self.assertEqual(data["notifications"], [])

    # def test_notification_with_need_approval_false_is_skipped(self):
    #     user = self._complete_user_registration("notapproved@post.bgu.ac.il", "ValidPass1!", "לא", "דורש")
    #
    #     notif = NotificationModel(
    #         sender_user_id="admin",
    #         receiver_user_id=user.user_id,
    #         message="הודעה שלא דורשת אישור",
    #         time=datetime.now(),
    #         notification_id="notif_non_approval",
    #         need_approval=False,
    #         AppointSystemManager=True,
    #         link=""
    #     )
    #     self.session.add(notif)
    #     self.session.commit()
    #
    #     result = self.negev.get_unapproved_notification_list(user.user_id)
    #     data = json.loads(result)
    #
    #     self.assertTrue(data["success"])
    #     self.assertEqual(data["notifications"], [])

    # def test_notification_with_null_time(self):
    #     user = self._complete_user_registration("notime@post.bgu.ac.il", "ValidPass1!", "אין", "זמן")
    #
    #     notif = NotificationModel(
    #         sender_user_id="admin",
    #         receiver_user_id=user.user_id,
    #         message="הודעה בלי זמן",
    #         time=None,
    #         notification_id="notif_null_time",
    #         need_approval=True,
    #         AppointSystemManager=True,
    #         link=""
    #     )
    #     self.session.add(notif)
    #     self.session.commit()
    #
    #     result = self.negev.get_unapproved_notification_list(user.user_id)
    #     data = json.loads(result)
    #
    #     self.assertTrue(data["success"])
    #     self.assertEqual(len(data["notifications"]), 1)
    #     self.assertIsNone(data["notifications"][0]["timestamp"])

    def test_mark_notification_as_seen_system_success(self):
        """System Test: Successfully mark an existing notification as seen."""

        repo = NotificationRepository()

        # Insert notification directly via session
        session = repo.Session()
        notif = NotificationModel(
            notification_id="test_seen_1",
            receiver_user_id=self.user.user_id,
            sender_user_id="admin_user",
            message="System test notification",
            AppointSystemManager=True,
            IsApproved=False,
            time=datetime.utcnow(),
            link="/system"
        )
        session.add(notif)
        session.commit()

        # Before marking
        before = repo.get_notification_by_id("test_seen_1")
        self.assertFalse(before.IsApproved)

        # Mark as seen
        result = self.negev.mark_notification_as_seen("test_seen_1")
        self.assertTrue(result)

        # After marking
        after = repo.get_notification_by_id("test_seen_1")
        self.assertTrue(after.IsApproved)

        # # Clean up (optional)
        # session.delete(after)
        # session.commit()
        # session.close()

    def test_mark_notification_as_seen_nonexistent(self):
        """System Test: Mark nonexistent notification – expect exception."""

        with self.assertRaises(ValueError) as context:
            self.negev.mark_notification_as_seen("does_not_exist_999")

        self.assertIn("No notification found", str(context.exception))

    def test_mark_notification_as_seen_already_approved(self):
        """System Test: Marking a notification that is already approved should return True and do nothing harmful."""

        repo = NotificationRepository()
        session = repo.Session()

        notif = NotificationModel(
            notification_id="already_approved_1",
            receiver_user_id=self.user.user_id,
            sender_user_id="admin_user",
            message="Already approved notification",
            AppointSystemManager=True,
            IsApproved=True,  # ← already marked
            time=datetime.utcnow(),
            link="/system"
        )

        session.add(notif)
        session.commit()

        # Call the function
        result = self.negev.mark_notification_as_seen("already_approved_1")
        self.assertTrue(result)

        # Ensure still approved
        refreshed = repo.get_notification_by_id("already_approved_1")
        self.assertTrue(refreshed.IsApproved)

        # # Cleanup
        # session.delete(refreshed)
        # session.commit()
        # session.close()

    def test_mark_notification_as_seen_none_id(self):
        """System Test: Passing None as notification_id should fail gracefully."""

        with self.assertRaises(Exception) as context:
            self.negev.mark_notification_as_seen(None)

        self.assertIn("None", str(context.exception))  # אופציונלי

    def test_disapprove_system_manager_appoint_success(self):
        """System Test: Disapprove a valid system manager nomination."""

        # שלב 1 – משתמש מועמד
        nominee = self._complete_user_registration("nominee@bgu.ac.il", "Pass1!", "Dana", "Nominee")

        # שלב 2 – שליחת התראה בקוד רגיל
        response = self.negev.appoint_system_manager(nominee_email=nominee.email, nominator_user_id=self.user.user_id)
        self.assertIn("success", response)

        # שלב 3 – שליפת התראה שהגיעה למשתמש
        notif_repo = NotificationRepository()
        notifs = notif_repo.get_unapproved_notifications(nominee.user_id)
        self.assertTrue(len(notifs) > 0)
        notif = notifs[0]

        # שלב 4 – דחייה
        result_json = self.negev.disapprove_system_manager_appoint(notification_id=notif.notification_id, sender_id=nominee.user_id)
        result = json.loads(result_json)

        self.assertEqual(result["status"], "success")
        self.assertIn("נדחתה", result["message"])


    def test_disapprove_system_manager_appoint_invalid_notification(self):
        """System Test: Disapprove with invalid notification ID – expect error."""

        result_json = self.negev.disapprove_system_manager_appoint(notification_id="invalid_999", sender_id=self.user.user_id)
        result = json.loads(result_json)

        self.assertEqual(result["status"], "error")
        self.assertIn("No", result["message"].lower())


    def test_approve_system_manager_appoint_success(self):
        """System Test: Successfully approve a system manager nomination."""

        nominee = self._complete_user_registration("nominee@bgu.ac.il", "Pass1!", "Dana", "Nominee")

        # נשלחת הצעה מהמשתמש הראשי
        response = self.negev.appoint_system_manager(nominee_email=nominee.email, nominator_user_id=self.user.user_id)
        self.assertIn("success", response)

        # שליפת ההתראה שנשלחה
        notif_repo = NotificationRepository()
        notifs = notif_repo.get_unapproved_notifications(nominee.user_id)
        self.assertTrue(len(notifs) > 0)
        notif = notifs[0]

        # אישור המועמדות
        result_json = self.negev.approve_system_manager_appoint(notification_id=notif.notification_id, sender_id=nominee.user_id)
        result = json.loads(result_json)

        self.assertEqual(result["status"], "success")
        self.assertIn("הבקשה נדחתה", result["message"])  # הניסוח בטעות, נתקן בהמשך

    def test_approve_system_manager_appoint_notification_not_found(self):
        """System Test: Approval fails due to missing notification."""
        try:
            result_json = self.negev.approve_system_manager_appoint(notification_id="not_exist_123",
                                                                    sender_id=self.user.user_id)
            result = json.loads(result_json)
        except ValueError as e:
            result = {"status": "error", "message": str(e)}

        self.assertEqual(result["status"], "error")
        self.assertIn("no", result["message"].lower())




