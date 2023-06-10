
class EmptyField(Exception):
    def __init__(self):
        self.message = "Campo não preenchido."
        super().__init__(self.message)