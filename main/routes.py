from main import app, db
from flask import render_template, redirect, flash, url_for, request, send_from_directory, abort
from flask_login import current_user, login_user, logout_user, login_required
from main.models import User, Dare, Upvote, Comment, followers, Report
from main.forms import LoginForm, RegistrationForm, UploadDareForm, EditProfileForm, EmptyForm, CommentForm, SearchProfileForm, ResetPasswordRequestForm, ResetPasswordForm, ReportForm
from werkzeug.urls import url_parse
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from main.email import send_password_reset_email


@app.before_request
def before_request():
    if current_user.is_authenticated:
        if current_user.banned == 1 and request.path != url_for('logout'):
            return render_template('banned.html', title = 'Banned')
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/', methods = ['GET', 'POST'])
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember = form.remember_me.data)
        flash('Logged in successfully')
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            if user.id == 1:
                next_page = url_for('new_reports')
            else:
                next_page = url_for('home')
        return redirect(next_page)
    return render_template('login.html', form = form)


@app.route('/register', methods = ['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username = form.username.data, name = form.name.data, email = form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you have successfully registered!')
        return redirect(url_for('login'))
    return render_template('register.html', title = 'Registeration', form = form)


@app.route('/home', methods = ['GET', 'POST'])
@login_required
def home():
    form0 = SearchProfileForm()
    form = UploadDareForm()
    form3 = EmptyForm()
    page = request.args.get('page', 1, type = int)
    posts = current_user.followed_posts().filter_by(banned = 0).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = None
    prev_url = None
    if posts.has_next:
        next_url = url_for('home', page = posts.next_num)
    if posts.has_prev:
        prev_url = url_for('home', page = posts.prev_num)
    return render_template('home.html', title = 'Home', posts = posts.items, form = form, next_url = next_url, prev_url = prev_url, form3 = form3, form0 = form0)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/profile/<string:username>')
@login_required
def profile(username):
    user = User.query.filter_by(username = username).first_or_404()
    if user.banned == 0 or current_user.id == 1:
        form0 = SearchProfileForm()
        form3 = EmptyForm()
        form = EmptyForm()
        form1 = UploadDareForm()
        form2 = ReportForm()
        page = request.args.get('page', 1, type = int)
        posts = user.dares.filter_by(banned = 0).order_by(Dare.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
        next_url = url_for('profile', username = username, page = posts.next_num)\
        if posts.has_next else None
        prev_url = url_for('profile', username = username, page = posts.prev_num)\
        if posts.has_prev else None
        banned_dares = user.dares.filter_by(banned = 1)
        return render_template('profile.html', title = 'Profile', user = user, posts = posts.items, prev_url = prev_url, next_url = next_url, form3 = form3, form0 = form0, form = form, form1 = form1, form2 = form2, banned_dares = banned_dares)
    return render_template('banned.html', title = 'Banned')


@app.route('/upload', methods = ['POST'])
def upload():
    form = UploadDareForm()
    if form.validate_on_submit():
        dare = Dare(dare = form.dare_desc.data, user = current_user)
        db.session.add(dare)
        db.session.commit()
        vid = form.dare_vid.data
        local_path = app.config["DAREVIDS_UPLOADS"]
        specific_path = local_path + '/' + str(current_user.id) + '_' + current_user.username
        os.chdir(local_path)
        if not os.path.exists(str(current_user.id) + '_' + current_user.username):
            os.mkdir(str(current_user.id) + '_' + current_user.username)
        vidname = secure_filename(str(dare.id) + '.mp4')
        vid.save(os.path.join(specific_path, vidname))
        proper_path = app.config["PROPER_PATH"]
        os.chdir(proper_path)
        return redirect(request.referrer)
    return redirect(request.referrer)


@app.route('/view_dare/<int:dare_id>')
@login_required
def view_dare(dare_id):
    dare = Dare.query.get_or_404(dare_id)
    if dare.banned == 0 or current_user.id == 1:
        form0 = SearchProfileForm()
        form = EmptyForm() #sending form to view_dare
        form1 = CommentForm()
        form2 = EmptyForm()
        form3 = EmptyForm()
        form4 = ReportForm()
        voted = False
        vote = Upvote.query.filter_by(dare = dare, user = current_user).first()
        if vote:
            voted = True
        comments = Comment.query.filter_by(dare = dare).order_by(Comment.timestamp.desc())
        prev = request.args.get('prev')
        return render_template('view_dare.html', title = 'Viewing Dare', dare = dare, form = form, voted = voted, form1 = form1, comments = comments, form2 = form2, form3 = form3, form0 = form0, prev = prev, form4 = form4)
    return render_template('banned.html', title = 'Banned')


@app.route('/open_dare/<int:dare_id>')
@login_required
def open_dare(dare_id):
    try:
        dare = Dare.query.get_or_404(dare_id)
        user = dare.user
        directory = app.config['DAREVIDS_UPLOADS'] + '/' + str(user.id) + '_' + user.username
        return send_from_directory(directory, filename = str(dare_id) + '.mp4', as_attachment = False)
    except FileNotFoundError:
        abort(404)


def badge(user):
    all_dares = Dare.query.filter_by(user = user)
    votes = 0
    for dare in all_dares:
        votes = votes + dare.votes
    if votes > 4:
        return 'Viking '
    elif votes > 3:
        return 'Hero '
    elif votes > 2:
        return 'Daredevil '
    elif votes > 1:
        return 'Fearless '
    elif votes > 0:
        return 'Brave '
    else:
        return 'Rookie' 


@app.route('/vote/<int:dare_id>', methods = ['POST'])
@login_required
def vote(dare_id): #form.validate nth to validate tho, can dont put form and form.validate as well
    form = EmptyForm() #using form to validate in post req
    if form.validate_on_submit():
        dare = Dare.query.get_or_404(dare_id)
        check_voted = Upvote.query.filter_by(dare = dare, user = current_user).first()
        if check_voted:
            dare.votes = dare.votes - 1
            db.session.delete(check_voted)
            db.session.commit()
            flash('Downvoted! :(')
        else:
            dare.votes = dare.votes + 1
            new_vote = Upvote(dare = dare, user = current_user)
            db.session.add(new_vote)
            db.session.commit()
            flash('Upvoted! :)')
        user = dare.user
        user.badge = badge(user)
        db.session.commit()
        return redirect(request.referrer) #goes to the url the referred u here, have redirect after every successful post good habit, as may cause issues in refresh
    return redirect(request.referrer) #csrf token expired or invalid


@app.route('/comment/<int:dare_id>', methods = ['POST'])
@login_required
def comment(dare_id):
    form = CommentForm()
    if form.validate_on_submit():
        dare = Dare.query.get(dare_id)
        comment = Comment(content = form.content.data, dare = dare, user = current_user)
        db.session.add(comment)
        db.session.commit()
        return redirect(request.referrer)
    return redirect(request.referrer)


@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    form = EmptyForm()
    if form.validate_on_submit():
        comment = Comment.query.get(comment_id)
        db.session.delete(comment)
        db.session.commit()
        flash('Comment deleted')
        return redirect(request.referrer)
    return redirect(request.referrer)


@app.route('/delete_dare/<int:dare_id>', methods=['POST'])
@login_required
def delete_dare(dare_id):
    form = EmptyForm()
    if form.validate_on_submit():
        dare = Dare.query.get(dare_id)
        for comment in dare.comments:
            db.session.delete(comment)
            db.session.commit()
        for upvote in dare.upvotes:
            db.session.delete(upvote)
            db.session.commit()
        prev_url = ''
        try:
            prev_url = request.args.get('prev') #only if come from viewdare
            if url_parse(prev_url).netloc != '':
                prev_url = url_for('home')
        except:
            prev_url = request.referrer

#        if prev_url.split('/')[3] == 'view_dare':
#            prev_url = prev_url.split('=')[1].replace('%2F', '/')
#        if prev_url.find('+'):
#            prev_url = prev_url.replace('+', '%20') 
#            prev_url = prev_url.request.args.get('prev')
#            if url_parse(prev_url).netloc != '':
#                prev_url = url_for('home')


        user = dare.user
        dare.votes = 0
        db.session.commit()
        user.badge = badge(user)
        
        local_path = app.config['DAREVIDS_UPLOADS']
        delete_file_path = local_path + '/' + str(user.id) + '_' + user.username
        os.chdir(delete_file_path)
        os.remove(str(dare.id) + '.mp4')
        os.chdir(app.config['PROPER_PATH'])

        reports = Report.query.filter_by(dare = dare)
        if reports:
            for report in reports:
                report.content = report.content + ' Dare deleted by owner.'
                db.session.commit()
        db.session.delete(dare)
        db.session.commit()
        flash('Dare deleted')
        return redirect(prev_url)
    return redirect(request.referrer)


@app.route('/edit_profile', methods = ['GET', 'POST'])
@login_required
def edit_profile():
    form0 = SearchProfileForm()
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved')
        return redirect(url_for('profile', username = current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title = 'Edit Profile', form = form, form0 = form0)
    

@app.route('/leaderboard')
@login_required
def leaderboard():
    form0 = SearchProfileForm()
    form3 = EmptyForm()
    page = request.args.get('page', 1, type = int)
    posts = Dare.query.filter_by(banned = 0).order_by(Dare.votes.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False) ############limit
    next_url = url_for('leaderboard', page = posts.next_num)\
        if posts.has_next else None
    prev_url = url_for('leaderboard', page = posts. prev_num)\
        if posts.has_prev else None
    page_num = request.args.get('page', '1')
    start_num = int(page_num) * 3 - 2
    return render_template('leaderboard.html', title = 'Leadeboard', posts = posts.items, next_url = next_url, prev_url = prev_url, form3 = form3, form0 = form0, start_num = start_num)


@app.route('/search', methods = ['POST'])
@login_required
def search():
    form0 = SearchProfileForm()
    if form0.validate_on_submit():
        return redirect(url_for('profile', username = form0.username.data))
    flash('Invalid Username')
    return redirect(request.referrer)


@app.route('/resetpassreq', methods = ['GET', 'POST'])
def resetpassreq():
    if current_user.is_authenticated:
        return redirect('/home')
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login')) 
    return render_template('resetpassreq.html', form = form, title = 'Reset Password Request')


@app.route('/resetpassword/<string:token>', methods = ['GET', 'POST'])
def resetpassword(token):
    if current_user.is_authenticated:
        return redirect('/home')
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset')
        return redirect(url_for('login'))
    return render_template('resetpassword.html', form = form, title = 'ResetPassword')


@app.route('/handle_follow/<string:username>', methods = ['POST'])
def handle_follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = username).first()
        if user is None:
            flash('User ' + username + ' not found')
            return redirect(request.referrer)
        if current_user == user:
            flash('You cannot follow or unfollow yourself')
            return redirect(request.referrer)
        if current_user.is_following(user):
            current_user.unfollow(user)
            flash('You have unfollowed ' + username)
        else:
            current_user.follow(user)
            flash('You are now following ' + username)
        db.session.commit()
        return redirect(request.referrer)
    return redirect(request.referrer)


@app.route('/report', methods = ['GET', 'POST'])
def report():
    form = ReportForm()
    if form.validate_on_submit():
        prev_url = request.args.get('prev')
        if url_parse(prev_url).netloc != '':
            prev_url = url_for('home')
        report = ''
        if prev_url.find('view_dare') == 1:
            dare_id = prev_url.split('/')[2]
            report = Report(content = form.report.data, page_of_report = prev_url, reporter = current_user, dare_id = dare_id)
        elif prev_url.find('profile') == 1:
            print(prev_url)
            profile_username = prev_url.split('/')[2]
            user = User.query.filter_by(username = profile_username).first()
            report = Report(content = form.report.data, page_of_report = prev_url, reporter = current_user, user = user)
        else:
            report = Report(content = form.report.data, page_of_report = prev_url, reporter = current_user)
        db.session.add(report)
        db.session.commit()
        flash('Your report has been submitted. Thank you for your feedback')
        return redirect(prev_url)
    return render_template('report.html', form = form, title = 'Report')


@app.route('/new_reports', methods = ['GET', 'POST']) #2 issues, if person clicks report after clicking report, then the prev page is now report and the home page goes to admin hime and not the person home
def new_reports():
    form = ReportForm()
    if form.validate_on_submit():
        id = request.args.get('id')
        report = Report.query.get_or_404(id)
        report.action_taken = form.report.data
        report.seen = 1
        db.session.commit()
        return redirect(url_for('new_reports'))
    page = request.args.get('page', 1, type = int)
    reports = Report.query.filter_by(seen = 0).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('new_reports', page = reports.next_num)\
    if reports.has_next else None
    prev_url = url_for('new_reports', page = reports.prev_num)\
    if reports.has_prev else None
    return render_template('new_reports.html', reports = reports.items, form = form, prev_url = prev_url, next_url = next_url, title = 'New Reports')


@app.route('/ban', methods = ['POST'])
def ban():
    print('ban')
    form = ReportForm()
    if form.validate_on_submit():
        print('validate')
        prev_url = request.referrer
        profile_username = ''
        print(prev_url)
        print(prev_url.find('view_dare'))
        if prev_url.find('view_dare') != -1:
            print('in view')
            dare_id = prev_url.split('/')[4]
            dare = Dare.query.get(dare_id)
            profile_username = dare.user.username
            dare.banned = 1
            dare.votes = 0
            dare.ban_reason = form.report.data
            db.session.commit()
            user = User.query.filter_by(username = profile_username).first()
            user.badge = badge(user)
            db.session.commit()
            reports = Report.query.filter_by(dare = dare)
            for report in reports:
                report.seen = 1
                report.action_taken = form.report.data
                db.session.commit()
        elif prev_url.find('profile') != -1:
            print('in profile')
            profile_username = request.args.get('prev').split('/')[2]
            user = User.query.filter_by(username = profile_username).first()
            print(user)
            print(user.banned)
            user.banned = 1
            print('user.banned')
            user.ban_reason = form.report.data
            db.session.commit()
            print('commit')
            reports = Report.query.filter_by(user = user)
            print('report')
            for report in reports:
                report.seen = 1
                report.action_taken = form.report.data
                db.session.commit()
        print('redirect prof')
        return redirect(url_for('profile', username = profile_username))
    return redirect(request.referrer)
