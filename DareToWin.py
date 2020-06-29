from main import app, db
from main.models import User, Dare, Upvote, Comment, followers, Report

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Dare': Dare, 'Upvote':Upvote, 'Comment':Comment, 'followers':followers, 'Report':Report}
