class ProgressBar:
    def __init__(self, total, width=50):
        self.total = total
        self.width = width
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args, **kwargs):
        self.update(self.total)
        print()

    def update(self, value):
        fullchars = int(value / self.total * self.width)
        emptychars = self.width - fullchars
        print(f'{"█" * fullchars}{"-" * emptychars}', end='\r')
