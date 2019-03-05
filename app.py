from flask import Flask, render_template,request,url_for,redirect,flash
from flask_sqlalchemy import SQLAlchemy  # 导入扩展类
import os
import sys
import click
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import datetime

WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
app.config['SECRET_KEY'] = 'dev'  # 等同于 app.secret_key = 'dev'

# ...



db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

class Work(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uname = db.Column(db.String(20))
    recordtime = db.Column(db.DateTime)
    project = db.Column(db.String(5))
    uwork = db.Column(db.Text)

class Period(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

def dateformat(val):
    return str(val)[:11]
def datetime2date(val):
    return datetime.date(val.year,val.month,val.day)
def datetime2str(val):
    return str(val)[:11]
env = app.jinja_env
env.filters['dateformat'] = dateformat
env.filters['datetime2date'] = datetime2date
env.filters['datetime2str'] = datetime2str

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    return user

@app.route('/',methods=['GET','POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('No such user.')  # 如果验证失败，显示错误消息
            return redirect(url_for('login'))  # 重定向回登录页面
        else:
            # 验证用户名和密码是否一致
            if username == user.username and user.validate_password(password):
                if user.name == "admin" or user.name == "Admin":
                    login_user(user)
                    flash('Login success')
                    return redirect(url_for('search'))
                else:
                    login_user(user)  # 登入用户
                    flash('Login success.')
                    return redirect(url_for('work'))  # 重定向到主页

            flash('Invalid username or password.')  # 如果验证失败，显示错误消息
            return redirect(url_for('login'))  # 重定向回登录页面
    
    return render_template('login.html')

@app.route('/work',methods=['GET','POST'])
@login_required
def work():
    if request.method=='POST':
        uname       = current_user.username
        recordtime  = datetime.datetime.strptime(str(request.form['recordtime']),'%Y-%m-%d')
        project     = request.form['project']
        uwork       = request.form['uwork']
        if not project:
            flash('Invalid input.')
            return redirect(url_for('work'))
        temp=Work(uname=uname,recordtime=recordtime,project=project,uwork=uwork)
        db.session.add(temp)
        db.session.commit()
        flash('Item added.')
        return redirect(url_for('work'))

    # works=Work.query.all()
    works=Work.query.filter_by(uname=current_user.username)
    u = User.query.filter_by(username=current_user.username).first()
    return render_template('work.html', works=works,user=u)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('No such user.')  # 如果验证失败，显示错误消息
            return redirect(url_for('login'))  # 重定向回登录页面
        else:
            # 验证用户名和密码是否一致
            if username == user.username and user.validate_password(password):
                if user.name == "admin" or user.name == "Admin":
                    login_user(user)
                    flash('Login success')
                    return redirect(url_for('search'))
                else:
                    login_user(user)  # 登入用户
                    flash('Login success.')
                    return redirect(url_for('work'))  # 重定向到主页

            flash('Invalid username or password.')  # 如果验证失败，显示错误消息
            return redirect(url_for('login'))  # 重定向回登录页面
    
    return render_template('login.html')

@app.route('/logout')
@login_required  # 用于视图保护，后面会详细介绍
def logout():
    logout_user()  # 登出用户
    flash('Goodbye.')
    return redirect(url_for('index'))  # 重定向回首页

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_valify = request.form['password_valify']

        if not username or not password or password!=password_valify:
            flash('Invalid input.')
            return redirect(url_for('register'))
        
        user_to_add = User(name='Guest',username=username)
        user_to_add.set_password(password)  # 设置密码
        db.session.add(user_to_add)
        db.session.commit()
        flash('Create account success.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.errorhandler(Exception) 
def all_exception_handler(e):
    # 对于 HTTP 异常，返回自带的错误描述和状态码
    # 这些异常类在 Werkzeug 中定义，均继承 HTTPException 类
    # if isinstance(e, HTTPException):
    #     return e.desciption, e.code
    # return 'Error', 500  # 一般异常
    return 'Error', 500
@app.errorhandler(404)  # 传入要处理的错误代码
def page_not_found(e):  # 接受异常对象作为参数
    # user = User.query.first()
    # u = User.query.filter_by(username=current_user.username).first()
    return render_template('404.html'), 404  # 返回模板和状态码

@app.route('/work/edit/<int:work_id>', methods=['GET', 'POST'])
@login_required
def edit(work_id):
    work = Work.query.get_or_404(work_id)
    u = User.query.filter_by(username=current_user.username).first()
    if request.method == 'POST':  # 处理编辑表单的提交请求

        uname=current_user.username
        recordtime=datetime.datetime.now()
        project=request.form['project']
        uwork=request.form['uwork']
        
        if not project:
            flash('Invalid input.')
            return redirect(url_for('edit', work_id=work_id))  # 重定向回对应的编辑页面
        
        # work.uname=uname
        work.recordtime=recordtime
        work.project=project
        work.uwork=uwork
        db.session.commit()  # 提交数据库会话
        flash('Item updated.')
        if u.name == "Admin":
            return redirect(url_for('report'))
        return redirect(url_for('work'))  # 重定向回主页

    return render_template('edit.html', work=work,user=u)  # 传入被编辑的电影记录

@app.route('/work/delete/<int:work_id>', methods=['POST'])  # 限定只接受 POST 请求
@login_required
def delete(work_id):
    work = Work.query.get_or_404(work_id)  # 获取电影记录
    db.session.delete(work)  # 删除对应的记录
    db.session.commit()  # 提交数据库会话
    flash('Item deleted.')
    u = User.query.filter_by(username=current_user.username).first()
    if u.name == "Admin":
        return redirect(url_for('report'))
    return redirect(url_for('work'))  # 重定向回主页

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']
        # username = request.form['username']
        oldpass = request.form['old_pass']
        newpass = request.form['new_pass']
        confirm = request.form['confirm']
        if not name or len(name) > 20 or not oldpass or not newpass or not confirm:
            flash('Invalid input.')
            return redirect(url_for('settings'))
        # check the oldpass
        if not current_user.validate_password(oldpass):
            flash("old password is not correct.")
            return redirect(url_for('settings'))
        # check the newpass and confirm
        if newpass != confirm:
            flash("input new password is different.")
            return redirect(url_for('settings'))
        

        current_user.name = name
        current_user.set_password(newpass)
        # current_user 会返回当前登录用户的数据库记录对象
        # 等同于下面的用法
        # user = User.query.first()
        # user.name = name
        db.session.commit()
        flash('Settings updated.')
        if name=='Admin':
            return redirect(url_for('search'))
        else:
            return redirect(url_for('work'))
    u = User.query.filter_by(username=current_user.username).first()
    return render_template('settings.html',user=u)

@app.route('/report', methods=['GET'])
@login_required
def report():
    # startdate = datetime.datetime.strptime(str(start),'%Y-%m-%d')
    # enddate = datetime.datetime.strptime(str(end),'%Y-%m-%d')

    period = Period.query.first()
    sd = period.start
    ed = period.end

    works=Work.query.filter(Work.recordtime > sd).filter(Work.recordtime <= ed).order_by(Work.uname).all()
    u = User.query.filter_by(name='Guest').all()
    return render_template('report.html',works=works,users=u)

@app.route('/search', methods=['GET','POST'])
@login_required
def search():
    if request.method == 'POST':
        startdate   = request.form['startdate']
        enddate     = request.form['enddate']

        startdateT = datetime.datetime.strptime(str(startdate),'%Y-%m-%d')
        enddateT = datetime.datetime.strptime(str(enddate),'%Y-%m-%d')

        period = Period.query.first()
        if period==None:
            
            period = Period(start=startdateT,end=enddateT)
            db.session.add(period)
            db.session.commit()
        else:
            period.start = startdateT
            period.end = enddateT
            db.session.commit()
        return redirect(url_for('report'))
    u = User.query.filter_by(username=current_user.username).first()
    return render_template('search.html',user=u)


# 命令
@app.cli.command()
@click.option('--drop', is_flag=True,help='Create after drop.')
def initdb(drop):
    """ Initialize the database. """
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')

@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    """Create user."""
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)  # 设置密码
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)  # 设置密码
        db.session.add(user)

    db.session.commit()  # 提交数据库会话
    click.echo('Done.')

if __name__ == '__main__':
    app.run(host='127.0.0.1',port=5000)