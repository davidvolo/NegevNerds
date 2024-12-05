from enum import Enum

class Moed(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


    def __str__(self):
        return self.value

class Semester(Enum):
    FALL = "Fall"
    SPRING = "Spring"
    SUMMER = "Summer"

    def __str__(self):
        return self.value
