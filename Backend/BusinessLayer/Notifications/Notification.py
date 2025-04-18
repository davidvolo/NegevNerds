from Backend.DataLayer.DTOs.NotificationDTO import NotificationDTO
from Backend.DataLayer.Noitifications.NotificationRepository import NotificationRepository


class Notification:
    def __init__(self, notification_id ,receiver_user_id, sender_user_id, message, timestamp,link,isApproved = False ,
                 appoint_system_manager=False, appoint_course_manager=False, comment_to_following=False,
                 comment_to_comment=False, react_to_comment=False, remove_course_manager=False):
        self.notification_id = notification_id
        self.receiver_user_id = receiver_user_id
        self.sender_user_id = sender_user_id
        self.message = message
        self.timestamp = timestamp
        self.link = link
        self.isApproved= isApproved
        self.appoint_system_manager = appoint_system_manager
        self.appoint_course_manager = appoint_course_manager
        self.comment_to_following = comment_to_following
        self.comment_to_comment = comment_to_comment
        self.react_to_comment = react_to_comment
        self.remove_course_manager = remove_course_manager

    @classmethod
    def create(cls, notification_id, receiver_user_id, sender_user_id, message, timestamp,link,isApproved = False ,
               appoint_system_manager=False, appoint_course_manager=False, comment_to_following=False,
               comment_to_comment=False, react_to_comment=False, remove_course_manager=False):
        """
        Class method to create a new notification and save it to the database.

        Returns:
            Notification: Newly created notification instance
        """
        notification = cls(
            notification_id=notification_id,
            receiver_user_id=receiver_user_id,
            sender_user_id=sender_user_id,
            message=message,
            timestamp=timestamp,
            link = link,
            isApproved = isApproved,
            appoint_system_manager=appoint_system_manager,
            appoint_course_manager=appoint_course_manager,
            comment_to_following=comment_to_following,
            comment_to_comment=comment_to_comment,
            react_to_comment=react_to_comment,
            remove_course_manager=remove_course_manager
        )
        notification_repository = NotificationRepository()
        notification_repository.add_notification(notification=notification)
        return notification

    def to_dto(self):
        return NotificationDTO(
            notification_id=self.notification_id,
            receiver_user_id=self.receiver_user_id,
            sender_user_id=self.sender_user_id,
            message=self.message,
            timestamp=self.timestamp,
            link = self.link,
            isApproved = self.isApproved,
            appoint_system_manager=self.appoint_system_manager,
            appoint_course_manager=self.appoint_course_manager,
            comment_to_following=self.comment_to_following,
            comment_to_comment=self.comment_to_comment,
            react_to_comment=self.react_to_comment,
            remove_course_manager=self.remove_course_manager
        )

    def __str__(self):
        return f"Notification for {self.receiver_user_id}: from {self.sender_user_id} - {self.message} (Sent at {self.timestamp})"
