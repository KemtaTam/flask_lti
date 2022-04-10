import sqlite3
import os
from pathlib import Path
from flask import g

SESSIONS = {}	#хранение какой-то информации о пользователе и ее дальнейшее использование
SOLUTIONS = {}	#решения пользователей в системе
CONSUMERS = {
	'timestamp_and_nonce': []
}
		
class FDataBase():
	__instance = None

	def __new__(cls, *args, **kwargs):		#вызывается перед созданием экземпляра класса
		if cls.__instance is None:
			cls.__instance = super().__new__(cls)
		return cls.__instance

	def __del__(self):			#деструктор
		FDataBase.__instance = None

	#общая функция для установаления соединения с базой данных
	def connect_db(self):
		#методу connect передаем путь, в котором расположена бд
		conn = sqlite3.connect(os.path.join(Path.cwd(), "database.db"))
		#чтобы записи в бд были представлены не в виде кортежей, а в виде словаря
		#conn.row_factory = sqlite3.Row		
		return conn	#возвращает установленное соединение

	#установление соединения
	def get_db(self):
		#Соединение с БД, если оно еще не установлено
		if not hasattr(g, 'link_db'):	#существует ли у g свойство link_db
			g.link_db = self.connect_db()	#если свойства нет, устанавливаем соединение
		return g.link_db

	def __init__(self):		#конструктор
		db = self.get_db()
		self.__db = db
		self.__cur = db.cursor()

	def is_key_valid(self, key):
		try:
			self.__cur.execute("SELECT key from keysecret")
			res = self.__cur.fetchone()
			return res[0] == key
		except sqlite3.Error as e:
			print("Ошибка проверки валидации ключа "+str(e))
			return False

	def get_secret(self, key):		
		if self.is_key_valid(key):
			try:
				self.__cur.execute("SELECT secret from keysecret")
				res = self.__cur.fetchone()
				return res[0]
			except sqlite3.Error as e:
				print("Ошибка взятия секрета "+str(e))
				return False

	def add_user(self, user_id, name, email):
		try:
			self.__cur.execute(f"SELECT COUNT() FROM users WHERE user_id LIKE '{user_id}'")
			res = self.__cur.fetchone()
			if res[0] > 0:
				return False
			self.__cur.execute("INSERT INTO users VALUES(NULL, ?, ?, ?, 3)", (user_id, name, email))
			self.__db.commit()
		except sqlite3.Error as e:
			print("Ошибка добавления юзера в БД:\n " + str(e) + '\n')
			return False
		return True

	def get_session(self, session_id): 	
		try:
			self.__cur.execute("SELECT task, lis_outcome_service_url, lis_result_sourcedid, oauth_consumer_key, admin \
								FROM sessions WHERE session_id=?", (session_id,))
			res = self.__cur.fetchall()
		except sqlite3.Error as e:
				print("Ошибка выборки сессии в БД:\n " + str(e) + '\n')
				return False
		if (res): 
			res = res[-1]
			SESSIONS[session_id] = {
				'tasks': {
					res[0]: {	#task
						'passback_params': {
							'lis_outcome_service_url': res[1],
							'lis_result_sourcedid': res[2],
							'oauth_consumer_key': res[3],
						}
					}
				}, 
				'admin': res[4]	#admin
			}
		return SESSIONS.get(session_id, {})

	def add_session(self, session_id, task, passback_params, admin=False): 
		session = self.get_session(session_id)
		if session:		#если такой пользователь присутствует, обновить его данные
			try:
				self.__cur.execute(f"UPDATE sessions \
									 SET lis_result_sourcedid='{passback_params['lis_result_sourcedid']}', admin='{admin}' \
									 WHERE session_id='{session_id}'")
				self.__db.commit()
			except sqlite3.Error as e:
				print("Ошибка обновления сессии в БД:\n " + str(e) + '\n')
				return False
		else:
			try:
				self.__cur.execute("INSERT INTO sessions VALUES(NULL, ?, ?, ?, ?, ?, ?)", (
						session_id, 
						task, 
						passback_params['lis_outcome_service_url'], 
						passback_params['lis_result_sourcedid'],
						passback_params['oauth_consumer_key'], 
						admin
					)
				)
				self.__db.commit()
				print('Сессии добавлены в бд\n')
			except sqlite3.Error as e:
				print("Ошибка добавления сессии в БД:\n " + str(e) + '\n')
				return False

	def get_solution(self, solution_id):
		try:
			self.__cur.execute("SELECT userid, task, score, lis_outcome_service_url, \
						lis_result_sourcedid, oauth_consumer_key, is_passbacked \
						FROM solutions WHERE solution_id=?", (solution_id,))
			res = self.__cur.fetchone()
		except sqlite3.Error as e:
				print("Ошибка выборки решений в БД:\n " + str(e) + '\n')
				return False
		if(res):
			SOLUTIONS[solution_id] = {
				'_id': solution_id,
				'userid': res[0],
				'task_id': res[1],
				'score': res[2],
				'passback_params': {
					'lis_outcome_service_url': res[3],
					'lis_result_sourcedid': res[4],
					'oauth_consumer_key': res[5],
				},
				'is_passbacked': res[6]
			}
		return SOLUTIONS.get(solution_id, {})

	def add_solution(self, solution_id, user_id, task_id, score, passback_params, is_passbacked=False):
		res = self.get_user_solutions_count(user_id)
		if res > 0:
			self.update_user_solutions_info(solution_id, user_id, task_id, score, passback_params, is_passbacked)
		else:
			try:
				self.__cur.execute("INSERT INTO solutions VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?)", (
						solution_id, 
						user_id,
						task_id,
						score,
						passback_params['lis_outcome_service_url'], 
						passback_params['lis_result_sourcedid'], 
						passback_params['oauth_consumer_key'], 
						is_passbacked
					)
				)
				self.__db.commit()
				print('Решения добавлены в бд\n')
			except sqlite3.Error as e:
				print("Ошибка добавления решений в БД:\n " + str(e) + '\n')
				return False

	def get_user_solutions_count(self, user_id):
		try:
			self.__cur.execute(f"SELECT COUNT() FROM solutions WHERE userid LIKE '{user_id}'")
			res = self.__cur.fetchone()
			return res[0]
		except sqlite3.Error as e:
			print("Ошибка подсчета числа юзеров в БД:\n " + str(e) + '\n')
			return False

	def update_user_solutions_info(self, solution_id, user_id, task_id, score, passback_params, is_passbacked):
		try:
			self.__cur.execute(f"UPDATE solutions \
								SET lis_result_sourcedid='{passback_params['lis_result_sourcedid']}', \
									solution_id='{solution_id}', \
									is_passbacked='{is_passbacked}', \
									score='{score}', \
									task='{task_id}' \
								WHERE userid='{user_id}'")
			self.__db.commit()
		except sqlite3.Error as e:
			print("Ошибка обновления решения в БД:\n " + str(e) + '\n')
			return False

	def get_unsend_solution(self):
		return (SOLUTIONS[solution_id] for solution_id in SOLUTIONS if not SOLUTIONS[solution_id].get('is_passbacked', True))

	def set_passbacked_flag(self, solution_id, flag):		
		SOLUTIONS[solution_id]['is_passbacked'] = flag
		try:
			self.__cur.execute("UPDATE solutions SET is_passbacked = ? WHERE solution_id = ?", (flag, solution_id))
			self.__db.commit()
			print('flag изменен\n')
		except sqlite3.Error as e:
			print("Ошибка смены отправки в БД:\n " + str(e) + '\n')
			return False

	def add_lisResultSourcedid(self, lis_result_sourcedid):	#временно
		self.__cur.execute("INSERT INTO params VALUES(NULL, ?)", (lis_result_sourcedid, ))
		self.__db.commit()

	def get_lisResultSourcedid(self):	#временно
		self.__cur.execute("SELECT passback_params FROM params")
		res = self.__cur.fetchall()
		print('res[-1]', res[-1])
		return res

	def has_timestamp_and_nonce(self, key, timestamp, nonce):
		if(self.is_key_valid(key)):
			return (timestamp, nonce) in CONSUMERS['timestamp_and_nonce']

	def add_timestamp_and_nonce(self, key, timestamp, nonce):
		if(self.is_key_valid(key)):
			CONSUMERS['timestamp_and_nonce'].append((timestamp, nonce))
			print('CONSUMERS:\n', CONSUMERS,'\n')

	# парсинг данных из passback_params (из строки в словарь)
	def parsing_passback_params(self, passback_params):
		passback_params = passback_params['lis_result_sourcedid'] \
			.replace('{', '') \
			.replace('}', '') \
			.replace('"data":', '') \
			.replace('"', '') \
			.split(',')
		for i in range(len(passback_params)):
			passback_params[i] = passback_params[i].split(':')
		return dict(passback_params) 