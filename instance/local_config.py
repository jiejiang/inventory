DEBUG = True

UPLOAD_FOLDER = 'upload'

DOWNLOAD_FOLDER = 'download'

SQLALCHEMY_TRACK_MODIFICATIONS = True

SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://postgres:devserver@localhost/postorders'

BATCH_ORDER_QUEUE = 'batch_order'