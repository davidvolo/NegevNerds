import json
import os
from unittest.mock import patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Backend.DataLayer.Base import Base, delete_all_data
from Backend.DataLayer.Noitifications.NotificationModel import NotificationModel
from datetime import datetime, timedelta

from Backend.DataLayer.Noitifications.NotificationRepository import NotificationRepository
from Backend.DataLayer.SystemManagers.SystemManagersRepository import SystemManagersRepository
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
        self.course_id = "777.1.1010"
        self.nominee_email = "new_manager@bgu.ac.il"
        self.nominator_user_id = "user123"

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

        mock_repo_instance = MagicMock()
        mock_repo_instance.get_unapproved_notifications.return_value = fake_notifications
        mock_notification_repo_class.return_value = mock_repo_instance

        response_json = self.negev.get_unapproved_notification_list(user_id=user_id)
        response = json.loads(response_json)

        self.assertTrue(response["success"])
        self.assertEqual(len(response["notifications"]), 3)
        types = {n["type"] for n in response["notifications"]}
        self.assertSetEqual(types, {"AppointSystemManager", "AppointCourseManager", "CommentToFollowing"})

    def test_get_unapproved_notifications_returns_empty_when_none(self):
        user = self._complete_user_registration("empty@post.bgu.ac.il", "ValidPass1!", "אין", "התראות")

        result = self.negev.get_unapproved_notification_list(user.user_id)
        data = json.loads(result)

        self.assertTrue(data["success"])
        self.assertEqual(data["notifications"], [])

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

    def test_mark_notification_as_seen_none_id(self):
        """System Test: Passing None as notification_id should fail gracefully."""

        with self.assertRaises(Exception) as context:
            self.negev.mark_notification_as_seen(None)

        self.assertIn("None", str(context.exception))

    @patch("Backend.BusinessLayer.Notifications.LateNotifications.socketio.emit")
    def test_appoint_system_manager_success(self, mock_socket_emit):
        """System Test: Successfully send nomination to an existing non-manager user."""

        nominee = self._complete_user_registration("newuser@bgu.ac.il", "Pass1!", "Dana", "Nominee")

        response_json = self.negev.appoint_system_manager(
            nominee_email=nominee.email,
            nominator_user_id=self.user.user_id
        )

        result = json.loads(response_json)
        self.assertEqual(result["status"], "success")
        self.assertIn("successfully", result["message"])

    def test_appoint_system_manager_already_manager(self):
        """System Test: User is already a system manager – should return error."""

        nominee = self._complete_user_registration("existing@bgu.ac.il", "Pass1!", "Tom", "Manager")

        system_repo = SystemManagersRepository()
        system_repo.add_system_manager(nominee.user_id)

        response_json = self.negev.appoint_system_manager(
            nominee_email=nominee.email,
            nominator_user_id=self.user.user_id
        )

        result = json.loads(response_json)
        self.assertEqual(result["status"], "error")
        self.assertIn("כבר הינו מנהל מערכת", result["message"])

    def test_appoint_system_manager_email_not_found(self):
        """System Test: Email not registered in the system – expect error."""

        response_json = self.negev.appoint_system_manager(
            nominee_email="ghost@bgu.ac.il",
            nominator_user_id=self.user.user_id
        )

        result = json.loads(response_json)
        self.assertEqual(result["status"], "error")
        self.assertIn("לא קיים", result["message"])

    def test_appoint_system_manager_invalid_email(self):
        """System Test: Invalid email format – should return error."""

        response_json = self.negev.appoint_system_manager(
            nominee_email="not-an-email",
            nominator_user_id=self.user.user_id
        )

        result = json.loads(response_json)
        self.assertEqual(result["status"], "error")
        self.assertIn("אימייל חוקי", result["message"])

    def test_disapprove_system_manager_appoint_success(self):
        """System Test: Disapprove a valid system manager nomination."""
        nominee = self._complete_user_registration("nominee@bgu.ac.il", "Pass1!", "Dana", "Nominee")

        response = self.negev.appoint_system_manager(nominee_email=nominee.email, nominator_user_id=self.user.user_id)
        self.assertIn("success", response)

        notif_repo = NotificationRepository()
        notifs = notif_repo.get_unapproved_notifications(nominee.user_id)
        self.assertTrue(len(notifs) > 0)
        notif = notifs[0]

        result_json = self.negev.disapprove_system_manager_appoint(notification_id=notif.notification_id,
                                                                   sender_id=nominee.user_id)
        result = json.loads(result_json)

        self.assertEqual(result["status"], "success")
        self.assertIn("נדחתה", result["message"])

    def test_disapprove_system_manager_appoint_invalid_notification(self):
        """System Test: Disapprove with invalid notification ID – expect error."""
        result_json = self.negev.disapprove_system_manager_appoint(notification_id="invalid_999",
                                                                   sender_id=self.user.user_id)
        result = json.loads(result_json)

        self.assertEqual(result["status"], "error")
        self.assertIn("no", result["message"].lower())

    def test_approve_system_manager_appoint_success(self):
        """System Test: Successfully approve a system manager nomination."""
        nominee = self._complete_user_registration("nominee@bgu.ac.il", "Pass1!", "Dana", "Nominee")

        response = self.negev.appoint_system_manager(nominee_email=nominee.email, nominator_user_id=self.user.user_id)
        self.assertIn("success", response)

        notif_repo = NotificationRepository()
        notifs = notif_repo.get_unapproved_notifications(nominee.user_id)
        self.assertTrue(len(notifs) > 0)
        notif = notifs[0]

        result_json = self.negev.approve_system_manager_appoint(notification_id=notif.notification_id,
                                                                sender_id=nominee.user_id)
        result = json.loads(result_json)

        self.assertEqual(result["status"], "success")
        self.assertIn("הבקשה נדחתה", result["message"])

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

    @patch("Backend.DataLayer.CourseData.CourseRepository.CourseRepository.get_course_by_id")
    @patch("Backend.DataLayer.CourseManagers.CourseManagersRepository.CourseManagersRepository.is_exist",
           return_value=False)
    @patch("Backend.BusinessLayer.User.UserFacade.UserFacade.getUser_by_id")
    @patch("Backend.BusinessLayer.User.UserFacade.UserFacade.getUser_by_email")
    @patch("Backend.BusinessLayer.User.UserFacade.UserFacade.is_valid_email", return_value=True)
    @patch("Backend.BusinessLayer.User.UserFacade.UserFacade.should_send_notification", return_value=False)
    @patch("Backend.BusinessLayer.Notifications.NotificationFacade.NotificationFacade.send_notification")
    def test_appoint_course_manager_success(
        self, mock_notify, mock_should_notify, mock_valid_email, mock_get_user_by_email,
        mock_get_user_by_id, mock_is_exist, mock_get_course_by_id
    ):
        # Arrange
        nominee_user = MagicMock()
        nominee_user.user_id = "nominee123"
        mock_get_user_by_email.return_value = nominee_user

        nominator_user = MagicMock()
        nominator_user.get_first_name.return_value = "Alice"
        nominator_user.get_last_name.return_value = "Cohen"
        mock_get_user_by_id.return_value = nominator_user

        mock_get_course_by_id.return_value.name = "Introduction to Testing"

        # Act
        result_json = self.negev.appoint_course_manager(
            self.nominee_email, self.nominator_user_id, self.course_id
        )
        result = json.loads(result_json)

        # Assert
        self.assertEqual(result["status"], "success")
        self.assertIn("nomination", result["message"].lower())
        mock_notify.assert_called_once()

    @patch("Backend.DataLayer.CourseData.CourseRepository.CourseRepository.get_course_by_id")
    @patch("Backend.DataLayer.CourseManagers.CourseManagersRepository.CourseManagersRepository.is_exist",
           return_value=True)
    @patch("Backend.BusinessLayer.User.UserFacade.UserFacade.getUser_by_email")
    @patch("Backend.BusinessLayer.User.UserFacade.UserFacade.is_valid_email", return_value=True)
    def test_appoint_course_manager_already_manager(
            self, mock_valid_email, mock_get_user_by_email, mock_is_exist, mock_get_course_by_id
    ):
        nominee_user = MagicMock()
        nominee_user.user_id = "existing_manager_1"
        mock_get_user_by_email.return_value = nominee_user

        result_json = self.negev.appoint_course_manager(
            self.nominee_email, self.nominator_user_id, self.course_id
        )
        result = json.loads(result_json)

        self.assertEqual(result["status"], "error")
        self.assertIn("כבר הינו מנהל קורס", result["message"])

    def test_disapprove_course_manager_appoint_success(self):
        """System Test: Successfully disapprove a course manager nomination."""
        nominee = self._complete_user_registration("cm_nominee@bgu.ac.il", "Passwords1!", "נוגה", "בנימיני")

        # Simulate course manager appointment notification
        self.negev.appoint_course_manager(nominee_email=nominee.email,
                                          nominator_user_id=self.user.user_id,
                                          course_id=self.course_id)

        repo = NotificationRepository()
        notifs = repo.get_unapproved_notifications(nominee.user_id)
        self.assertGreater(len(notifs), 0)
        notif = notifs[0]

        # Act
        result_json = self.negev.disapprove_course_manager_appoint(
            notification_id=notif.notification_id,
            sender_id=nominee.user_id
        )
        result = json.loads(result_json)

        # Assert
        self.assertEqual(result["status"], "success")
        self.assertIn("נדחתה", result["message"])

    def test_disapprove_course_manager_appoint_notification_not_found(self):
        """System Test: Disapproval fails due to missing notification."""
        result_json = self.negev.disapprove_course_manager_appoint(
            notification_id="invalid_notif_id_123",
            sender_id=self.user.user_id
        )
        result = json.loads(result_json)

        self.assertEqual(result["status"], "error")
        self.assertIn("found", result["message"].lower())

    def test_approve_course_manager_appoint_success(self):
        """System Test: Successfully approve a course manager nomination."""
        nominee = self._complete_user_registration("approve@bgu.ac.il", "Pass1!", "Roni", "Tal")

        self.negev.appoint_course_manager(
            nominee_email=nominee.email,
            nominator_user_id=self.user.user_id,
            course_id=self.course_id
        )

        repo = NotificationRepository()
        notifs = repo.get_unapproved_notifications(nominee.user_id)
        self.assertGreater(len(notifs), 0)
        notif = notifs[0]

        result_json = self.negev.approve_course_manager_appoint(
            notification_id=notif.notification_id,
            sender_id=nominee.user_id
        )
        result = json.loads(result_json)

        self.assertEqual(result["status"], "success")
        self.assertIn("הבקשה נדחתה", result["message"])

    def test_approve_course_manager_appoint_notification_not_found(self):
        """System Test: Approval fails due to missing notification."""
        result_json = self.negev.approve_course_manager_appoint(
            notification_id="not_exist_course_appoint_123",
            sender_id=self.user.user_id
        )
        result = json.loads(result_json)

        self.assertEqual(result["status"], "error")
        self.assertIn("found", result["message"].lower())

    def test_get_notification_settings_success(self):
        """System Test: Successfully retrieve default notification settings."""
        settings = self.negev.get_notification_settings(self.user.user_id)
        self.assertIsInstance(settings, dict)
        self.assertIn("AppointSystemManager", settings)
        self.assertIn("AppointCourseManager", settings)
        self.assertIn("ReactToComment", settings)

    def test_get_notification_settings_invalid_user(self):
        """System Test: Get notification settings for a non-existent user – expect default or error."""
        fake_user_id = "not_exist_user"
        try:
            settings = self.negev.get_notification_settings(fake_user_id)
            self.assertIsInstance(settings, dict)
        except Exception as e:
            self.assertIn("error", str(e).lower())

    def test_update_notification_settings_success(self):
        """System Test: Successfully update notification settings."""
        settings_to_update = {
            "AppointSystemManager": False,
            "ReactToComment": False
        }
        result = self.negev.update_notification_settings(user_id=self.user.user_id, settings_dict=settings_to_update)
        self.assertTrue(result)

    def test_update_notification_settings_invalid_user(self):
        """System Test: Fail to update settings for nonexistent user."""
        with self.assertRaises(Exception) as context:
            self.negev.update_notification_settings(user_id="invalid_user_999", settings_dict={"ReactToComment": False})

        self.assertIn("error", str(context.exception).lower())
