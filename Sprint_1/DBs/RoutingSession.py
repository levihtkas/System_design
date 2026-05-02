from sqlalchemy.orm  import Session

class RoutingSession(Session):
    def __init__(self, master_engine, replica_engine, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.master_engine = master_engine
        self.replica_engine = replica_engine
    def get_bind(self, mapper = None, *, clause = None, bind = None, **kw):
        if self._flushing or self.in_transaction():
            return self.master_engine
        else:
            return self.replica_engine