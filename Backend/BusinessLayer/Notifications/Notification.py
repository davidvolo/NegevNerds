from Backend.DataLayer.Noitifications.NotificationRepository import NotificationRepository


class Notification:
    def __init__(self, receiver_user_id,sender_user_id , message, timestamp, need_approval, notification_id):
        self.receiver_user_id = receiver_user_id
        self.sender_user_id = sender_user_id
        self.message = message
        self.timestamp = timestamp
        self.need_approval = need_approval
        self.notification_id = notification_id

    @classmethod
    def create(cls, receiver_user_id,sender_user_id , message, timestamp, need_approval, notification_id):
        """
        Class method to create a new user and save to database

        Returns:
            User: Newly created user instance
        """
        notification = cls(
            receiver_user_id=receiver_user_id,
            sender_user_id=sender_user_id,
            timestamp=timestamp,
            need_approval=need_approval,
            message=message,
            notification_id=notification_id
        )
        notification_repository = NotificationRepository()
        notification_repository.add_Notification(notification=notification)
        return notification


    def __str__(self):
        return f"Notification for User {self.receiver_user_id}: from user{self.sender_user_id}- {self.message} (Sent at {self.timestamp})"
