from lti.tool_provider import ToolProvider
from FDataBase import FDataBase
import threading

PASSBACK_TIMER = None
PASSBACK_INTERVAL = 20

def put_unsend_result(use_timer=True):
	for solution in FDataBase().get_unsend_solution():
		print(f"Try to send {solution['_id']}")
		grade_passback(solution)
	if use_timer:
		PASSBACK_TIMER = threading.Timer(PASSBACK_INTERVAL, put_unsend_result)
		PASSBACK_TIMER.start()

def grade_passback(solution):
	passback_params = solution.get('passback_params', {})
	consumer_secret = FDataBase().get_secret(passback_params['oauth_consumer_key'])
	print('passback_params from grade_passback():\n', passback_params, '\n')
	if not passback_params:
		FDataBase().set_passbacked_flag(solution.get('_id'), True)
		print(f"No passback_params for solution={solution}")
		return

	#когда отправляем оценку, вызывается метод post_replace_result (заменяет результат, который уже существует на lms)
	response = ToolProvider \
		.from_unpacked_request(secret=consumer_secret, params=passback_params, headers=None, url=None) \
		.post_replace_result(score=solution.get('score'))
	
	if response.code_major == 'success' and response.severity == 'status':
		FDataBase().set_passbacked_flag(solution.get('_id'), True)
		print(f"Success grade passback. Solution {solution.get('_id')} of {solution.get('login')}. {response.description} {response.response_code} {response.code_major}")
	else:
		print("Error while putting result to lms. Solution {}. {} {} {} {}".format(solution.get('_id'), solution.get('login'), response.description, response.response_code, response.code_major))











