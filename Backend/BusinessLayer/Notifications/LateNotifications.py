import uuid
from datetime import datetime
import os
from Backend.BusinessLayer.Notifications.Notification import Notification
from Backend.DataLayer.Noitifications.NotificationRepository import NotificationRepository
from Backend.DataLayer.UserData.UserRepository import UserRepository

from email.mime.text import MIMEText
import smtplib
import logging


class LateNotifications:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance


    def __init__(self):
        """
        Initialize a LateNotifications instance.
        The notifications attribute is a dictionary where the key is the user ID
        and the value is a list of notifications for that user.
        """
        #self.notifications = {}

    def add_notification(self, receiver_id, sender_id, message, isApproved,link,appoint_system_manager, appoint_course_manager, comment_to_following,
                 comment_to_comment, react_to_comment, remove_course_manager):
        notification_id = self.generateNotificationId()
        backend_base_url = os.getenv("BACKEND_BASE_URL", "http://localhost:5001")
        approval_link = f"{backend_base_url}/api/course/mark_as_seen_from_email?notification_id={notification_id}"
        email_body = f"{message}\n\nלאישור וקבלת עדכונים נוספים:\n{approval_link}"

        # 📧 Email config
        sender_email = os.getenv("EMAIL_ADDRESS")
        sender_password = os.getenv("EMAIL_PASSWORD")
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        userRepo = UserRepository()
        receiver_email = userRepo.get_user_email_by_id(receiver_id)
        subject = "התראה חדשה מ-NegevNerds"
        email_body = f"{message}\n\nלאישור וקבלת עדכונים נוספים:\n{approval_link}"
        msg = MIMEText(email_body)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = receiver_email

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            logging.info(f"Notification email sent to {receiver_id}")
        except Exception as e:
            logging.error(f"Failed to send notification email: {e}")
            raise Exception("Failed to send notification email.")
        
        Notification.create(notification_id=notification_id,receiver_user_id=receiver_id, sender_user_id=sender_id,  message=message, timestamp=datetime.now(), 
                             link=link,isApproved=isApproved, appoint_system_manager=appoint_system_manager,appoint_course_manager= appoint_course_manager,
                             comment_to_following=comment_to_following,comment_to_comment=comment_to_comment, react_to_comment=react_to_comment, remove_course_manager= remove_course_manager)

    def generateNotificationId(self):
        return "notification-" + str(uuid.uuid4())



    def get_notification(self, user_id, notification_id):
        """
        Retrieve all notifications for a specific user.

        :param user_id: The ID of the user whose notifications are to be retrieved.
        :return: A list of notifications for the specified user, or an empty list if none exist.
        """
        #if user_id in self.notifications:
        #    if notification_id in self.notifications[user_id]:
        #        return self.notifications[user_id][notification_id]

        notifications_repo = NotificationRepository()
        notification = notifications_repo.get_notifications_by_user_id(user_id=user_id)
        return notification


    def get_user_notifications(self, user_id):
        """
        Retrieve all notifications for a specific user.

        :param user_id: The ID of the user whose notifications are to be retrieved.
        :return: A list of notifications for the specified user, or an empty list if none exist.
        """
        dtos = []
        notifications_repo = NotificationRepository()
        notifications = notifications_repo.get_notifications_by_user_id(user_id=user_id)
        for notification in notifications:
            dtos.append(notification.to_dto())
        #sorted_notifications = sorted(notifications, key=lambda n: n.timestamp, reverse=True)
        return dtos


    def get_last_user_notifications(self, user_id, number_of_notifications):
        """
        Retrieve all notifications for a specific user.

        :param user_id: The ID of the user whose notifications are to be retrieved.
        :return: A list of notifications for the specified user, or an empty list if none exist.
        """
        dtos = []
        notifications_repo = NotificationRepository()
        notifications = notifications_repo.get_last_notifications_by_user_id(user_id=user_id, number_of_notifications=number_of_notifications)
        for notification in notifications:
            dtos.append(notification.to_dto())
        #sorted_notifications = sorted(notifications, key=lambda n: n.timestamp, reverse=True)
        return dtos

    def remove_user_notifications(self, user_id):
        """
        Remove all notifications for a specific user.

        :param user_id: The ID of the user whose notifications are to be removed.
        """
        #if user_id in self.notifications:
        #    del self.notifications[user_id]

        notifications_repo = NotificationRepository()
        notifications_repo.delete_notifications_by_user(user_id=user_id)

    def remove_notification(self, user_id, notification_id):
        """
        Remove all notifications for a specific user.

        :param user_id: The ID of the user whose notifications are to be removed.
        """
        #if user_id in self.notifications:
        #    del self.notifications[user_id]

        notifications_repo = NotificationRepository()
        notifications_repo.delete_notification(notification_id=notification_id)


