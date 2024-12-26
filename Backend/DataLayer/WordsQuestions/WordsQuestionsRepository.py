from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

from Backend.DataLayer.Base import Base


#
# Base = declarative_base()


# Dynamically create table classes for each letter
def create_letter_model(letter, is_hebrew=False):
    table_name = f"{'hebrew' if is_hebrew else 'english'}letter{letter}"
    return type(f"Letter{letter}Model", (Base,), {
        '__tablename__': table_name,
        'word': Column(String,primary_key=True, nullable=False),
        'question_id': Column(Integer,primary_key=True)
    })


# Create model classes for all letters
MODELS = {}

# English letters
for letter in 'abcdefghijklmnopqrstuvwxyz':
    MODELS[letter] = create_letter_model(letter)

# Hebrew letters
for letter in 'פםןוטארקשדגכעיחלךףץתצמנהבסז':
    MODELS[letter] = create_letter_model(letter, is_hebrew=True)


class WordsQuestionsRepository:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '../../..', 'NegevNerds.db')

        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_word_to_question(self, word, question_id):
        session = self.Session()
        first_letter= word[0]
        model = MODELS[first_letter]
        entry = model(word=word,question_id=question_id)
        try:
            session.add(entry)
            session.commit()
        except IntegrityError:
            session.rollback()  # Rollback the transaction if there's an error (duplicate entry)
            print(f"Word '{word}' with question_id '{question_id}' already exists. Skipping.")
        finally:
            session.close()

    def get_questions_id_by_word(self, word):
        first_letter = word[0]
        session = self.Session()
        words = session.query(MODELS[first_letter]).filter_by(word=word).all()
        session.close()
        return words