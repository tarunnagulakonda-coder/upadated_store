from datetime import datetime, date
from models import db


class Banner(db.Model):
    __tablename__ = 'banners'

    id = db.Column(db.Integer, primary_key=True)
    # Path relative to the static folder, e.g. 'uploads/banners/abc.jpg'
    image = db.Column(db.String(255), nullable=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    offer_text = db.Column(db.String(100), nullable=True)
    button_text = db.Column(db.String(50), nullable=True)
    redirect_url = db.Column(db.String(255), nullable=True)
    # 'Active' or 'Inactive'
    status = db.Column(db.String(20), default='Active', nullable=False)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_active(self):
        return self.status == 'Active'

    def is_visible(self, on_date=None):
        """A banner is shown to customers only when it is Active
        and (if set) today falls within [start_date, end_date]."""
        if self.status != 'Active':
            return False
        today = on_date or date.today()
        if self.start_date and self.start_date > today:
            return False
        if self.end_date and self.end_date < today:
            return False
        return True

    @classmethod
    def visible(cls):
        """Banners for the customer site, in admin-defined order."""
        banners = cls.query.filter_by(status='Active') \
            .order_by(cls.display_order.asc(), cls.id.asc()).all()
        return [b for b in banners if b.is_visible()]
