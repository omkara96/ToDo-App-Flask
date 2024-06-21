from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from databaseModel import session as db_session, User, Todolist
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from jinja2 import Environment

app = Flask(__name__)
app.secret_key = 'omkar_todo_app'
app.jinja_env.globals['timedelta'] = timedelta
login_manager = LoginManager()
login_manager.init_app(app)

def truncate(s, length=100, ellipsis=True):
    if len(s) <= length:
        return s
    return s[:length] + ('...' if ellipsis else '')

app.jinja_env.filters['truncate'] = truncate

def calculate_time_remaining(created_on, work_time_minutes):
    # Convert work_time_minutes to timedelta
    work_time_delta = timedelta(minutes=work_time_minutes)
    
    # Calculate estimated completion time
    estimated_completion_time = created_on + work_time_delta
    
    # Calculate time remaining
    current_time = datetime.now()
    time_remaining_delta = estimated_completion_time - current_time
    time_remaining_minutes = int(time_remaining_delta.total_seconds() / 60)
    return time_remaining_minutes

def calculate_difference_in_minutes(datetime1_str, datetime2_str):
    datetime_format = "%Y-%m-%d %H:%M:%S"
    datetime1 = datetime.strptime(datetime1_str, datetime_format)
    datetime2 = datetime.strptime(datetime2_str, datetime_format)
    time_difference = datetime2 - datetime1
    difference_in_minutes = int(time_difference.total_seconds() / 60)
    return difference_in_minutes

@login_manager.user_loader
def loader_user(id):
    return db_session.query(User).filter_by(id=id).first()

@app.route("/")
def home():
    return render_template('home.html',  active_page='home')

@app.route("/dashboard")
@login_required
def dashboard():
    search_query = request.args.get('search', None)

    if search_query:
        todos = db_session.query(Todolist).filter(Todolist.user_id == current_user.id, Todolist.todo_title.ilike(f"%{search_query}%")).order_by(Todolist.created_on.desc()).all()
    else:
        todos = db_session.query(Todolist).filter(Todolist.user_id == current_user.id).order_by(Todolist.created_on.desc()).all()

    for todo in todos:
        if not todo.iscompleted:
            if todo.created_on is not None:
                expected_completion_time = todo.created_on + timedelta(minutes=todo.work_time)
                remaining_time = max(0, (expected_completion_time - datetime.now()).total_seconds() // 60)
                overdue = max(0, (datetime.now() - expected_completion_time).total_seconds() // 60) if datetime.now() > expected_completion_time else 0
                todo.remaining_time = remaining_time
                todo.overdue = overdue
                todo.expected_completion_time = expected_completion_time
            else:
                todo.remaining_time = None
                todo.overdue = None
                todo.expected_completion_time = None
        else:
            todo.remaining_time = None
            todo.overdue = None
            todo.expected_completion_time = None

    return render_template('dashboard.html', todos=todos)

@app.route("/signin", methods=['POST', 'GET'])
def signin():
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = db_session.query(User).filter_by(email=email).first()
        if user and password == user.password:
            session['current_user'] = user.email
            session['logged_in'] = True
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials, please try again.', 'danger')
    
    return render_template('signin.html',  active_page='signin')

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        password = request.form['password']

        try:
            user = User(first_name=fname, last_name=lname, email=email, password=password)
            db_session.add(user)
            db_session.commit()
            return redirect(url_for('home'))
        except IntegrityError:
            db_session.rollback()
            return "Username or email already exists."
        except Exception as e:
            db_session.rollback()
            return f"An error occurred: {str(e)}"

    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    session.pop('current_user', None)
    logout_user()
    return redirect(url_for('home'))

@app.route("/add", methods=['POST'])
@login_required
def addtodo():
    if request.method == 'POST':
        todonm = request.form["todonm"]

        session['todonm'] = todonm  # Store the todo name in the session
        return redirect(url_for('saveTodo'))

@app.route("/addTodo", methods=['POST', 'GET'])
@login_required
def saveTodo():
    crtdttm = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if request.method == 'POST':
        todonm = request.form["todonm"]
        tododesc = request.form["tododesc"]
        timetocmplt = request.form["timetocmplt"]
        created_on = datetime.strptime(crtdttm, '%Y-%m-%d %H:%M:%S')
        datetime_obj = datetime.strptime(timetocmplt, "%Y-%m-%dT%H:%M")
        formatted_datetime = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
        try:
            todo = Todolist(
                            todo_title=todonm, 
                            todo_desc=tododesc, 
                            created_on=created_on,
                            work_time=calculate_difference_in_minutes(crtdttm, formatted_datetime),
                            user=current_user,
                            iscompleted=None,
                            completed_on=None,
                            overdue=None
                            )
            db_session.add(todo)
            db_session.commit()
            return redirect(url_for('dashboard'))
        except IntegrityError:
            db_session.rollback()
            return "ToDo already exists."
        except Exception as e:
            db_session.rollback()
            return f"An error occurred: {str(e)}"

    todonm = session.pop('todonm', None)
    return render_template('addtodo.html', datetime=crtdttm, todonm=todonm)

@app.route('/get_todo/<int:todo_id>', methods=['GET'])
@login_required
def get_todo(todo_id):
    todo = db_session.query(Todolist).filter_by(id=todo_id).first()
    if todo:
        return f'Todo Title: {todo.todo_title}, Todo Description: {todo.todo_desc}'
    else:
        return 'Todo not found'

@app.route('/view/<int:todo_id>')
@login_required
@login_required
def view_todo(todo_id):
    todo = db_session.query(Todolist).filter_by(id=todo_id, user_id=current_user.id).first()
    if not todo:
        flash('Todo not found or you do not have permission to view it.', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('view_todo.html', todo=todo)

@app.route('/edit/<int:id>')
@login_required
def edit_todo(id):
    todo = db_session.query(Todolist).filter(id)
    return render_template('edit_todo.html', todo=todo)

@app.route('/closetodo/<int:todo_id>', methods=['GET', 'POST'])
@login_required
def closetodo(todo_id):
    todo = db_session.query(Todolist).filter_by(id=todo_id).first()
    if todo:
        if not todo.iscompleted:
            todo.iscompleted = True
            todo.completed_on = datetime.now()
            if todo.created_on and todo.work_time:
                expected_completion_time = todo.created_on + timedelta(minutes=todo.work_time)
                overdue = max(0, (datetime.now() - expected_completion_time).total_seconds() // 60) if datetime.now() > expected_completion_time else 0
                todo.overdue = overdue
            db_session.commit()
            flash(f'Todo "{todo.todo_title}" marked as completed.', 'success')
        else:
            flash(f'Todo "{todo.todo_title}" is already completed.', 'info')
    else:
        flash(f'Todo with id {todo_id} not found.', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/deltodo/<int:todo_id>', methods=['GET', 'POST'])
@login_required
def delete_todo(todo_id):
    todo = db_session.query(Todolist).filter_by(id=todo_id).first()
    if todo:
        return render_template('delete_confirm.html', todo=todo)
    else:
        flash(f'Todo with id {todo_id} not found.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/confirm_delete/<int:todo_id>', methods=['POST', 'GET'])
@login_required
def confirm_delete(todo_id):
    todo = db_session.query(Todolist).filter_by(id=todo_id).first()
    if todo:
        db_session.delete(todo)
        db_session.commit()
        flash(f'Todo "{todo.todo_title}" deleted successfully.', 'success')
    else:
        flash(f'Todo with id {todo_id} not found.', 'danger')
    return redirect(url_for('dashboard'))


# Custom pagination function
def paginate(query, page, per_page):
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total


# Route handler for completed todos
@app.route('/completed_todos')
@login_required
def completed_todos():
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Query completed todos for the current user
    completed_query = db_session.query(Todolist).filter_by(user_id=current_user.id, iscompleted=True).order_by(Todolist.completed_on.desc())

    # Paginate the completed todos using the custom paginate function
    completed_todos, total = paginate(completed_query, page, per_page)

    # Calculate pagination details
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'has_prev': page > 1,
        'has_next': (page * per_page) < total,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if (page * per_page) < total else None,
        'pages': (total + per_page - 1) // per_page  # Calculate total number of pages
    }

    return render_template('completed_todos.html', todos=completed_todos, pagination=pagination)

if __name__ == "__main__":
    app.run(debug=True)
