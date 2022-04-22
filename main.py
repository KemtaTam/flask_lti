from flask import Flask, abort, request, make_response, render_template, url_for, redirect, session, g
from uuid import uuid4
import sqlite3
import os
from FDataBase import FDataBase

from lti_module.check_request import check_request
from lti_module import utils
from auth_checkers import check_auth, check_admin, check_task_access
from grade_passback import put_unsend_result

#конфигурация
SECRET_KEY = '7e9d14702e5e3a863b95579d5bfe30d0c68b673c'

app = Flask(__name__)
app.config.from_object(__name__) #загружаем конфигурацию из приложения
#переопределим путь к бд
#свойство root_path ссылается на текущий рабочий каталог данного приложения
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'database.db')))	

name = ''
		
#фунция, которая будет создавать файл database.db и отсутствующие таблицы
def create_db():
	db = sqlite3.connect(app.config['DATABASE'])
	db.row_factory = sqlite3.Row
	with app.open_resource('database.sql', mode='r') as f:	
		db.cursor().executescript(f.read())
	db.commit()
	db.close()

#Перехват запросов (повторный код) декоратор
dbase = None
@app.before_request
def before_request():
	#Установление соединения с БД перед выполнением запроса
	global dbase	#говорит, что будем обращаться к глобальной переменной (которая объявлена выше)
	dbase = FDataBase()

#разрыв соединения
""" @app.teardown_appcontext
def close_db(error):
	#Закрываем соединение с БД, если оно было установлено
	if hasattr(g, 'link_db'):
		g.link_db.close()
		print('-------соединения с бд закрыто-------- from main', '\n') """

""" @app.route('/', methods=['GET'])
def index_test():
	return make_response(render_template('index.html', **request.args)) """

#показываем пользователю страницу с заданием
@app.route('/<task_id>', methods=['GET'])
def index(task_id):
	user = check_auth()
	if check_task_access(task_id):  
		return make_response(render_template('index.html', task_id=task_id, name=name))
	else:
		abort(401, f"You don't have access to task_id={task_id}. Allowed tasks: {list(user['tasks'].keys())}")

#пользователь решает задачу
@app.route('/<task_id>/send/solution/', methods=['GET'])
def send_solution(task_id):
	user = check_auth()
	answer = request.args.get('answer', 0)
	if(answer != '1'):		#если ответ неправильный, уменьшить оставшиеся попытки
		dbase.update_user_attempts(session['session_id'])

	solution_id = str(uuid4())
	dbase.add_solution(solution_id=solution_id, user_id=session['session_id'], task_id=task_id, score=answer,
		passback_params=user['tasks'].get(task_id)['passback_params'])

	solution = dbase.get_solution(solution_id)
	print('solution from /solution/<solution_id>:\n', solution, '\n')
	if solution:
		put_unsend_result()
		return redirect(url_for('get_user_solution', solution_id=solution_id))
	else:
		abort(404, 'Такого задания нет')

@app.route('/solution/<solution_id>', methods=['GET'])
def get_user_solution(solution_id):
	user = check_auth()
	solution = dbase.get_solution(solution_id)
	attempts = dbase.get_user_attempts(session['session_id'])
	return make_response(render_template('solution.html', solution_id=solution_id, solution=solution, attempts=attempts))

#главный роут, на который будет приходить пост запрос от lms
@app.route('/lti', methods=['POST'])
def lti_route():
	params = request.form	#извлечение информации из запроса (все что дала нам lms)
	consumer_secret = dbase.get_secret(params.get('oauth_consumer_key', ''))
	request_info = dict( 
		headers=dict(request.headers),
		data=params,
		url=request.url,
		secret=consumer_secret
	)
	
	if check_request(request_info):
		user_id = utils.get_user_id(params)
		fullname = utils.get_full_name(params)
		email = utils.get_email(params)
		custom_params = utils.get_custom_params(params)
		task_id = custom_params.get('task_id', 'default_task_id')
		role = utils.get_role(params)
		#начинаем доставать параметры для отправки оценок на lms
		params_for_passback = utils.extract_passback_params(params)
		global name
		name = utils.get_person_name(params)
		
		dbase.add_user(user_id, fullname, email)
		dbase.add_session(user_id, task_id, params_for_passback, role)	
		session['session_id'] = user_id	#сохраняем в запросе уник идентификатор

		if(dbase.get_user_attempts(user_id) > 0):	
			return redirect(url_for('index', task_id=task_id))
		else:
			abort(403, 'Попытки закончились')
	else:
		abort(403, 'check_request не прошел')

if __name__ == "__main__":
	app.debug = True
	app.run()
