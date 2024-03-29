from flask import render_template, redirect, url_for, request, \
    abort, current_app, flash
from flask_login import login_user, current_user, logout_user,\
                        login_required
from twittor.forms import LoginForm, RegisterForm, EditProfileForm,\
                        TweetForm, PasswdResetRequestForm, PasswdResetForm
from twittor import db
from twittor.models.user import User
from twittor.models.tweet import Tweet
from twittor.email import send_email

@login_required
def index():
    form = TweetForm()
    if form.validate_on_submit():
        t = Tweet(body=form.tweet.data, author=current_user)
        db.session.add(t)
        db.session.commit()
        return redirect(url_for('index'))
    page_num = int(request.args.get('page') or 1)
    tweets = current_user.own_and_followed_tweets().paginate(page=page_num, per_page=current_app.config['TWEET_PER_PAGE'], error_out=False)
    next_url = url_for('index', page=tweets.next_num) if tweets.has_next else None
    prev_url = url_for('index', page=tweets.prev_num) if tweets.has_prev else None
    return render_template('index.html', form=form, tweets=tweets.items,\
        next_url=next_url, prev_url=prev_url)

def login():
    # 判断用户是否登录
    if current_user.is_authenticated:
        return redirect(url_for('index')) #若登录，重定向到主页

    # 若没有登陆
    form = LoginForm()
    if form.validate_on_submit():
        # 通过数据库验证用户身份
        u = User.query.filter_by(username=form.username.data).first()
        if u is None or not u.check_password(form.password.data): # 如果验证不通过
            print('Invalid username or password')
            return redirect(url_for('login'))
        
        # log user in
        login_user(u, remember=form.remember_me.data)

        # 设置登陆后的重定向页
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('index'))
        
    return render_template('login.html', title="Login", form=form)

# 用户登出，并重定向
def logout():
    logout_user()
    return redirect(url_for('login'))

def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', title='Registration', form=form)

def user(username):
    u = User.query.filter_by(username=username).first()
    if u is None:
        abort(404)
    page_num = int(request.args.get('page') or 1)
    tweets = u.tweets.order_by(Tweet.create_time.desc()).paginate(
        page=page_num, per_page=current_app.config['TWEET_PER_PAGE'], error_out=False)
    prev_url = url_for('profile', page=tweets.prev_num, username=username) if tweets.has_prev else None
    next_url = url_for('profile', page=tweets.next_num, username=username) if tweets.has_next else None
    if request.method == 'POST':
        if request.form['request_button'] == 'Follow':
            print('click follow')
            current_user.follow(u)
            db.session.commit()
        elif request.form['request_button'] == 'Unfollow':
            print('click unfollow')
            current_user.unfollow(u)
            db.session.commit()
        else:
            flash("Send an email to your email address, please check!!!!")
            send_email_for_user_activate(current_user)
    return render_template('user.html',title='Profile', user=u, tweets=tweets.items,\
        prev_url=prev_url, next_url=next_url)

def send_email_for_user_activate(user):
    token = user.get_jwt()
    url_user_activate = url_for(
        'user_activate',
        token=token,
        _external=True
    )
    send_email(
        subject=current_app.config['MAIN_SUBJECT_USER_ACTIVATE'],
        recipients=[user.email],
        text_body= render_template(
            'email/user_activate.txt',
            username=user.username,
            url_user_activate=url_user_activate
        ),
        html_body=render_template(
            'email/user_activate.html',
            username=user.username,
            url_user_activate=url_user_activate
        )
    )

def user_activate(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_jwt(token)
    if not user:
        msg = "Token has expired, please try to re-send email"
    else:
        user.is_activated = True
        db.session.commit()
        msg = 'User has been activated!'
    return render_template('user_activate.html', msg=msg)


def page_not_found(e):
    return render_template('404.html'), 404

def edit_profile():
    form = EditProfileForm()
    if request.method =='GET':
        form.about_me.data = current_user.about_me
    if form.validate_on_submit():
        current_user.about_me = form.about_me.data
        db.session.commit()
        return redirect(url_for('profile', username=current_user.username))
    return render_template('edit_profile.html', form=form)

def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = PasswdResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Reset password link have send to your Email Box.')
        token = user.get_jwt()
        url_password_reset = url_for('password_reset', token=token, _external=True)
        url_password_reset_request = url_for('reset_password_request',  _external=True)
        send_email(
            subject='Twittor - Reset your password',
            recipients=[user.email],
            text_body = render_template(
                'email/passwd_reset.txt',
                url_password_reset_request = url_password_reset_request,
                url_password_reset = url_password_reset
            ),
            html_body = render_template(
                'email/passwd_reset.html',
                url_password_reset_request = url_password_reset_request,
                url_password_reset = url_password_reset
            )
        )
        return redirect(url_for('login'))
    return render_template('password_reset_request.html', form=form)

def password_reset(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_jwt(token)
    if not user:
        return redirect(url_for('index'))
    form = PasswdResetForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template(
        'password_reset.html', title='Password Reset', form=form
    )


def explore():
    # get all user and sort by followers
    page_num = int(request.args.get('page') or 1)
    tweets = Tweet.query.order_by(Tweet.create_time.desc()).paginate(
        page=page_num, per_page=current_app.config['TWEET_PER_PAGE'], error_out=False)

    next_url = url_for('index', page=tweets.next_num) if tweets.has_next else None
    prev_url = url_for('index', page=tweets.prev_num) if tweets.has_prev else None
    return render_template(
        'explore.html', tweets=tweets.items, next_url=next_url, prev_url=prev_url
    )