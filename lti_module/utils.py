TITLE = 'context_title'
RETURN_URL = 'launch_presentation_return_url'
USERNAME = 'ext_user_username'
PERSON_NAME = 'lis_person_name_given'
ROLES = 'roles'
ADMIN_ROLE = 'Instructor'
USER_ID = 'user_id'
EMAIL = 'lis_person_contact_email_primary'
FULLNAME = 'lis_person_name_full'
CUSTOM_PARAM_PREFIX = 'custom_'
#параметры для отправки оценок это заранее известные три ключа
# которые содержатся в лаунч запросе и которые мы должны сохранить, связать с решением
# и когда мы захотим отправить оценку за это решение, их и использовать
PASSBACK_PARAMS = ('lis_outcome_service_url', 'lis_result_sourcedid', 'oauth_consumer_key')

def get_full_name(data): return get_param(data, FULLNAME)
def get_email(data): return get_param(data, EMAIL)
def get_user_id(data): return get_param(data, USER_ID)
def get_title(data): return get_param(data, TITLE)
def get_return_url(data): return get_param(data, RETURN_URL)
def get_username(data): return get_param(data, USERNAME)
def get_person_name(data): return get_param(data, PERSON_NAME)

def get_role2(data): return get_param(data, ROLES)
def get_role(data, default_role=False):
	try:
		return get_param(data, ROLES).split(',')[0] == ADMIN_ROLE
	except:
		return default_role

def get_param(data, key):
	if key in data:
		return data[key]
	else:
		raise KeyError(f"{data} doesn't include {key}.")
		
#указываются в lms (task_id = SystemTaskID)
def get_custom_params(data):
	#обрезается префикс custom_
	return { key[len(CUSTOM_PARAM_PREFIX):]: data[key] for key in data if key.startswith(CUSTOM_PARAM_PREFIX) }

def extract_passback_params(data):
	params = {}
	for param_key in PASSBACK_PARAMS:
		if param_key in data:
			params[param_key] = data[param_key]
		else:
			raise KeyError(f"{data} doesn't include {param_key}. Must inslude: {PASSBACK_PARAMS}")
	return params