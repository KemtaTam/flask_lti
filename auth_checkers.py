from flask import abort, session
from FDataBase import FDataBase

#session_id это айди пользователя
def check_auth():
	#session - объект во flask для работы с сессиями
	session_id = session.get('session_id', None)	#смотрим куки запросы, которые пришли (айди пользователя)	
	user_session = FDataBase().get_session(session_id)	#проверка на существование таких куков

	if user_session:
		return user_session
	else:
		abort(401, "check_auth не прошел")

def check_admin():
	return FDataBase().get_session(session.get('session_id', None)).get('admin', False)

def check_task_access(task_id):
	user_session = FDataBase().get_session(session.get('session_id', None))
	if check_admin():	#если пользователь админ, то доступ разрешен ко всему
		return True
	else:
		return task_id in user_session['tasks']	#если не админ, то проверка 