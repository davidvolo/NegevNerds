from datetime import datetime
from collections import defaultdict

from Backend.BusinessLayer.Util.Exceptions import UserAlreadyPostEmoji, EmojiNotFounded


class Comment:
    def __init__(self, comment_id, writer_name, date=None, prev_id=None, text=""):
        """
        Initialize a Comment instance.
        """
        self.id = comment_id
        self.writer_name = writer_name
        self.date = date if date else datetime.now()  # Default to current date if not provided
        self.prev_id = prev_id
        self.text = text
        self.emoji_counter_map = {"like": set(), "dislike": set()}

    def add_emoji(self, emoji, userId):
        """
        Add an emoji to the comment, incrementing its count.
        """
        if userId not in self.emoji_counter_map[emoji]:
            self.emoji_counter_map[emoji].add(userId)
            if emoji == "dislike":
                self.emoji_counter_map["like"].remove(userId)
            else:
                self.emoji_counter_map["like"].remove(userId)
        else:
            raise UserAlreadyPostEmoji

    def remove_emoji(self, emoji):

        if emoji in self.emoji_counter_map and self.emoji_counter_map[emoji] > 0:
            self.emoji_counter_map[emoji] -= 1
        else:
            raise EmojiNotFounded

    def edit_text(self, new_text):
        self.text = new_text

    def get_score(self):
        return self.emoji_counter_map["like"] - self.emoji_counter_map["dislike"]
